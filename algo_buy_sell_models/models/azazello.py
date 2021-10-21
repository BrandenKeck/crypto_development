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
algod_token = keys['algod_token_1']
headers = {"X-API-Key": algod_token}
algod_client = algod.AlgodClient(algod_token, algod_address, headers)

# Get TMan Client / 350338509 is the app ID for all TinymanClient implementations
from tinyman.v1.client import TinymanClient
client = TinymanClient(algod_client, 350338509)

# A function to determine how much of an asset is in the wallet
def get_asset_decimal_amount(asset_id):
    decimals = algod_client.asset_info(asset_id)['params']['decimals']
    wallet = algod_client.account_info(keys['address'])
    asset = next(item for item in wallet['assets'] if item["asset-id"] == asset_id)
    return asset['amount'] * 10**(-decimals)




choice = get_asset_decimal_amount(297995609)
print(choice)
