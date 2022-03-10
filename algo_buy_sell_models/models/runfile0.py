from azazello import azazello
aa = azazello(
    default_model = False,
    load_model = False
)
aa.add_tengu(0, 31566704, alpha=0.040, beta=0.060, gamma=1.000) # ALGO / USDC
aa.add_tengu(0, 226701642, alpha=0.020, beta=0.020, gamma=0.500) # ALGO / YLDY
aa.run()
