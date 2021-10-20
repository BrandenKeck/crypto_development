# Imported Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Change tp parent directory and import the buyer / seller
import sys
sys.path.append("..")
from eth_buy_sell import eth_buyer_seller

# Sim class
class grendel():

    # Sim class init
    def __init__(self, acd=60, ocd=5, rcd=10,                   # WAIT TIMES
                    meth=0.01, musdc=15,                        # MINIMUM BALANCES
                    btx0=0.20, stx0=0.10, bth=0.3, sth=0.05,   # BUYING / SELLING RULES...
                    bfact=50, sfact=50):                        # SCALING TX SIZE

        # Simulation Parameters
        self.action_cooldown = acd          # Wait time after a transaction (minutes)
        self.observe_cooldown = ocd         # Wait time between transaction attempts (minutes)
        self.reporting_cooldown = rcd       # Wait time between "reported datapoints" (minutes)
        self.min_eth_balance = meth         # Minimum ETH Balance in Account (ETH)
        self.min_usdc_balance = musdc       # Minimum USDC Balance in Account (USDC)
        self.min_buy_size = btx0            # Minimum buy size (ETH)
        self.min_sell_size = stx0           # Minimum sell size (ETH)
        self.buy_percent_threshold = bth    # Percent decrease before buying (% ETH-USD Change)
        self.sell_percent_threshold = sth   # Percent increase before selling (% ETH-USD Change)
        self.buy_scaling_factor = bfact     # Increase in buy size per decrease in percent value (ETH / %)
        self.sell_scaling_factor = sfact    # Increase in buy size per decrease in percent value (ETH / %)

        # Use a basic buy / sell model starting at 1 ETH and 50 gwei average fee
        self.buyer_seller = eth_buyer_seller(eth0=10, verbose=False)
        self.price_point = self.buyer_seller.current_price

    # Simulation Function -- Loop over the dataset based on input parameters
    def run(self):

        # Simulation Loop
        while(not self.buyer_seller.is_eof):

            # Wait Action Cooldown
            ticker = 0
            while(ticker < self.action_cooldown):

                # Increment Time
                ticker = ticker + 1
                self.buyer_seller.act(0)


            # Observe prices until next action
            observe = True
            while(observe):

                # Main Logic - Decide to Buy or Sell
                observe = self.calculate_move()

                # If no action, Wait Observe Cooldown
                if(observe and not self.buyer_seller.is_eof):

                    # Wait observe cooldown
                    ticker = 0
                    while(ticker < self.observe_cooldown):

                        # Break on EOF
                        if self.buyer_seller.is_eof: return

                        # Increment Time
                        ticker = ticker + 1
                        self.buyer_seller.act(0)

                # Else, Exit Observe Logic
                else: observe = False

        plt.plot(np.arange(len(self.buyer_seller.total_balance)), self.buyer_seller.total_balance)
        plt.plot(np.arange(len(self.buyer_seller.eth_price)), self.buyer_seller.eth_price)
        plt.plot(self.buyer_seller.buy_times, np.ones(len(self.buyer_seller.buy_times)), 'go')
        plt.plot(self.buyer_seller.sell_times, np.ones(len(self.buyer_seller.sell_times)), 'yo')
        plt.plot(self.buyer_seller.failure_times, np.ones(len(self.buyer_seller.failure_times)), 'rx')
        plt.show()
        input()

    # Main Logic - Decide to Buy or Sell
    def calculate_move(self):

        # Init Flags
        buy = False
        sell = False

        # Calculate Percent Change
        percent_change = (self.buyer_seller.current_price - self.price_point)/self.price_point
        if(percent_change < -self.buy_percent_threshold): buy = True
        if(percent_change > self.sell_percent_threshold): sell = True
        #print({"pp": self.price_point, "cp": self.buyer_seller.current_price, "pc": percent_change})

        # If no action, return
        if(not buy and not sell): return True

        # BUY logic
        elif(buy):
            amt = self.min_buy_size + self.buy_scaling_factor * ((-percent_change) - self.buy_percent_threshold)
            self.buyer_seller.act(1, amt)
            if not self.buyer_seller.failure:
                self.price_point = self.buyer_seller.current_price

        # SELL logic
        elif(sell):
            amt = self.min_sell_size + self.sell_scaling_factor * (percent_change - self.sell_percent_threshold)
            self.buyer_seller.act(-1, amt)
            if not self.buyer_seller.failure:
                self.price_point = self.buyer_seller.current_price

        return False

# Call the simulation
model = grendel()
model.run()
