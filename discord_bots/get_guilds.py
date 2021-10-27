# Imports
import json, discord
from discord.ext import commands

# Get bot tokens
f = open('keys.json',)
keys = json.load(f)
f.close()

# Create a discord client
dicord_client = discord.Client()

# Create a client event
@dicord_client.event
async def on_ready():

    # Establish Discord Connections
    for guild in dicord_client.guilds:
        print(guild.id)

# Run the client and commander
dicord_client.run(keys['bot_token'])
