# Move up a level in the directory
# REMOVE IF RUNNING THIS SCRIPT INDEPENDENT OF THIS PROJECT
import sys
sys.path.append("..")

# Imports and JSON keys (API key untracked in repo for security)
import json, time
from datetime import datetime
from decimal import Decimal
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

# Fetch assets / Asset IDs from algo explorer
LION = client.fetch_asset(372666897)
USDC = client.fetch_asset(31566704)
LION_USDC = client.fetch_pool(LION, USDC)

# Loop for constant price updates
while True:

    # Calculate CHOICE -> USDC Swap to compare
    quote_LION_USDC = LION_USDC.fetch_fixed_input_swap_quote(LION(10_000), slippage=0)
    lion_price = quote_LION_USDC.amount_out_with_slippage
    lion_price = float(lion_price.amount) / float(10**lion_price.asset.decimals)
    time.sleep(5)

    # Get timestamp
    now = datetime.now()
    current_time = now.strftime("%d-%b-%Y %H:%M:%S")

    # Print results
    print(f'\r')
    print(f'[{current_time}]')
    print(f'LION -> USDC (Direct Swap): {lion_price}')
