#!/usr/bin/env python3
import bech32
from src.email import *
import os
import glob
import re
import ast
import sys
import subprocess
import json
from io import StringIO
from chainexplorer import explorer as exp
from bitcoinUtils.src.FORMATutils import *
from src.helpers import *
from src.electrum import *
from bitcoinlib.wallets import Wallet
from bitcoinlib.transactions import Transaction, Output
from bitcoinlib.keys import Key
import math

BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
RIVER_ADDRESS = 'bc1qecz4hqg6r06vptt9x6zxt3auf9vns3hc0mlgnm'
# PRIVATE_ADDRESS = "3CjXfgPaqeKL8e29uX1DnXN8nYHaspx8n5"
MEMPOOL_API = "https://mempool.space/api"
MEMPOOL_FEE_PATH = f"{MEMPOOL_API}/v1/fees/recommended"

setsPerBTC = 100000000

def getUtxos(address):
    url = f"{MEMPOOL_API}/address/{address}/utxo"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError("Error fetching UTXOs")
    return response.json()

def sweepAddress(spendAddress, wif, isPending=False):
    appendToDatalog(f"Running sweepAddress()")

    mediumFee, fastFee = getRecommendedFees()

    bitcoin_price = getBtcPrice()
    UTXOs = getUtxos(spendAddress)

    if not UTXOs:
        send_email("No UTXOs Found", f"Address: {spendAddress}")
        return

    totalInputSats = sum(utxo["value"] for utxo in UTXOs)
    tx_size = len(UTXOs) * 180 + 34 + 10 

    totalInputUSD = bitcoin_price*totalInputSats/setsPerBTC

    if (totalInputUSD < 20):
        satsPerVB = (mediumFee+fastFee)/2
    else:
        satsPerVB = fastFee

    totalFees = math.ceil(tx_size * satsPerVB)
    feeUSD = bitcoin_price*totalFees/setsPerBTC

    key = Key(import_key=wif)
    tx = Transaction(network='bitcoin')
    tx.witness_type = None

    sendAmount = int(totalInputSats - totalFees)
    sendAmountUSD = bitcoin_price*sendAmount/setsPerBTC

    for utxo in UTXOs:
        tx.add_input(utxo["txid"], utxo["vout"])

    tx.add_output(address=RIVER_ADDRESS, value=sendAmount)
    tx.sign(key.private_hex)

    rawTx = tx.raw_hex()

    if rawTx is not None:
        appendToDatalog(f"Attempting to sweep ${round(sendAmountUSD,2):,} to {RIVER_ADDRESS} (RIVER). Amount: {sendAmount} satoshis From:\t{spendAddress}\t WIF:\t{wif}\t Fee:\t{totalFees} (${round(feeUSD,2)}) @ {satsPerVB} sat/vB")
        send_email(f"Attempting to sweep ${round(sendAmountUSD,2):,} to {RIVER_ADDRESS} (RIVER)", f"Amount: {sendAmount} satoshis \n\nFrom:\t{spendAddress}\nWIF:\t{wif}\nFee:\t{totalFees} (${round(feeUSD,2)}) @ {satsPerVB} sat/vB")
    
    cmd = ['bitcoin-cli', 'sendrawtransaction', rawTx]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdErr = result.stderr

    if stdErr:
        send_email(f'Sweep of {spendAddress} failed.', stdErr)
    else:
        send_email(f'Sweep of {spendAddress} succeeded!', 'Watch for your funds in river.')

def estimateVSize(rawTx, inputCount):
    baseSize = len(bytes.fromhex(rawTx)) 
    witnessSize = inputCount * 107 
    vsize = (3 * baseSize + witnessSize) 
    return vsize

def broadcastTransaction(rawTx):
    command = f'bitcoin-cli sendrawtransaction {rawTx}'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def getBlockHeights():
    appendToDatalog(f"Running getBlockHeights()")
    try:
        output = subprocess.check_output(["bitcoin-cli", "getblockchaininfo"], text=True).strip()
        data = json.loads(output)
        localHeight = data.get("blocks")
        progress = 100*data.get("verificationprogress")
        progressPercent = str(progress).split('.')[0]
        progressDecimalExtended = 2*str(progress).split('.')[1]
        progressExtended = float(progressPercent+'.'+progressDecimalExtended)
        networkHeight = int(100*localHeight / progressExtended)
        print(f"{localHeight} {progress} {networkHeight}")
        appendToDatalog(f"Bitcoin-CLI: Local height: {localHeight}, Network height: {networkHeight}, Progress: {progress}")

    except Exception as e:
        appendToDatalog(f"Bitcoin-CLI: Error: {str(e)}")
        return None, None, None

    return localHeight, networkHeight

def getAddressBalance(address):
    urls = [
        f"https://mempool.space/api/address/{address}",
        f"https://blockstream.info/api/address/{address}",
        f"https://api.blockcypher.com/v1/btc/main/addrs/{address}",
        f"https://chain.api.btc.com/v3/address/{address}",
        f"https://sochain.com/api/v2/address/BTC/{address}"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if "chain_stats" in data:
                    return data["chain_stats"].get("funded_txo_sum", 0) - data["chain_stats"].get("spent_txo_sum", 0)
                elif "final_balance" in data:
                    return data["final_balance"]
                elif "data" in data and "balance" in data["data"]:
                    return data["data"]["balance"]
                elif "status" in data and data["status"] == "success" and "balance" in data:
                    return int(float(data["balance"]) * 1e8)
        except requests.RequestException:
            continue
    
    return None

def getRecommendedFees():
    response = requests.get(MEMPOOL_FEE_PATH)
    fees = response.json()
    mediumFee = fees.get("halfHourFee")
    fastFee = fees.get("fastestFee")
    return mediumFee, fastFee

def fetchPrice(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            appendToDatalog(f"Successfully fetched data from {url}")
            return response.json()
        else:
            appendToDatalog(f"Failed to fetch data from {url}, Status Code: {response.status_code}")
    except Exception as e:
        appendToDatalog(f"Error fetching data from {url}: {str(e)}")
        return None

def getBtcPrice():
    appendToDatalog(f"Running puzzleSiteScraper()")
    
    urls = [
        "https://mempool.space/api/v1/prices",
        "https://api.coindesk.com/v1/bpi/currentprice/BTC.json",
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    ]
    
    for url in urls:
        response = fetchPrice(url)
        if response:
            if url == "https://mempool.space/api/v1/prices":
                price = response.get("USD")
                appendToDatalog(f"Fetching BTC price from mempool.space: {price}")
                return price
            elif url == "https://api.coindesk.com/v1/bpi/currentprice/BTC.json":
                price = response.get("bpi", {}).get("USD", {}).get("rate_float")
                appendToDatalog(f"Fetching BTC price from api.coindesk: {price}")
                return price
            elif url == "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT":
                price = float(response.get("price"))
                appendToDatalog(f"Fetching BTC price from api.binance: {price}")
                return price
    
    appendToDatalog(f"Failed to fetch BTC price from any sources.")
    return None

def checkAndSweep(blockDiff = False):
    appendToDatalog(f"Running checkAndSweep()")
    spendable_dict = {}
    for file in glob.glob(f"{LOG_PATH}/*_spendable.txt"):
        with open(file, "r") as f:
            for line in f:
                address, wif = line.strip().split("\t")
                spendable_dict[address] = wif

    if (blockDiff):
        files = [f for f in os.listdir(LOG_PATH) if f.endswith("_addresses.txt")]

        addresses = []
        for file in files:
            with open(os.path.join(LOG_PATH, file), "r") as f:
                for line in f:
                    addresses.append(line.strip())

        matched_dict = {k: v for k, v in spendable_dict.items() if k in addresses}

        if (matched_dict):
            for address, wif in matched_dict.items():
                appendToDatalog(f"Newly Spendable UTXO(s) detected: Address: {address}\tWIF: {wif}")
                send_email(f"Newly Spendable UTXO(s) Detected", f"Address: {address}\nWIF: {wif}")
                sweepAddress(address, wif)
    else:
        if (spendable_dict):
            for address, wif in spendable_dict.items():
                balance = getAddressBalance(address)
                if (balance > 0):
                    appendToDatalog(f"Spendable UTXO(s) detected: Address: {address}\tWIF: {wif}")
                    send_email(f"Spendable UTXO(s) Detected", f"Address: {address}\nWIF: {wif}")
                    sweepAddress(address, wif)
            send_email("Checked all Spendable Addresses", "Checked all spendable addresses for UTXOs.")

def getRawBlockData(block_height):
    for file in glob.glob(f"{LOG_PATH}/*_data.txt"):
        os.remove(file)

    try:    
        raw_block = exp.get_by_block(block_height)
        buffer = StringIO()
        sys.stdout = buffer
        exp.show_transactions(raw_block)
        sys.stdout = sys.__stdout__

        raw_data = buffer.getvalue()
        return raw_data
    except IndexError:
        appendToDatalog(f"EXP API Failed to retrieve block {block_height} from chainexplorer.")
        return None 
    
def parseBlockTransactionOutputs(rawBlockData):
    outputs = [line.strip() for line in rawBlockData.split('\n') if line.startswith("out:")]
    addresses = [addr for entry in outputs for addr in re.findall(r"'addr': '([^']+)'", entry)]
    addresses = list(dict.fromkeys(addresses))
    return addresses

def blockParser():
    appendToDatalog(f"Running blockParser()")
    # Remove old block data files. 
    removeFilesWithEnding(LOG_PATH, "_data.txt")
    removeFilesWithEnding(LOG_PATH, "_addresses.txt")

    localHeight, networkHeight = getBlockHeights()

    # Wrire new block data files. 
    rawBlockData = getRawBlockData(localHeight)
    fileName = f"{LOG_PATH}/{localHeight}_data.txt"
    appendToDatalog(f"Creating file: {fileName}")
    writeToFile(fileName, rawBlockData)

    addresses = parseBlockTransactionOutputs(rawBlockData)

    fileName = f"{LOG_PATH}/{localHeight}_addresses.txt"
    appendToDatalog(f"Creating file: {fileName}")
    writeToFile(fileName, addresses, isList=True)

def blockStatusEmail():
    appendToDatalog("Running blockStatusEmail()")
    localHeight, networkHeight = getBlockHeights()
    nodePercent = round(100 * localHeight / networkHeight, 3)
    
    if localHeight is None or networkHeight is None:
        sys.exit(1)

    nodeLagging = networkHeight - localHeight > 3
    electrumHeight = getElectrumHeight()
    electrumPercent = round(100 * electrumHeight / networkHeight, 3)
    electrumLagging = electrumPercent < 99.9

    status = "Node and Electrum Lagging" if nodeLagging and electrumLagging else \
             "Node Lagging" if nodeLagging else \
             "Electrum Lagging" if electrumLagging else \
             "Fully Synced"

    subject = f"Raspi5Bolt Status: {status}"
    body = f"Raspi5Bolt node is {'not ' if nodeLagging else ''}up to date.\n"
    body += f"Electrum is {'not ' if electrumLagging else ''}fully indexed.\n\n"

    if nodeLagging:
        body += f"Node Status: {nodePercent:.2f}%\n"
    if electrumLagging:
        body += f"Electrum Status: {electrumPercent:.2f}%\n\n"

    body += f"Node: {localHeight}\n"
    body += f"Electrum: {electrumHeight}\n"
    body += f"Network: {networkHeight}\n\n"

    send_email(subject, body)

def checkEmailAndSweep(debugEmailParts=None):
    appendToDatalog(f"Running checkEmailAndSweep()")

    if (debugEmailParts):
        emailParts = debugEmailParts
    else:
        emailParts = checkEmail()

    if (emailParts):
        appendToDatalog(f'New email detected.')
        address_wif_dict = {}
        for subject, body in emailParts:
            if (subject != 'raspi5bolt'):
                appendToDatalog(f'Spam email detected. {subject}')
                return

            wif = generateWifCompressed(body)

            commands = findCommandsInString(body)

            if wif:
                addresses = [wif_to_P2PKH(wif),wif_to_P2SHpP2WPKH(wif),wif_to_bech32(wif)]
                appendToDatalog(f'New spend address found for WIF {wif}')
                send_email(f"New spend address for WIF {wif}", f"Addresses:\n{addresses[0]}\n{addresses[1]}\n{addresses[2]}")
                for address in addresses:
                    isAppended = appendToFile(f"{LOG_PATH}/email_spendable.txt", f"{address}\t{wif}")
                    if (isAppended):
                        sweepAddress(address, wif)
            elif commands:
                for command in commands:
                    appendToDatalog(f'Command {command} recieved.')
                    if command == 'log':
                        datalogEmail()
                    elif command == 'status':
                        blockStatusEmail()
                    elif command == 'help':
                        helpEmail()
            else:
                pass
