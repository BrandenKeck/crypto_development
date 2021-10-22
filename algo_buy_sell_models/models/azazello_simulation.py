# Move up a level in the directory
# REMOVE IF RUNNING THIS SCRIPT INDEPENDENT OF THIS PROJECT
import sys
sys.path.append("..")

# Imports
import json, time
from datetime import datetime
from decimal import Decimal
from algosdk import mnemonic
from algosdk.v2client import algod
from tinyman.v1.client import TinymanClient

class azazello_sim:

    def __init__(self, slips=0.005, asset_amounts=100):

        # Import APIs and SDKs
        self.keys = self.load_keys()
        self.algod_clients = self.load_algod_clients()
        self.tinyman_clients = self.load_tinyman_clients()
        self.clidex = 0

        # Establish Simulation Parameters
        self.slips = slips
        self.assets = self.load_assets()
        self.wallet = self.populate_wallet(asset_amounts)

    # Execute a Cyclic Swap
    def run(self, amount):
        pass

    # Swap function wrapper
    def swap(self, amount, asset1, asset2, slips):
        amt_in = asset1(int(amount * 10**asset1.decimals))
        pool = self.tinyman_clients[self.get_clidex()].fetch_pool(asset1, asset2)
        quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
        amt_out = quote.amount_out_with_slippage
        return amt_out.decimal_amount

    def populate_wallet(self, amt):
        wallet = dict()
        usdc = self.tinyman_clients[self.get_clidex()].fetch_asset(self.assets["USDC"])
        for asset, asset_id in self.assets.items():
            if asset == "USDC":
                wallet["USDC"] = amt
            else:
                curr_asset = self.tinyman_clients[self.get_clidex()].fetch_asset(asset_id)
                ex_rate = self.swap(1, usdc, curr_asset, 0)
                wallet[asset] = amt * ex_rate
        return wallet

    def default_approved_tx():
        pass

    # Get API Key from External File
    def load_keys(self):
        f = open('../keys.json',)
        keys = json.load(f)
        f.close()
        return keys

    # Load Algod Client
    def load_algod_clients(self):
        clients = []
        algod_address = "https://mainnet-algorand.api.purestake.io/ps2"
        for key in self.keys["algod_tokens"]:
            algod_token = key
            algod_headers = {"X-API-Key": algod_token}
            algod_client = algod.AlgodClient(algod_token, algod_address, algod_headers)
            clients.append(algod_client)

        return clients

    def load_tinyman_clients(self):
        clients = []
        for client in self.algod_clients:
            clients.append(TinymanClient(client, 350338509))

        return clients

    def load_assets(self):
        return {
            "ALGO": 0,
            "USDC": 31566704,
            "USDt": 312769,
            "YLDY": 226701642,
            "GEMS": 230946361,
            "OPUL": 287867876,
            "PLANETS": 27165954,
            "SMILE": 300208676,
            "CHOICE": 297995609
        }

    def get_clidex(self):
        self.clidex = self.clidex + 1
        if self.clidex >= len(self.algod_clients):
            self.clidex = 0

        return self.clidex

#
# HARDCODED OUT THE SECOND API
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#

mysim = azazello_sim()
print(mysim.wallet)
