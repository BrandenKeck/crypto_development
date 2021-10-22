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

# Get TMan Client / 350338509 is the app ID for all TinymanClient implementations
from tinyman.v1.client import TinymanClient
client = TinymanClient(algod_client, 350338509)

# Create a Trade
CHOICE = client.fetch_asset(297995609)
ALGO = client.fetch_asset(0)
CHOICE_ALGO = client.fetch_pool(CHOICE, ALGO)
quote_CHOICE_ALGO = CHOICE_ALGO.fetch_fixed_input_swap_quote(ALGO(1000), slippage=0.001)
tx_CHOICE_ALGO = CHOICE_ALGO.prepare_swap_transactions_from_quote(quote_CHOICE_ALGO, swapper_address=keys['address'])

# Sign the transaction
private_key = mnemonic.to_private_key(keys['mnemonic'])
tx_CHOICE_ALGO.sign_with_private_key(keys['address'], private_key)
result = client.submit(tx_CHOICE_ALGO, wait=True)
print(result)
