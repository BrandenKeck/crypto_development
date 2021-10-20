# Imported Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

class stochastic_oscillator():

    def __init__(self, n):
        self.n = n
        self.vals = []
        self.so = -1

    def increment(self, val):
        self.vals.append(val)
        if len(self.vals) > self.n:
            self.vals.pop(0)
            highest = max(self.vals)
            lowest = min(self.vals)
            self.so = (val-lowest)/(highest-lowest)

class roc():

    def __init__(self, n):
        self.idx = 0
        self.n = n
        self.vals = []
        self.roc = -1

    def increment(self, val):
        self.vals.append(val)
        if len(self.vals) > self.n:
            self.vals.pop(0)
            self.roc = (val - self.vals[0])/self.vals[0]

class rsi():

    def __init__(self):
        pass

    def increment(self, val):
        pass

# Import data
dat = pd.read_csv(r'gemini_eth-usd_data/ETH-USD_Master_Data.csv')

# Arrays for plotting
price = []

'''
emas = []
ema_arrs = []
for xx in [7200, 14400, 28800, 72000, 144000]:
    emas.append(ema(xx))
    ema_arrs.append([])
'''
so = stochastic_oscillator(60)
so_arr = []

# Loop
n = len(dat.index)
for i in np.arange(n):

    val = dat.iloc[i]["Close"]
    #for ema in emas: ema.increment(val)
    so.increment(val)

    price.append(val)
    #for ii in np.arange(len(ema_arrs)): ema_arrs[ii].append(emas[ii].ema)
    so_arr.append(so.so)

    if i%100000 == 0: print(i)

xx = np.arange(n)
#plt.plot(xx, price)
#for ema_arr in ema_arrs: plt.plot(xx, ema_arr)
fig, axs = plt.subplots(2)
axs[0].plot(xx, price)
axs[1].plot(xx, so_arr)
plt.show()
