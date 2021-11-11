# Imports
import json, time
from datetime import datetime
from algosdk.v2client import algod
from tinyman.v1.client import TinymanClient
import discord
from discord.ext import commands

# Get bot tokens
f = open('keys.json',)
keys = json.load(f)
f.close()

# Create a discord client
dicord_client = discord.Client()

# Get Algo Client / Using purestake; supplement your own API key for the algod_token
algod_address = 'https://mainnet-algorand.api.purestake.io/ps2'
algod_token = keys['algod_token']
headers = {'X-API-Key': algod_token}
algod_client = algod.AlgodClient(algod_token, algod_address, headers)

# Get TMan Client / 350338509 is the app ID for all TinymanClient implementations
# Get Assets and Pools - ALGO, CHOICE, USDC
tinyman = TinymanClient(algod_client, 350338509)
ALGO = tinyman.fetch_asset(0)
CHOICE = tinyman.fetch_asset(297995609)
USDC = tinyman.fetch_asset(31566704)
ALGO_USDC = tinyman.fetch_pool(ALGO, USDC)
CHOICE_ALGO = tinyman.fetch_pool(CHOICE, ALGO)

# Retrieve price of choice
def get_prices():
    quote_ALGO_USDC = ALGO_USDC.fetch_fixed_input_swap_quote(ALGO(1_000_000), slippage=0)
    algo_price = float(quote_ALGO_USDC.amount_out_with_slippage.amount) / float(10**quote_ALGO_USDC.amount_out_with_slippage.asset.decimals)
    quote_CHOICE_ALGO = CHOICE_ALGO.fetch_fixed_input_swap_quote(CHOICE(100), slippage=0)
    choice_out = float(quote_CHOICE_ALGO.amount_out_with_slippage.amount) / float(10**quote_CHOICE_ALGO.amount_out_with_slippage.asset.decimals)
    choice_price = round(algo_price * choice_out, 4)
    return choice_price

# Create a client event
@dicord_client.event
async def on_ready():

    # Get some prices before kicking off the update loop
    choice_price = get_prices()
    choice_baseline = choice_price
    baseline_change = 0

    # Begin loop
    pings = 0
    while True:

        # Every five pings update status
        if pings >= 5:

            # Tinyman call - every five minutes update the Choice price and Algo price
            choice_price = get_prices()
            baseline_change = 100 * (choice_price - choice_baseline) / choice_baseline

            if abs(baseline_change) > 10:

                # Post to crypto guild specifically
                crypto_guild = dicord_client.get_guild(805183939148513311)
                crypto_bot_channel = crypto_guild.get_channel(901082610334306345)

                # Send ALGO / CHOICE price to discord on 10% change
                await crypto_bot_channel.send(
                    f"Hello Everybody!\n" +
                    f"It's been awhile since I've checked in!\n" +
                    f"There's been some movement in Choice Coin, a change of **{round(baseline_change, 2)}%**!\n"
                    f'The current price of Choice Coin is **${choice_price}** :rocket:'
                );
                choice_baseline = choice_price

            # Log Health Status - every five pings update console
            print(f'\r')
            now = datetime.now()
            current_time = now.strftime("%d-%b-%Y %H:%M:%S")
            print(f'[{current_time}] CHOICE = ${choice_price} with baseline_change of {round(baseline_change, 2)}')

            # Reset Ping Clock
            pings = 0

        # Updat bot status
        for guild in dicord_client.guilds:
            curr_guild = dicord_client.get_guild(guild.id)
            curr_bot = curr_guild.me
            await curr_bot.edit(nick = f'${choice_price}')

        # Every five updates add a ping
        pings = pings + 1
        time.sleep(10)

# Run the client and commander
dicord_client.run(keys['bot_token'])
