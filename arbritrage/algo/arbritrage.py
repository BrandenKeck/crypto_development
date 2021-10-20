# Imports
import json, time, random
from algosdk.v2client import algod
from tinyman.v1.client import TinymanClient

class cyclic_swap:

    def __init__(self, slips=0.005):

        # Import APIs and SDKs
        self.api_key = self.load_api_key()
        self.algod_client = self.load_algod_client()
        self.tinyman = TinymanClient(self.algod_client, 350338509)

        # Set assets for the cyclic swap
        self.asset1 = None
        self.asset2 = None
        self.asset3 = None
        self.slips = slips

    # Execute a Cyclic Swap
    def execute(self, amount):
        try:
            amt_out1 = self.swap(amount, self.asset1, self.asset2, self.slips)
            amt_out2 = self.swap(amt_out1, self.asset2, self.asset3, self.slips)
            amt_out3 = self.swap(amt_out2, self.asset3, self.asset1, self.slips)
            net = amt_out3 - amount
            result = f'[NET: {net}] {amount} {self.asset1.name} --> {amt_out1} {self.asset2.name} --> {amt_out2} {self.asset3.name} --> {amt_out3} {self.asset1.name}'
        except:
            result = f'[Liquidity Failure] {self.asset1.name} / {self.asset2.name} / {self.asset3.name}'

        print(result)

    # Swap function wrapper
    def swap(self, amount, asset1, asset2, slips):
        amt_in = asset1(int(amount * 10**asset1.decimals))
        pool = self.tinyman.fetch_pool(asset1, asset2)
        quote = pool.fetch_fixed_input_swap_quote(amt_in, slippage=slips)
        amt_out = quote.amount_out_with_slippage
        return amt_out.decimal_amount

    # Set New Assets
    def set_assets(self, asset1, asset2, asset3):
        self.asset1 = self.tinyman.fetch_asset(asset1)
        self.asset2 = self.tinyman.fetch_asset(asset2)
        self.asset3 = self.tinyman.fetch_asset(asset3)

    # Get API Key from External File
    def load_api_key(self):
        f = open('keys.json',)
        keys = json.load(f)
        f.close()
        return keys['algod_token_2']

    # Load Algod Client
    def load_algod_client(self):
        algod_address = "https://mainnet-algorand.api.purestake.io/ps2"
        algod_token = self.api_key
        algod_headers = {"X-API-Key": self.api_key}
        algod_client = algod.AlgodClient(algod_token, algod_address, algod_headers)
        return algod_client

# Fetch assets / Asset IDs from algo explorer
print("\r")
assets = {
    "ALGO": 0,
    "USDC": 31566704,
    "USDt": 312769,
    "YLDY": 226701642,
    "GEMS": 230946361,
    "OPUL": 287867876,
    "PLANETS": 27165954,
    "SMILE": 300208676,
    "RIO": 2751733,
    "HDL": 137594422,
    "CHOICE": 297995609,
    "AWT": 233939122
}
swapper = cyclic_swap(slips = 0)
while True:
    ness = random.sample(list(assets), 3)
    swapper.set_assets(assets[ness[0]], assets[ness[1]], assets[ness[2]])
    swapper.execute(1000)
    time.sleep(20)
