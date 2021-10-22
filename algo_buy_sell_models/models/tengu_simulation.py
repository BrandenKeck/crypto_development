# Move up a level in the directory
# REMOVE IF RUNNING THIS SCRIPT INDEPENDENT OF THIS PROJECT
import sys
sys.path.append("..")

# Imports
import json, time
from datetime import datetime
from algosdk import mnemonic
from algosdk.v2client import algod
from tinyman.v1.client import TinymanClient

class tengu_sim:

    def __init__(self, asset, slips=0.005, asset_amounts=100,
                    usd_trade_size=1, asset_trade_size=1,
                    swap_threshold = 0.02, timestep=60):

        # Import APIs and SDKs
        self.clidex = 0
        self.keys = self.load_keys()
        self.algod_clients = self.load_algod_clients()
        self.tinyman_clients = self.load_tinyman_clients()
        self.algo = self.tinyman_clients[self.get_clidex()].fetch_asset(0)
        self.usdc = self.tinyman_clients[self.get_clidex()].fetch_asset(31566704)
        self.asset = self.tinyman_clients[self.get_clidex()].fetch_asset(asset)

        # Establish Initial Swaprates
        self.u2a_baseline = self.swap(1, self.usdc, self.asset, 0)
        self.a2u_baseline = self.swap(1, self.asset, self.usdc, 0)

        # Establish Simulation Parameters
        self.slips = slips
        self.num_swaps = 0
        self.uts = usd_trade_size
        self.ats = asset_trade_size
        self.st = swap_threshold
        self.ts = timestep
        self.wallet = {
            "USDC": asset_amounts,
            "ASSET": self.swap(1, self.usdc, self.asset, 0) * asset_amounts,
        }

        # Store original asset amounts
        self.usdc0 = self.wallet["USDC"]
        self.asset0 = self.wallet["ASSET"]

    # Execute Tengu Simulation
    def run(self):

        # Game Loop
        while True:

            # Add a line to the output; print current time
            print(f'\r')
            now = datetime.now()
            current_time = now.strftime("%d-%b-%Y %H:%M:%S")
            print(f'[{current_time}]')

            # Get Current Rates
            u2a_current = self.swap(1, self.usdc, self.asset, 0)
            a2u_current = self.swap(1, self.asset, self.usdc, 0)

            # Calculate Change In Rates
            u2a_percent_change = (u2a_current - self.u2a_baseline) / self.u2a_baseline
            a2u_percent_change = (a2u_current - self.a2u_baseline) / self.a2u_baseline

            # Make Swap if Threshold Broken
            if u2a_percent_change > self.st:
                usdc_in = (100 * u2a_percent_change) * self.uts
                asset_out = self.swap(usdc_in, self.usdc, self.asset, self.slips)
                self.wallet["USDC"] = self.wallet["USDC"] - usdc_in
                self.wallet["ASSET"] = self.wallet["ASSET"] + asset_out
                self.u2a_baseline = u2a_current
                self.num_swaps = self.num_swaps + 1
                print(f'Swapped {usdc_in} USDC for {asset_out} {self.asset.name} given rate change {u2a_percent_change}')

            elif a2u_percent_change > self.st:
                asset_in = (100 * a2u_percent_change) * self.ats
                usdc_out = self.swap(asset_in, self.asset, self.usdc, self.slips)
                self.wallet["USDC"] = self.wallet["USDC"] + usdc_out
                self.wallet["ASSET"] = self.wallet["ASSET"] - asset_in
                self.a2u_baseline = a2u_current
                self.num_swaps = self.num_swaps + 1
                print(f'Swapped {asset_in} {self.asset.name} for {usdc_out} USDC given rate change {a2u_percent_change}')

            # Print Results and Wait Timestep
            print(f'Num Swaps: {self.num_swaps}')
            print(f'{self.asset.name} Price: {a2u_current} vs. Baseline: {self.a2u_baseline} at {u2a_percent_change}%')
            print(f'USDC Price: {u2a_current} vs. Baseline: {self.u2a_baseline} at {a2u_percent_change}%')
            print(f'Wallet Size: {self.get_wallet_balance()} with {self.usdc0} USDC and {self.asset0} {self.asset.name}')
            time.sleep(self.ts)

    # Swap function wrapper
    def swap(self, amount, asset1, asset2, slips):
        amt_in = asset1(int(amount * 10**asset1.decimals))
        pool = self.tinyman_clients[self.get_clidex()].fetch_pool(asset1, asset2)
        quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
        amt_out = quote.amount_out_with_slippage
        return amt_out.decimal_amount

    def get_wallet_balance(self):
        asset_to_usdc = self.swap(1, self.asset, self.usdc, 0)
        algo_to_usdc = self.swap(1, self.algo, self.usdc, 0)
        balance = self.wallet["USDC"] + asset_to_usdc*self.wallet["ASSET"] - self.num_swaps*0.002*algo_to_usdc
        return balance

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

    def get_clidex(self):
        self.clidex = self.clidex + 1
        if self.clidex >= len(self.algod_clients):
            self.clidex = 0

        return self.clidex

#
# HARDCODED OUT THE SECOND API
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#

# Run with YLDY
mysim = tengu_sim(226701642)
mysim.run()
print(mysim.get_wallet_balance())
