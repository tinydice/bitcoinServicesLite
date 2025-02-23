from bitcoinlib.services.services import Service
import time

service = Service(network='bitcoin')

def getMempoolTransactions():
    return service.mempool()

def getTransactionDetails(txid):
    txData = service.gettransaction(txid)
    return txData

def extractAddressesFromTx(txData, addresses, addressUTXOs):
    txid = txData.txid
    outputs = txData.outputs
    for index, output in enumerate(outputs):
        address = output.address
        print(address)
        addresses.add(address)
        addressUTXOs[address] = {
            'value': output.value,
            'txid': txid,
            'index': index,
            'witness': output.witness_type
        }

    return addresses, addressUTXOs

def monitorMempool():
    knownTxids = set()
    while True:
        addresses = set()
        addressUTXOs = {}

        if len(knownTxids) >= 10000:
            knownTxids.pop()

        txids = getMempoolTransactions()
        for txid in txids:
            if txid not in knownTxids:
                knownTxids.add(txid)
                txData = getTransactionDetails(txid)
                addresses, addressUTXOs = extractAddressesFromTx(txData, addresses, addressUTXOs)
        print(len(addresses))
        
if __name__ == "__main__":
    monitorMempool()
