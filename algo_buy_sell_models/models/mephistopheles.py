# Move up a level in the directory
# REMOVE IF RUNNING THIS SCRIPT INDEPENDENT OF THIS PROJECT
import sys, json
sys.path.append("..")

# Imports
import json, time
import numpy as np
from datetime import datetime
from algosdk import mnemonic
from algosdk.v2client import algod
from tinyman.v1.client import TinymanClient

# MEPHISTOPHELES MODEL
# Set up a collection of individual trade pairs (TENGU MODELS)
# Added baseline functionality to allow multiple baselines per tengu with different characteristics
class mephistopheles:

    def __init__(self, slips=0.001, timestep=720, default_model=True,
                load_model=False, save_model=True, model_file="ness.json"):

        # general params
        self.slips = slips
        self.dt = timestep
        self.save_model = save_model
        self.model_file = model_file

        # Import APIs and SDKs
        self.clidex = 0
        self.keys = self.load_keys()
        self.algod_clients = self.load_algod_clients()
        self.tinyman_clients = self.load_tinyman_clients()

        # Setup multi-tengu swaps
        self.assets = dict()
        self.rates = dict()
        self.tengus = []

        # Quick creation for models / load from file / from scratch with default settings
        if load_model:
            self.load_model_from_json()
        elif default_model:
            self.add_tengu(0, 31566704) # ALGO / USDC
            self.add_tengu(0, 226701642) # ALGO / YLDY
            self.add_tengu(0, 27165954) # ALGO / PLANETS
            self.add_tengu(0, 287867876) # ALGO / OPUL
            self.add_tengu(230946361, 31566704) # GEMS / USDC
            self.add_tengu(0, 230946361) # ALGO / GEMS
            self.add_tengu(287867876, 31566704) # OPUL / USDC
            self.add_tengu(0, 300208676) # ALGO / SMILE

    # Azazello gameloop
    def run(self):

        # Turn on USDC -> Asset rates for all assets
        self.set_usdc_active()

        # Start the Game Loop; Run until process is killed
        while True:

            # Get Current Time for Output
            now = datetime.now()
            current_time = now.strftime("%d-%b-%Y %H:%M:%S")
            print(f"[{current_time}] UPDATE -----\n")

            # Update exchange rates for active pairs
            self.get_rates()

            # Update swap formulations
            self.update_tengu()

            # Loop over tengu
            for tt in self.tengus:

                # Set Assets
                a1 = self.assets[tt.a1]["asset"]
                a2 = self.assets[tt.a2]["asset"]

                # attempt forward swap
                if tt.swapforward > 0:
                    swap_result = self.live_swap(
                        amount = tt.swapforward,
                        asset_in = a1,
                        asset_out = a2,
                        slips = self.slips
                    )
                    if swap_result != "SWAP FAILURE":
                        a1toa2 = self.test_swap(1, a1, a2, 0)
                        a2toa1 = self.test_swap(1, a2, a1, 0)
                        tt.set_baseline(a1toa2, a2toa1)
                    print(swap_result)

                # attempt backward swap
                if tt.swapbackward > 0:
                    swap_result = self.live_swap(
                        amount = tt.swapbackward,
                        asset_in = a2,
                        asset_out = a1,
                        slips = self.slips
                    )
                    if swap_result != "SWAP FAILURE":
                        a1toa2 = self.test_swap(1, a1, a2, 0)
                        a2toa1 = self.test_swap(1, a2, a1, 0)
                        tt.set_baseline(a1toa2, a2toa1)
                    print(swap_result)

                # Print Update
                print(f"{a1.name}->{a2.name} Baseline: {round(100*tt.a1toa2_baseline_change,2)}% | " +
                f"{a2.name}->{a1.name} Baseline: {round(100*tt.a2toa1_baseline_change,2)}% -----\n")

            # Save model if configured
            if self.save_model: self.save_model_to_json()

            # Await next swap attempt
            time.sleep(self.dt)

    # Swap an actual amount of an ASA to another asset
    def live_swap(self, amount, asset_in, asset_out, slips):
        try:
            amt_in = asset_in(int(amount * 10**asset_in.decimals))
            pool = self.tinyman_clients[self.get_clidex()].fetch_pool(asset_in, asset_out)
            quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
            tx = pool.prepare_swap_transactions_from_quote(quote, swapper_address=self.keys["address"])
            tx.sign_with_private_key(self.keys["address"], mnemonic.to_private_key(self.keys["mnemonic"]))
            swap_result = self.tinyman_clients[self.get_clidex()].submit(tx, wait=True)
        except: swap_result = "SWAP FAILURE"
        return swap_result

    # Rate Function wrapper; Get exchange amounts without actually swapping;
    def test_swap(self, amount, asset_in, asset_out, slips):
        amt_in = asset_in(int(amount * 10**asset_in.decimals))
        pool = self.tinyman_clients[self.get_clidex()].fetch_pool(asset_in, asset_out)
        quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
        amt_out = quote.amount_out_with_slippage
        return float(amt_out.amount) / float(10**amt_out.asset.decimals)

    # Function to fetch asset rates
    def get_rates(self):

        # Update the Rates Matrix for active rates only
        for a1 in self.rates:
            for a2 in self.rates[a1]:
                if self.rates[a1][a2]["active"]:
                    asset1 = self.assets[a1]["asset"]
                    asset2 = self.assets[a2]["asset"]
                    self.rates[a1][a2]["rate"] = self.test_swap(1, asset1, asset2, 0)

    # Function to update asset pair baseline changes
    def update_tengu(self):

        # Retrieve Wallet Data
        wallet = self.algod_clients[self.get_clidex()].account_info(self.keys["address"])

        for tt in self.tengus:

            # Get available amounts and swap rates
            asset1_id = tt.a1
            asset2_id = tt.a2
            a1_available = self.get_wallet_asset_amt(wallet, asset1_id)
            a2_available = self.get_wallet_asset_amt(wallet, asset2_id)
            a1toa2 = self.rates[asset1_id][asset2_id]["rate"]
            a2toa1 = self.rates[asset2_id][asset1_id]["rate"]

            # Get USDC Rates
            if asset1_id == 31566704: usdctoa1 = 1
            else: usdctoa1 = self.rates[31566704][asset1_id]["rate"]
            if asset2_id == 31566704: usdctoa2 = 1
            else: usdctoa2 = self.rates[31566704][asset2_id]["rate"]

            # Update Tengu
            tt.update(a1_available, a2_available, a1toa2, a2toa1, usdctoa1, usdctoa2)

    # Function to add swap pairs to the simulation.  This can be done manually or with the default init flag.
    def add_tengu(self, asset1_id, asset2_id, baselines):

        # Add assets to asset list if necessary
        if asset1_id > 0: a1dec = self.algod_clients[self.get_clidex()].asset_info(asset1_id)["params"]["decimals"]
        else: a1dec = 6
        if asset1_id not in self.assets:
            self.assets[asset1_id] = {
                "asset": self.tinyman_clients[self.get_clidex()].fetch_asset(asset1_id),
                "decimals": a1dec
            }
        if asset2_id > 0: a2dec = self.algod_clients[self.get_clidex()].asset_info(asset2_id)["params"]["decimals"]
        else: a2dec = 6
        if asset2_id not in self.assets:
            self.assets[asset2_id] = {
                "asset": self.tinyman_clients[self.get_clidex()].fetch_asset(asset2_id),
                "decimals": a2dec
            }

        # Construct rates matrix as needed
        if asset1_id not in self.rates:
            self.rates[asset1_id] = dict()
            for asset in self.assets:
                self.rates[asset1_id][asset] = {
                    "rate": None,
                    "active": False
                }
        if asset2_id not in self.rates:
            self.rates[asset2_id] = dict()
            for asset in self.assets:
                self.rates[asset2_id][asset] = {
                    "rate": None,
                    "active": False
                }
        for asset in self.rates:
            if asset1_id not in self.rates[asset]:
                self.rates[asset][asset1_id] = {
                    "rate": None,
                    "active": False
                }
            if asset2_id not in self.rates[asset]:
                self.rates[asset][asset2_id] = {
                    "rate": None,
                    "active": False
                }
            if asset not in self.rates[asset1_id]:
                self.rates[asset1_id][asset] = {
                    "rate": None,
                    "active": False
                }
            if asset not in self.rates[asset2_id]:
                self.rates[asset2_id][asset] = {
                    "rate": None,
                    "active": False
                }

        # Set active swaprates (don't waste API calls on inactive swaps)
        self.rates[asset1_id][asset2_id]["active"] = True
        self.rates[asset2_id][asset1_id]["active"] = True
        self.rates[asset1_id][asset2_id]["rate"] = self.test_swap(1, self.assets[asset1_id]["asset"], self.assets[asset2_id]["asset"], 0)
        self.rates[asset2_id][asset1_id]["rate"] = self.test_swap(1, self.assets[asset2_id]["asset"], self.assets[asset1_id]["asset"], 0)

        # Create a Tengu
        self.tengus.append(tengu(asset1_id, asset2_id, self.rates[asset1_id][asset2_id]["rate"], self.rates[asset2_id][asset1_id]["rate"], swapmin, swapmax, alpha, beta, gamma))

    # Function to turn on USDC -> Asset rates for all assets
    def set_usdc_active(self):

        # Add USDC if it's not in assets already
        if 31566704 not in self.assets:
            self.assets[31566704] = {
                "asset": self.tinyman_clients[self.get_clidex()].fetch_asset(31566704),
                "decimals": self.algod_clients[self.get_clidex()].asset_info(31566704)["params"]["decimals"]
            }
            self.rates[31566704] = dict()
            for asset in self.rates:
                self.rates[asset][31566704] = {
                    "rate": None,
                    "active": False
                }
                self.rates[31566704][asset] = {
                    "rate": None,
                    "active": False
                }

        # Turn on USDC -> Asset rates for all assets
        for asset in self.rates[31566704]:
            if asset != 31566704:
                self.rates[31566704][asset]['active'] = True

    # Retrieve Asset Amount from Wallet
    def get_wallet_asset_amt(self, wallet, asset_id):

        # Handle ASAs
        if asset_id > 0:
            asset_decimals = self.assets[asset_id]["decimals"]
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

    # Load model from json
    def load_model_from_json(self):

        # Open JSON file
        with open(self.model_file, 'r') as fp:
            onett = json.load(fp)

        # Load in Tengus
        self.tengus = []
        for tt in onett['model']:
            self.add_tengu(
                asset1_id=tt["a1"], asset2_id=tt["a2"],
                swapmin=tt["swapmin"], swapmax=tt["swapmax"],
                alpha=tt["alpha"], beta=tt["beta"], gamma=tt["gamma"]
            )
            self.tengus[len(self.tengus) - 1].set_baseline(tt["a1toa2_baseline"], tt["a2toa1_baseline"])

    # Save model to json
    def save_model_to_json(self):

        # Init an empty model object
        onett = {"model": []}

        # Write Tengus to model
        for tt in self.tengus:
            onett["model"].append(
                {
                "a1": tt.a1,
                "a2": tt.a2,
                "alpha": tt.alpha,
                "beta": tt.beta,
                "gamma": tt.gamma,
                "swapmin": tt.swapmin,
                "swapmax": tt.swapmax,
                "a1toa2_baseline": tt.a1toa2_baseline,
                "a2toa1_baseline": tt.a2toa1_baseline
                }
            )

        # Save to JSON
        with open(self.model_file, 'w') as fp:
            json.dump(onett, fp)

    # Counter function; Increments Index and Returns Value
    def get_clidex(self):
        self.clidex = self.clidex + 1
        if self.clidex >= len(self.algod_clients):
            self.clidex = 0

        # Return Index Value
        return self.clidex

# TENGU MODEL
# Handle individual ASA pair swaps
# Swaps calculated as logistic functions bounded by min(beta*swapmax, swapmin) and swapmax
#   Swap excuted after a percent change of alpha is reached
#   Swap function shape is defined by alpha, beta, and gamma parameters
class tengu:

    def __init__(self,
                asset1, asset2,       # Assets Settings
                a1a2bl, a2a1bl,       # Initial Baselines
                swapmin, swapmax,     # Swap Scale (in USD)
                alpha, beta, gamma,   # Model Shape Params
                ):

        # Store Asset IDs
        self.a1 = asset1
        self.a2 = asset2

        # List of Swap Baselines
        self.sacis = dict()

    # Add a new baseline for the swap pair
    def add_saci(self, swapmin=0, swapmax=600, alpha=0.030, beta=0.025, gamma=0.800):
        pass

    # Update baseline models
    def update_saci(self):

        # Loop over all baselines
        for ss in self.sacis:
            pass

    # Set baseline after an executed swap
    def set_saci(self, id):
        pass


# SACI UTILITY
# A scaling baseline utility for the TENGU swap sub-model
class saci:

    def __init__(self,
                swapmin, swapmax,     # Swap Scale (in USD)
                alpha, beta, gamma,   # Model Shape Params
                alpha_scaling,        # Directional alpha param scaling
                beta_scaling,         # Directional beta param scaling
                gamma_scaling,        # Directional gamma param scaling
                num_timesteps         # Number of timesteps for baseline calc
                ):

        # Establish Shape Parameters
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        # Swap amount settings
        self.swapmin = swapmin
        self.swapmax = swapmax
        self.ascale = alpha_scaling
        self.bscale = beta_scaling
        self.gscale = gamma_scaling
        self.ndt = num_timesteps

        # Actual System State
        self.swapforward = 0
        self.swapbackward = 0
        self.directionality = 0
        self.skip_step = 0

        # Establish Baselines
        self.a1a2_baseline = 0
        self.a2a1_baseline = 0
        self.a1a2_baseline_change = 0
        self.a2a1_baseline_change = 0

    # Update exchange rates; calculate swap amounts
    def update(self,
        a1_available, a2_available,
        a1_to_a2, a2_to_a1,
        usdc_to_a1, usdc_to_a2):

        # Check Skip Step
        if self.skipper():

            # Update Baseline Changes
            self.a1a2_baseline_change = (a1_to_a2 - self.a1a2_baseline) / self.a1a2_baseline
            self.a2a1_baseline_change = (a2_to_a1 - self.a2a1_baseline) / self.a2a1_baseline

            # Calculate Forward Swap
            self.swapforward = 0
            heaviside_forward = self.heaviside(self.a1a2_baseline_change)
            logistic_forward = self.modified_logistic(self.a1a2_baseline_change)
            minswap_forward = self.swapmin * usdc_to_a1
            self.swapforward = heaviside_forward * logistic_forward * (self.swapmax * usdc_to_a1)
            if self.swapforward < minswap_forward or a1_available < self.swapforward: self.swapforward = 0

            # Calculate Backward Swap
            self.swapbackward = 0
            heaviside_backward = self.heaviside(self.a2a1_baseline_change)
            logistic_backward = self.modified_logistic(self.a2a1_baseline_change)
            minswap_backward = self.swapmin * usdc_to_a2
            self.swapbackward = heaviside_backward * logistic_backward * (self.swapmax * usdc_to_a2)
            if self.swapbackward < minswap_backward or a2_available < self.swapbackward: self.swapbackward = 0

    # Skip step counter function
    def skipper(self):

        # Increment Counter
        self.skip_step = self.skip_step + 1

        # Return True if Counter Complete
        if self.skip_step >= self.ndt:
            self.skip_step = 0
            return True

        # Return False if Skip Step
        return False

    # Update baseline information
    def set_baseline(self, a1toa2, a2toa1, fwd=False, bkwd=False):
        self.a1a2_baseline = a1toa2
        self.a2a1_baseline = a2toa1
        if fwd:
            if self.directionality < 0: self.directionality = 0
            else: self.directionality = self.directionality + 1
        if bkwd:
            if self.directionality > 0: self.directionality = 0
            else: self.directionality = self.directionality - 1

    # Simple Logistic Eqn Implementation
    def modified_logistic(self, x):
        if self.directionality != 0:

        else:
            
        return 1 / (1 + ((1 - self.beta) / self.beta)**((x - self.gamma)/(self.alpha - self.gamma)))

    # Simple Heaviside Implementation
    def heaviside(self, x):
        if x > self.alpha: return 1
        else: return 0
