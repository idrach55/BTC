from strategy import RESTProtocol, read_keys

import time
import requests
import matplotlib.pyplot as plt

plt.rcParams["axes.grid"] = True

tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
tableau20 = [(r/255., g/255., b/255.) for r,g,b in tableau20]

def get_mid():
	r = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/ticker')
	if r.status_code == 200:
		return float(r.json()['price'])

def mark_to_market(rest):
	success, usd, btc = rest.get_balances()
	return usd + btc * get_mid()

if __name__ == "__main__":
	rest = RESTProtocol(read_keys('keys.txt'), debug=True)
	initial_marking = mark_to_market(rest)

	pnls   = []
	stamps = []

	plt.ion()
	fig = plt.figure()
	while True:
		stamps.append(time.time())
		pnls.append(mark_to_market(rest) - initial_marking)
		plt.plot(stamps[-10:], pnls[-10:], c=tableau20[0], lw=2)
		#plt.ylim(-0.30, 1.00)
		plt.show()
		plt.pause(0.2)
