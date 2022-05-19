# Imports
import json
from algosdk import mnemonic
from algosdk.v2client import algod
from algosdk.future import transaction

# Get keys
f = open("./keys.json",)
keys = json.load(f)

# Setup SDK client
algod_address = "https://mainnet-algorand.api.purestake.io/ps2"
algod_token = keys["algod_tokens"][3]
algod_headers = {"X-API-Key": algod_token}
algod_client = algod.AlgodClient(algod_token, algod_address, algod_headers)

params = algod_client.suggested_params()
txn = transaction.AssetConfigTxn(
    sender=keys["address"],
    sp=params,
    index="", # ADD THE ASSET ID
    strict_empty_address_check=False
)
stxn = txn.sign(mnemonic.to_private_key(keys["mnemonic"]))
try:
    txid = algod_client.send_transaction(stxn)
    print("Signed transaction with txID: {}".format(txid))
except Exception as err:
    print(err)
