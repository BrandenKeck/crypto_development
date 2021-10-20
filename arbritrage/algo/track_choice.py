# Imports and JSON keys (API key untracked in repo for security)
import json, time
from datetime import datetime
f = open('keys.json',)
keys = json.load(f)
f.close()

# Get Algo Client / Using purestake; supplement your own API key for the algod_token
from algosdk.v2client import algod
algod_address = "https://mainnet-algorand.api.purestake.io/ps2"
algod_token = keys['algod_token']
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
CHOICE_ALGO = client.fetch_pool(CHOICE, ALGO)

# Take a loog at some swaps
while True:

    # Calculate Price
    # Double swap CHOICE -> ALGO -> USDC due to low ALGO-USDC liquidity
    quote_ALGO_USDC = ALGO_USDC.fetch_fixed_input_swap_quote(ALGO(1_000_000), slippage=0)
    quote_CHOICE_ALGO = CHOICE_ALGO.fetch_fixed_input_swap_quote(CHOICE(100), slippage=0)
    decimal_correction = 10 ** (CHOICE.decimals - ALGO.decimals)
    algo_price = quote_ALGO_USDC.price
    choice_price = quote_ALGO_USDC.price * (decimal_correction * quote_CHOICE_ALGO.price)

    # Get timestamp
    now = datetime.now()
    current_time = now.strftime("%d-%b-%Y %H:%M:%S")

    # Print results
    print(f'\r')
    print(f'[{current_time}]')
    print(f'Price of ALGO in USDC: {algo_price}')
    print(f'Price of CHOICE in USDC: {choice_price}')

    # Wait ten seconds before checking again
    time.sleep(10)
