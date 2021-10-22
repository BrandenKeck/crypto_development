# Imports
import os, json, time
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
discord_commander = commands.Bot(command_prefix="!")

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
    algo_price = quote_ALGO_USDC.amount_out_with_slippage.decimal_amount
    quote_CHOICE_ALGO = CHOICE_ALGO.fetch_fixed_input_swap_quote(CHOICE(100), slippage=0)
    choice_out = quote_CHOICE_ALGO.amount_out_with_slippage.decimal_amount
    choice_price = round(algo_price * choice_out, 4)
    return choice_price

# Command to show the price immediately
@discord_commander.command()
async def choice_price(ctx):
    sender = str(ctx.author).split("#")[0]
    choice_price = get_prices()
    await ctx.send(
        f'Hello There, {sender}\n' +
        f'The current price of Choice Coin is **${choice_price}**\n' +
        f':rocket: :rocket: :rocket: BALLS DEEP :rocket: :rocket: :rocket:'
    )

# Create a client event
@dicord_client.event
async def on_ready():

    # Establish Discord Connections
    guild = dicord_client.get_guild(805183939148513311)
    bot_channel = guild.get_channel(901082610334306345)
    bot = guild.me

    # Get some prices before kicking off the update loop
    choice_price = get_prices()
    choice_baseline = choice_price

    # Begin loop
    pings = 0
    while True:

        # Every five pings update status
        if pings >= 5:

            # Tinyman call - every five minutes update the Choice price and Algo price
            choice_price = get_prices()
            baseline_change = 100 * (choice_price - choice_baseline) / choice_baseline

            if abs(baseline_change) > 10:

                # Send ALGO / CHOICE price to discord on 10% change
                await bot_channel.send(
                    f"Hello Everybody!\n" +
                    f"It's been awhile since I've checked in!\n" +
                    f"There's been some movement in Choice Coin, a change of **{baseline_change}%**!\n"
                    f'The current price of Choice Coin is **${choice_price}**\n' +
                    f':rocket: :rocket: :rocket: BALLS DEEP :rocket: :rocket: :rocket:'
                );
                choice_baseline = choice_price

            # Log Health Status - every five pings update console
            print(f'\r')
            now = datetime.now()
            current_time = now.strftime("%d-%b-%Y %H:%M:%S")
            print(f'[{current_time}] CHOICE = ${choice_price}')

            # Reset Ping Clock
            pings = 0

        # Update clock and bot status every five seconds
        pings = pings + 1
        await bot.edit(nick = f'${choice_price}')

# Run the client and commander
discord_commander.run(keys['bot_token'])
dicord_client.run(keys['bot_token'])
