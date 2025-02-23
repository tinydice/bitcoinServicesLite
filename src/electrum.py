import subprocess
import requests
import json
import re
from src.helpers import *
from src.electrum import *

datalog = []

def electrumRpc(method, params=[]):
    url = 'https://127.0.0.1:50001'
    headers = {'Content-Type': 'application/json'}
    data = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1,
    }
    response = requests.post(url, json=data, headers=headers, verify=False)
    return response.json()

def getAddressFromWif(wif):
    response = electrumRpc('importprivkey', [wif])
    return response.get('result')

def getBalance(address):
    return electrumRpc('getbalance', [address])

def getIndexingStatus():
    try:
        process = subprocess.Popen(['sudo', 'journalctl', '-n', '10', '-u', 'electrs'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, _ = process.communicate()
        matches = re.findall(r'indexing \d+ blocks: \[(\d+)\.\.(\d+)\]', output)
        if matches:
            appendToDatalog(f"Electrum has indexed {matches[-1]} blocks.")
            return matches[-1]
        if 'Electrum fully indexed' in output:
            appendToDatalog(f"Electrum is fully indexed.")
            return -1
    except Exception as e:
        print(f"Error: {e}")
    return None

def getElectrumHeight():
    appendToDatalog(f"Running getBlockHeights()")
    status = getIndexingStatus()
    if isinstance(status, tuple):
        return int(status[1])
    return None

if __name__ == "__main__":
    height = getElectrumHeight()
    if height != -1:
        print(f"Electrs is indexing up to block {height}")
    else:
        response = electrumRpc('ping')
        print(response)