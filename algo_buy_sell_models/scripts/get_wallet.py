# Move up a level in the directory
# REMOVE IF RUNNING THIS SCRIPT INDEPENDENT OF THIS PROJECT
import sys
sys.path.append("..")

# Imports
import json, time
from datetime import datetime
from decimal import Decimal
from algosdk import mnemonic

# Load JSON keys (untracked in repo for security)
f = open('../keys.json',)
keys = json.load(f)
f.close()

# Get Algo Client / Using purestake; supplement your own API key for the algod_token
from algosdk.v2client import algod
algod_address = "https://mainnet-algorand.api.purestake.io/ps2"
algod_token = keys["algod_tokens"][0]
headers = {"X-API-Key": algod_token}
algod_client = algod.AlgodClient(algod_token, algod_address, headers)

# Shows how to get a wallet
wallet = algod_client.account_info(keys['address'])
print(wallet)

# Shows how to get an asset (CHOICE)
asset_id = 297995609 # CHOICE
decimals = algod_client.asset_info(asset_id)['params']['decimals']
asset = next(item for item in wallet['assets'] if item["asset-id"] == asset_id)
amt = asset['amount'] * 10**(-decimals)
print(amt)

# Shows how to get Algo
decimals = 6
amt = wallet['amount'] * 10**(-decimals)
print(amt)
