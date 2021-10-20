# Imported Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sim class
class eth_buyer_seller():

    # Sim class init
    def __init__(self, eth0=1, xfgf=50, verbose=True, pint=100000,
                    datafile = r'../gemini_eth-usd_data/ETH-USD_Master_Data.csv'):

        # Simulation Data
        self.pint = pint
        self.verbose = verbose
        self.sim_data_idx = 0
        self.sim_data = pd.read_csv(datafile)

        # Init end of file triggers
        self.is_eof = False
        self.eof = len(self.sim_data.index)

        # This is a transfer-only simulation.
        # A basic account transfer fee (USDC/ETH) will be incorporated
        self.xfer_gas_fee = 4 * xfgf * 1e-09

        # Set ETH0 / USDC for t=0
        self.eth = eth0
        self.usdc = 0
        self.current_balance = self.get_total_assets()
        self.current_price = self.sim_data.iloc[self.sim_data_idx]["Close"]

        # Track Transactions and Balances
        self.txs = []
        self.buy_times = []
        self.sell_times = []
        self.failure_times = []
        self.acct_eth = [self.eth]
        self.acct_usdc = [self.usdc]
        self.failure = False

        # Other analysis can be added functionally
        self.emas = {}

        # Performance Metrics
        self.total_balance = [self.current_balance]
        self.eth_price = [self.current_price]
        self.eth_normalized_balance = [self.total_balance[0] / self.eth_price[0]]

        # Simulation begins with a transfer of eth0 to the account, then a transfer of 1/2 eth0 to USD
        #   This is meant to establish equal pools in a way that I would naturally enter the market
        #   This sets up an initial net loss from entry transactions
        self.eth = self.eth_account_transfer(eth0)/2
        self.usdc = self.trade_eth_to_usdc(self.eth)

    # Action catalyst function,
    # Scaled to a sigmoid
    def act(self, idx, amt=None):

        # Check EOF before taking an action
        if self.is_eof:
            print("ERROR: END OF FILE")
        else:
            if idx == 1:
                self.buy(amt)
            if idx == 0:
                self.hold()
            if idx == -1:
                self.sell(amt)

    # Dictates no action
    def hold(self):
        self.current_price = self.sim_data.iloc[self.sim_data_idx]["Close"]
        self.current_balance = self.get_total_assets()
        self.tick()

    # Enacts a BUY action
    def buy(self, amt):
        dollars = self.monitor_eth_to_usdc(amt)
        if dollars <= self.usdc:
            value = dollars
            eth_out = self.trade_usdc_to_eth(dollars)
            self.eth = self.eth + eth_out
            self.usdc = self.usdc - dollars
            self.buy_times.append(self.sim_data_idx)
            self.failure = False
        else:
            value = "BUY FAILURE"
            self.failure_times.append(self.sim_data_idx)
            self.failure = True

        # Advance timestep
        self.current_price = self.sim_data.iloc[self.sim_data_idx]["Close"]
        self.current_balance = self.get_total_assets()
        tx = {"timepoint": self.sim_data_idx, "action": "BUY", "trade_value": value, "acct_total": "$"+str(self.current_balance), "acct_usdc": self.usdc, "acct_eth": self.eth}
        if self.verbose: print(tx)
        self.txs.append(tx)
        self.tick()

    # Enacts a SELL action
    def sell(self, amt):
        if amt <= self.eth:
            value = amt
            usdc_out = self.trade_eth_to_usdc(amt)
            self.eth = self.eth - amt
            self.usdc = self.usdc + usdc_out
            self.sell_times.append(self.sim_data_idx)
            self.failure = False
        else:
            value = "SELL FAILURE"
            self.failure_times.append(self.sim_data_idx)
            self.failure = True

        # Advance timestep
        self.current_price = self.sim_data.iloc[self.sim_data_idx]["Close"]
        self.current_balance = self.get_total_assets()
        tx = {"timepoint": self.sim_data_idx, "action": "SELL", "trade_value": value, "acct_total": "$"+str(self.current_balance), "acct_usdc": self.usdc, "acct_eth": self.eth}
        if self.verbose: print(tx)
        self.txs.append(tx)
        self.tick()

    # Advance a timestep
    def tick(self):

        # Track Metrics
        balance = self.get_total_assets()
        self.acct_eth.append(self.eth)
        self.acct_usdc.append(self.usdc)
        self.total_balance.append(self.current_balance)
        self.eth_price.append(self.current_price)
        self.eth_normalized_balance.append(self.current_balance / self.current_price)

        # Decide to check balances
        if self.sim_data_idx%self.pint == 0:
            total = self.get_total_assets()
            tx = {"timepoint": self.sim_data_idx, "action": "CHECK FUNDS", "trade_value": "N/A", "acct_total": "$"+str(total), "acct_usdc": self.usdc, "acct_eth": self.eth}
            print(tx)
            self.txs.append(tx)

        # Advance Analytics
        for key in self.emas: self.emas[key].increment(self.sim_data.iloc[self.sim_data_idx]["Close"])

        # Advance Time
        self.sim_data_idx = self.sim_data_idx + 1
        if self.sim_data_idx >= self.eof - 1: self.is_eof = True

    # add EMA class to the analysis
    def add_ema(n):
        self.emas[str(n)] = ema(n)

    # Calculates total USD value off the account and current simulation timepoint
    def get_total_assets(self):
        total = self.eth * self.sim_data.iloc[self.sim_data_idx]["Close"]
        total = total + self.usdc
        return total

    # Calculate output USDC value after ETH --> USDC conversion fees
    def trade_eth_to_usdc(self, eth0):
        usdc = eth0 * self.sim_data.iloc[self.sim_data_idx]["Close"]
        usdc = usdc - self.monitor_eth_to_usdc(self.xfer_gas_fee)
        return usdc

    # Calculate output ETH value after USDC --> ETH conversion fees
    def trade_usdc_to_eth(self, usdc0):
        eth = usdc0 / self.sim_data.iloc[self.sim_data_idx]["Close"]
        eth = eth - self.xfer_gas_fee
        return eth

    # Calculate account value after transfer fees
    def eth_account_transfer(self, eth0):
        return eth0 - self.xfer_gas_fee

    # Convert ETH to USDC at the necessary timepoint
    # Conversion is only "monitored", there is no loss of fees
    def monitor_eth_to_usdc(self, eth0):
        return eth0 * self.sim_data.iloc[self.sim_data_idx]["Close"]

    # Convert USDC to ETH at the necessary timepoint
    # Conversion is only "monitored", there is no loss of fees
    def monitor_usdc_to_eth(self, usdc0):
        return usdc0 / self.sim_data.iloc[self.sim_data_idx]["Close"]


# EMA Class
class ema():

    # Init class
    def __init__(self, n):

        self.idx = 0
        self.n = n
        self.running_ave = 0
        self.values = []

    # Increment calculations
    def increment(self, val):

        if self.idx < self.n:
            self.running_ave = self.running_ave + (val - self.running_ave)/(self.idx+1)
            self.values.append(-1)
        elif self.idx == self.n:
            self.values.append(self.running_ave)
        else:
            self.values.append(val * (2/(self.n + 1)) + self.ema * (1 - (2/(self.n + 1))))

        self.idx = self.idx + 1
