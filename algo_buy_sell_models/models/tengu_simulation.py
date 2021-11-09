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

class tengu_sim:

    def __init__(self,
                asset1=0, asset2=226701642,                   # Assets
                slips=0.005, asset_amounts=100, timestep=180, # Trade Settings (in USD)
                alpha=0.01, beta=0.05, gamma=0.60,            # Model Shape Params
                Pmax=1, Tmin=0, Tmax=500,                     # Model Buy/Sell Params (in USD)
                ):

        # Import APIs and SDKs
        self.clidex = 0
        self.keys = self.load_keys()
        self.algod_clients = self.load_algod_clients()
        self.tinyman_clients = self.load_tinyman_clients()

        # Get Assets from TinymanClient
        self.algo = self.tinyman_clients[self.get_clidex()].fetch_asset(0)
        self.usdc = self.tinyman_clients[self.get_clidex()].fetch_asset(31566704)
        self.asset1 = self.tinyman_clients[self.get_clidex()].fetch_asset(asset1)
        self.asset2 = self.tinyman_clients[self.get_clidex()].fetch_asset(asset2)

        # Establish Simulation Parameters
        self.slips = slips
        self.dt = timestep
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.Pmax = Pmax
        self.Tmin = Tmin
        self.Tmax = Tmax

        # Establish Initial Swaprate Baselines
        self.algo_to_usdc = 0
        self.asset1_to_usdc = 0
        self.asset2_to_usdc = 0
        self.a1toa2_current = 0
        self.a2toa1_current = 0
        self.a1toa2_baseline = self.swap(1, self.asset1, self.asset2, 0)
        self.a2toa1_baseline = self.swap(1, self.asset2, self.asset1, 0)
        self.a1toa2_baseline_change = 0
        self.a2toa1_baseline_change = 0

        # Simulation Components - Store original values, track wallet, etc
        self.init_asset1_price = self.swap(1, self.usdc, self.asset1, 0)
        self.init_asset2_price = self.swap(1, self.usdc, self.asset2, 0)
        self.init_asset1 = self.init_asset1_price * asset_amounts
        self.init_asset2 = self.init_asset2_price * asset_amounts
        self.wallet = {
            "ASSET1": self.init_asset1,
            "ASSET2": self.init_asset2,
            "ALGO_FEES": 0
        }

    # Execute Tengu Simulation
    def run(self):

        # Game Loop
        while True:

            # Get Current Time for Output
            now = datetime.now()
            current_time = now.strftime("%d-%b-%Y %H:%M:%S")

            # Call baseline change function
            self.get_rates()

            # Try Direction 1; Asset 1 -> Asset 2
            if self.heaviside(self.a1toa2_baseline_change):
                px = self.modified_logistic(self.a1toa2_baseline_change)
                if px*self.wallet["ASSET1"] > self.Tmax/self.asset1_to_usdc:
                    a1_in = self.Tmax/self.asset1_to_usdc
                    a2_out = self.swap(a1_in, self.asset1, self.asset2, self.slips)
                    self.a1toa2_baseline = self.swap(1, self.asset1, self.asset2, 0)
                elif px*self.wallet["ASSET1"] > self.Tmin/self.asset1_to_usdc:
                    a1_in = px*self.wallet["ASSET1"]
                    a2_out = self.swap(a1_in, self.asset1, self.asset2, self.slips)
                    self.a1toa2_baseline = self.swap(1, self.asset1, self.asset2, 0)
                else:
                    a1_in = 0
                    a2_out = 0

                # Update Balances
                self.wallet["ASSET1"] = self.wallet["ASSET1"] - a1_in
                self.wallet["ASSET2"] = self.wallet["ASSET2"] + a2_out
                self.wallet["ALGO_FEES"] = self.wallet["ALGO_FEES"] + 0.002
                print(f'[{current_time}] Swapped {round(a1_in,2)} {self.asset1.name} for ' +
                f'{round(a2_out,2)} {self.asset2.name} given rate change {round(self.a1toa2_baseline_change,2)}')

            # Try Direction 2; Asset 2 -> Asset 1
            if self.heaviside(self.a2toa1_baseline_change):
                px = self.modified_logistic(self.a2toa1_baseline_change)
                if px*self.wallet["ASSET2"] > self.Tmax/self.asset2_to_usdc:
                    a2_in = self.Tmax/self.asset2_to_usdc
                    a1_out = self.swap(a2_in, self.asset2, self.asset1, self.slips)
                    self.a2toa1_baseline = self.swap(1, self.asset2, self.asset1, 0)
                elif px*self.wallet["ASSET2"] > self.Tmin*self.asset2_to_usdc:
                    a2_in = px*self.wallet["ASSET2"]
                    a1_out = self.swap(a2_in, self.asset2, self.asset1, self.slips)
                    self.a2toa1_baseline = self.swap(1, self.asset2, self.asset1, 0)
                else:
                    a2_in = 0
                    a1_out = 0

                # Update Balances
                self.wallet["ASSET2"] = self.wallet["ASSET2"] - a2_in
                self.wallet["ASSET1"] = self.wallet["ASSET1"] + a1_out
                self.wallet["ALGO_FEES"] = self.wallet["ALGO_FEES"] + 0.002
                print(f'[{current_time}] Swapped {round(a2_in,2)} {self.asset2.name} for ' +
                f'{round(a1_out,2)} {self.asset1.name} given rate change {round(self.a2toa1_baseline_change,2)}')

            # Print Results and Wait Timestep
            print(f'[{current_time}] Wallet Size: ${round(self.get_wallet_balance(),2)} | ' +
            f'{self.asset1.name}: {round(self.wallet["ASSET1"],2)} | ' +
            f'{self.asset2.name}: {round(self.wallet["ASSET2"],2)} | ' +
            f'Fees: {round(self.wallet["ALGO_FEES"])} | \n' +
            f'Baseline 1: {self.a1toa2_baseline_change}, px: {self.modified_logistic(self.a1toa2_baseline_change)} | ' +
            f'Baseline 2: {self.a2toa1_baseline_change}, px: {self.modified_logistic(self.a2toa1_baseline_change)}')
            time.sleep(self.dt)



    # Swap function wrapper
    def swap(self, amount, asset1, asset2, slips):
        amt_in = asset1(int(amount * 10**asset1.decimals))
        pool = self.tinyman_clients[self.get_clidex()].fetch_pool(asset1, asset2)
        quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
        amt_out = quote.amount_out_with_slippage
        return amt_out.decimal_amount

    # Function to calculate % change in asset rates
    def get_rates(self):

        # USDC rates
        self.algo_to_usdc = self.swap(1, self.algo, self.usdc, 0)
        self.asset1_to_usdc = self.swap(1, self.asset1, self.usdc, 0)
        self.asset2_to_usdc = self.swap(1, self.asset2, self.usdc, 0)

        # Get Current Rates
        self.a1toa2_current = self.swap(1, self.asset1, self.asset2, 0)
        self.a2toa1_current = self.swap(1, self.asset2, self.asset1, 0)

        # Calculate Change In Rates
        self.a1toa2_baseline_change = (self.a1toa2_current - self.a1toa2_baseline) / self.a1toa2_baseline
        self.a2toa1_baseline_change = (self.a2toa1_current - self.a2toa1_baseline) / self.a2toa1_baseline

    # Basic Function to Covert Wallet into USDC
    def get_wallet_balance(self):
        return self.asset1_to_usdc*self.wallet["ASSET1"] + self.asset2_to_usdc*self.wallet["ASSET2"] - self.algo_to_usdc*self.wallet["ALGO_FEES"]

    # Get API Key from External File
    def load_keys(self):
        f = open('../keys.json',)
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

    # Simple Logistic Eqn Implementation
    def modified_logistic(self, x):
        return self.Pmax / (1 + ((1 - self.beta) / self.beta)**((-x - self.gamma)/(self.alpha - self.gamma)))

    # Simple Heaviside Implementation
    def heaviside(self, x):
        if x > -self.alpha: return False
        else: return True

# Run with default ALGO/YLDY
mysim = tengu_sim()
mysim.run()
print(mysim.get_wallet_balance())
