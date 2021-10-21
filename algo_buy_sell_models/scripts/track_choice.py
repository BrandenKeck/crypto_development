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
algod_token = keys['algod_token_1']
headers = {"X-API-Key": algod_token}
algod_client = algod.AlgodClient(algod_token, algod_address, headers)

# Get TMan Client / 350338509 is the app ID for all TinymanClient implementations
from tinyman.v1.client import TinymanClient
client = TinymanClient(algod_client, 350338509)

# Fetch assets / Asset IDs from algo explorer
ALGO = client.fetch_asset(0)
CHOICE = client.fetch_asset(297995609)
USDC = client.fetch_asset(31566704)

# Fetch the pool we will work with
ALGO_USDC = client.fetch_pool(ALGO, USDC)
CHOICE_ALGO = client.fetch_pool(CHOICE, ALGO) # Two Part Swap CHOICE -> ALGO -> USDC
CHOICE_USDC = client.fetch_pool(CHOICE, USDC) # Direct Comparison CHOICE -> USDC

# Loop for constant price updates
while True:

    # Calculate ALGO -> USDC Swap
    quote_ALGO_USDC = ALGO_USDC.fetch_fixed_input_swap_quote(ALGO(1_000_000), slippage=0)
    algo_out = quote_ALGO_USDC.amount_out_with_slippage
    algo_price = Decimal(algo_out.amount) / Decimal(10**algo_out.asset.decimals)

    # Calculate CHOICE -> ALGO Swap
    quote_CHOICE_ALGO = CHOICE_ALGO.fetch_fixed_input_swap_quote(CHOICE(100), slippage=0)
    choice_out = quote_CHOICE_ALGO.amount_out_with_slippage
    choice_out_qty = Decimal(choice_out.amount) / Decimal(10**choice_out.asset.decimals)
    choice_price = algo_price * choice_out_qty

    # Calculate CHOICE -> USDC Swap to compare
    quote_CHOICE_USDC = CHOICE_USDC.fetch_fixed_input_swap_quote(CHOICE(100), slippage=0)
    direct_choice_out = quote_CHOICE_USDC.amount_out_with_slippage
    direct_choice_price = Decimal(direct_choice_out.amount) / Decimal(10**direct_choice_out.asset.decimals)


    # Get timestamp
    now = datetime.now()
    current_time = now.strftime("%d-%b-%Y %H:%M:%S")

    # Print results
    print(f'\r')
    print(f'[{current_time}]')
    print(f'ALGO -> USDC (Direct Swap): {algo_price}')
    print(f'CHOICE -> ALGO -> USDC Rate: {choice_price}')
    print(f'CHOICE -> USDC (Direct Swap): {direct_choice_price}')

    # Wait ten seconds before checking again
    time.sleep(10)
