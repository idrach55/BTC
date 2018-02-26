import numpy as np
import scipy.stats as stats
import datetime
import pandas as pd
import scipy.optimize as opt
import pickle

########################

def save_surface(surface):
    file = open('surface-%s.obj'%datetime.datetime.today().strftime('%Y-%m-%d'),'wb')
    pickle.dump(surface, file)
def load_surface(date):
    return pickle.load(open('surface-%s.obj'%date,'rb'))

########################

def BSsetup(S, K, T, sigma, r, c):
    d1 = (np.log(S/K) + (r - c + sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return d1,d2

def BScall(S, K, T, sigma, r, c):
    if T <= 0.0:
        return max(S-K,0.0)
    d1, d2 = BSsetup(S, K, T, sigma, r, c)
    return stats.norm.cdf(d1)*S - stats.norm.cdf(d2)*K*np.exp(-r*T)

def BSput(S, K, T, sigma, r, c):
    if T <= 0.0:
        return max(S-K,0.0)
    d1, d2 = BSsetup(S, K, T, sigma, r, c)
    return stats.norm.cdf(-d2)*K*np.exp(-r*T) - stats.norm.cdf(-d1)*S

def BSvol(S, K, T, r, c, V, call=True):
    value = lambda sigma: BScall(S,K,T,sigma,r,c) if call else BSput(S,K,T,sigma,r,c)
    return opt.brentq(lambda sigma: value(sigma)-V, 0.01, 10.0)

########################

def convert_GMT_EST(date):
    return pd.to_datetime(date).tz_localize('GMT').tz_convert('EST')
def now_EST():
    return pd.to_datetime(datetime.datetime.today()).tz_localize('EST')

# Expiry and now in same timezone
def time_to_expiry(expiry, now):
    return (expiry - now).total_seconds()/3600/24/365

#def expiry_codes(d):
#    return d.strftime('%d')+d.strftime('%b').upper()+d.strftime('%y')

expiry_codes = {'2018-03-30 08:00:00 GMT': '30MAR18',
                '2018-03-02 08:00:00 GMT': '2MAR18',
                '2018-02-16 08:00:00 GMT': '16FEB18',
                '2018-06-29 08:00:00 GMT': '29JUN18'}

expiries = dict([(code, date) for date, code in expiry_codes.items()])

########################

# Surface functional form
Sigma_explicit = lambda lK,pATM,pSKEW,pVoV: pATM -pSKEW*lK + pVoV*lK**2
Sigma = lambda lK,surface: Sigma_explicit(lK,surface[0],surface[1],surface[2])

def PV(option, surface, overrides={}):
    #expiry = expiry_codes[option['expiration']]
    #S = overrides['spot']; K = option['strike']
    #is_call = option['instrumentName'][-1] == 'C'
    #T = time_to_expiry(convert_GMT_EST(option['expiration']), now_EST())

    expiry = option.split('-')[1]
    S = overrides['spot']; K = float(option.split('-')[2])
    is_call = option.split('-')[3] == 'C'
    T = time_to_expiry(convert_GMT_EST(expiries[expiry]), now_EST())

    sigma = Sigma(np.log(K/S), surface[expiry])
    func = BScall if is_call else BSput

    if overrides.get('vol') is not None:
        sigma = overrides['vol']
    if overrides.get('time') is not None:
        T = overrides('time')
    if overrides.get('vol_shift') is not None:
        sigma += overrides['vol_shift']
    if overrides.get('time_shift') is not None:
        T += overrides['time_shift']

    return func(S,K,T,sigma,0.0,0.0)

def delta(option, surface, overrides={}):
    S = overrides['spot']
    dS = 0.01
    overrides_H = overrides.copy(); overrides_H['spot'] = S*(1+dS/2)
    overrides_L = overrides.copy(); overrides_L['spot'] = S*(1-dS/2)
    pv_H = PV(option, surface, overrides_H,)
    pv_L = PV(option, surface, overrides_L)
    return (pv_H - pv_L)/dS

def gamma(option, surface, overrides={}):
    S = overrides['spot']
    dS = 0.01
    overrides_H = overrides.copy(); overrides_H['spot'] = S*(1+dS/2)
    overrides_L = overrides.copy(); overrides_L['spot'] = S*(1-dS/2)
    delta_H = delta(option, surface, overrides_H)
    delta_L = delta(option, surface, overrides_L)
    return (delta_H - delta_L)/(dS/0.01)

def vega(option, surface, overrides={}):
    dSigma = 0.01
    vol_shift = 0.0
    if overrides.get('vol_shift') is not None:
        vol_shift = overrides['vol_shift']
    overrides_H = overrides.copy(); overrides_H['vol_shift'] = vol_shift+dSigma
    overrides_L = overrides.copy(); overrides_L['vol_shift'] = vol_shift-dSigma
    pv_H = PV(option, surface, overrides_H)
    pv_L = PV(option, surface, overrides_L)
    return (pv_H - pv_L)/(dSigma/0.01)

def theta(option, surface, overrides={}):
    dT = 1/365
    time_shift = 0.0
    if overrides.get('time_shift') is not None:
        time_shift = overrides['time_shift']
    overrides_H = overrides.copy(); overrides_H['time_shift'] = time_shift-dT
    pv_H = PV(option, surface, overrides_H)
    pv_L = PV(option, surface, overrides)
    return pv_H - pv_L
