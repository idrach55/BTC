from trader import Trader
import sys

if __name__ == "__main__":
	trader = Trader()

	m2m0 = 0.0
	if len(sys.argv) == 2: m2m0 = float(sys.argv[1])
	else:
		success, m2m0 = trader.risky.get_position_m2m()
		while not success: success, m2m0 = trader.risky.get_position_m2m()

	while True:
		success, pnl = trader.risky.get_pnl(m2m0)
		if success:
			print "profit loss: %0.5f    \r" % pnl,
	 		sys.stdout.flush()