import numpy as np

def round_trip(S0, S1, n, f=0.0025):
    return n*(S1*(1-f) - S0*(1+f))
