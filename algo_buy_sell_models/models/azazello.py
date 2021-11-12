# Move up a level in the directory
# REMOVE IF RUNNING THIS SCRIPT INDEPENDENT OF THIS PROJECT
import sys
sys.path.append("..")

# Imports
import json, time
import numpy as np
from datetime import datetime
from algosdk import mnemonic
from algosdk.v2client import algod
from tinyman.v1.client import TinymanClient

class azazello:

    def __init__(self, slips=0.001, timestep=301, default=True):

        # Import APIs and SDKs
        self.clidex = 0
        self.keys = self.load_keys()
        self.algod_clients = self.load_algod_clients()
        self.tinyman_clients = self.load_tinyman_clients()

        # Setup multi-tengu swaps
        self.assets = dict()
        self.tengu = []
        if default:
            pass

    # Azazello gameloop
    def run(self):

        while True:

            # Calculate baseline change
            self.get_rates()

            # Loop over tengu
            for tt in self.tengu:
                pass

            # Await next swap attempt
            time.sleep(self.dt)

    def add_tengu(self, asset1, asset2
                  swap100 = 100, swapmin=0, swapmax=500,  # Swap Scale (in USD)
                  alpha=0.005, beta=0.020, gamma=0.400,   # Model Shape Params
                  ):

        # Get Assets from TinymanClient
        self.usdc = self.tinyman_clients[self.get_clidex()].fetch_asset(31566704)
        self.asset1 = self.tinyman_clients[self.get_clidex()].fetch_asset(asset1)
        self.asset2 = self.tinyman_clients[self.get_clidex()].fetch_asset(asset2)

    # Retrieve Asset Amount from Wallet
    def get_wallet_asset_amt(self, asset_id):

        # Retrieve Wallet Data
        wallet = self.algod_clients[self.get_clidex()].account_info(self.keys["address"])

        # Handle ASAs
        if asset_id > 0:
            asset_decimals = self.algod_clients[self.get_clidex()].asset_info(asset_id)["params"]["decimals"]
            asset_position = next(item for item in wallet["assets"] if item["asset-id"] == asset_id)
            asset_amt = asset_position["amount"] * 10**(-asset_decimals)

        # Handle Algo
        else:
            asset_decimals = 6
            asset_amt = wallet["amount"] * 10**(-asset_decimals)

        # Return Amount
        return asset_amt

    # Get API Key from External File
    def load_keys(self):
        f = open("../keys.json",)
        keys = json.load(f)
        f.close()
        return keys

    # Load Algod Client
    def load_algod_clients(self):

        # Load client keys from external (untracked) file
        clients = []
        algod_address = "https://mainnet-algorand.api.purestake.io/ps2"
        for key in self.keys["algod_tokens"]:
            algod_token = key
            algod_headers = {"X-API-Key": algod_token}
            algod_client = algod.AlgodClient(algod_token, algod_address, algod_headers)
            clients.append(algod_client)

        # Return list of clients
        return clients

    # Load Tinyman Clients
    def load_tinyman_clients(self):

        # Load Tinyman Client for each Algod Client
        clients = []
        for client in self.algod_clients:
            clients.append(TinymanClient(client, 350338509))

        # Return list of clients
        return clients

    # Counter function; Increments Index and Returns Value
    def get_clidex(self):
        self.clidex = self.clidex + 1
        if self.clidex >= len(self.algod_clients):
            self.clidex = 0

        # Return Index Value
        return self.clidex


class tengu:

    def __init__(self,
                asset1=0, asset2=31566704,              # Assets Settings
                swap100 = 100, swapmin=0, swapmax=500,  # Swap Scale (in USD)
                alpha=0.005, beta=0.020, gamma=0.400,   # Model Shape Params
                ):



        # Establish Simulation Parameters
        self.slips = slips
        self.dt = timestep
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        # Swap amount settings
        self.swap100 = swap100
        self.swapmin = swapmin
        self.swapmax = swapmax

        # Establish Baselines
        self.a1toa2_baseline_change = 0
        self.a2toa1_baseline_change = 0
        self.a1toa2_baseline = self.test_swap(1, self.asset1, self.asset2, 0)
        self.a2toa1_baseline = self.test_swap(1, self.asset2, self.asset1, 0)

        # Establish Initial Swaprates
        self.usdc_to_asset1 = 0
        self.usdc_to_asset2 = 0
        self.a1toa2_current = 0
        self.a2toa1_current = 0
        self.get_rates()

        # Simulation Components - Store original values, track wallet, etc
        self.init_asset1_price = self.usdc_to_asset1
        self.init_asset2_price = self.usdc_to_asset2
        self.init_asset1_usdc = self.init_asset1_price * self.get_wallet_asset_amt(self.asset1.id)
        self.init_asset2_usdc = self.init_asset2_price * self.get_wallet_asset_amt(self.asset2.id)

    # Execute Tengu Simulation
    def attempt_swap(self):

            # Get Current Time for Output
            now = datetime.now()
            current_time = now.strftime("%d-%b-%Y %H:%M:%S")



            # Try Direction 1; Asset 1 -> Asset 2
            if self.heaviside(self.a1toa2_baseline_change):
                #a1_available = self.get_wallet_asset_amt(self.asset1.id)
                px = self.modified_logistic(self.a1toa2_baseline_change)
                if px * (self.swap100 * self.usdc_to_asset1) > self.swapmax * self.usdc_to_asset1:
                    swap_result = self.live_swap(
                        amount = self.swapmax * self.usdc_to_asset1,
                        asset1 = self.asset1,
                        asset2 = self.asset2,
                        slips = self.slips
                    )
                    self.a1toa2_baseline = self.test_swap(1, self.asset1, self.asset2, 0)
                    self.a2toa1_baseline = self.test_swap(1, self.asset2, self.asset1, 0)
                    print(swap_result)
                elif px * (self.swap100 * self.usdc_to_asset1)  > self.swapmin * self.usdc_to_asset1:
                    swap_result = self.live_swap(
                        amount = px * (self.swap100 * self.usdc_to_asset1),
                        asset1 = self.asset1,
                        asset2 = self.asset2,
                        slips = self.slips
                    )
                    if swap_result != "SWAP FAILURE":
                        self.a1toa2_baseline = self.test_swap(1, self.asset1, self.asset2, 0)
                        self.a2toa1_baseline = self.test_swap(1, self.asset2, self.asset1, 0)
                    print(swap_result)
                else: print(f"Minimum Swap Not Achieved: {round(self.swapmin*self.usdc_to_asset1, 2)}")

            # Try Direction 2; Asset 2 -> Asset 1
            if self.heaviside(self.a2toa1_baseline_change):
                #a2_available = self.get_wallet_asset_amt(self.asset2.id)
                px = self.modified_logistic(self.a2toa1_baseline_change)
                if px * (self.swap100 * self.usdc_to_asset2) > self.swapmax * self.usdc_to_asset2:
                    swap_result = self.live_swap(
                        amount = self.swapmax * self.usdc_to_asset2,
                        asset1 = self.asset2,
                        asset2 = self.asset1,
                        slips = self.slips
                    )
                    self.a1toa2_baseline = self.test_swap(1, self.asset1, self.asset2, 0)
                    self.a2toa1_baseline = self.test_swap(1, self.asset2, self.asset1, 0)
                    print(swap_result)
                elif px * (self.swap100 * self.usdc_to_asset2) > self.swapmin * self.usdc_to_asset2:
                    swap_result = self.live_swap(
                        amount = px * (self.swap100 * self.usdc_to_asset2),
                        asset1 = self.asset2,
                        asset2 = self.asset1,
                        slips = self.slips
                    )
                    if swap_result != "SWAP FAILURE":
                        self.a1toa2_baseline = self.test_swap(1, self.asset1, self.asset2, 0)
                        self.a2toa1_baseline = self.test_swap(1, self.asset2, self.asset1, 0)
                    print(swap_result)
                else: print(f"Minimum Swap Not Achieved: {round(self.swapmin*self.usdc_to_asset2, 2)}")

            # Print Results and Wait Timestep
            print(f"[{current_time}] " +
            f"{self.asset1.name}/{self.asset2.name} Baseline: {round(100*self.a1toa2_baseline_change,2)}% | " +
            f"{self.asset2.name}/{self.asset1.name} Baseline: {round(100*self.a2toa1_baseline_change,2)}%")



    # Rate Function function wrapper
    def live_swap(self, amount, asset1, asset2, slips):
        try:
            amt_in = asset1(int(amount * 10**asset1.decimals))
            pool = self.tinyman_clients[self.get_clidex()].fetch_pool(asset1, asset2)
            quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
            tx = pool.prepare_swap_transactions_from_quote(quote, swapper_address=self.keys["address"])
            tx.sign_with_private_key(self.keys["address"], mnemonic.to_private_key(self.keys["mnemonic"]))
            swap_result = self.tinyman_clients[self.get_clidex()].submit(tx, wait=True)
        except: swap_result = "SWAP FAILURE"
        return swap_result

    # Rate Function wrapper
    def test_swap(self, amount, asset1, asset2, slips):
        amt_in = asset1(int(amount * 10**asset1.decimals))
        pool = self.tinyman_clients[self.get_clidex()].fetch_pool(asset1, asset2)
        quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
        amt_out = quote.amount_out_with_slippage
        return float(amt_out.amount) / float(10**amt_out.asset.decimals)

    # Function to calculate % change in asset rates
    def get_rates(self):

        # USDC rates
        if self.asset1.id == 31566704: self.usdc_to_asset1 = 1
        else: self.usdc_to_asset1 = self.test_swap(1, self.usdc, self.asset1, 0)
        if self.asset2.id == 31566704: self.usdc_to_asset2 = 1
        else: self.usdc_to_asset2 = self.test_swap(1, self.usdc, self.asset2, 0)

        # Get Current Rates
        self.a1toa2_current = self.test_swap(1, self.asset1, self.asset2, 0)
        self.a2toa1_current = self.test_swap(1, self.asset2, self.asset1, 0)

        # Calculate Change In Rates
        self.a1toa2_baseline_change = (self.a1toa2_current - self.a1toa2_baseline) / self.a1toa2_baseline
        self.a2toa1_baseline_change = (self.a2toa1_current - self.a2toa1_baseline) / self.a2toa1_baseline

    # Simple Logistic Eqn Implementation
    def modified_logistic(self, x):
        return 1 / (1 + ((1 - self.beta) / self.beta)**((-x - self.gamma)/(self.alpha - self.gamma)))

    # Simple Heaviside Implementation
    def heaviside(self, x):
        if x > -self.alpha: return False
        else: return True

# Run with default settings
aa = azazello()
aa.run()
