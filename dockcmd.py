from trader import Trader

if __name__ == "__main__":
	trader = Trader()
	while True:
		command = raw_input("> ").split(" ")
		if command[0] == "buy" or command[0] == "sell" or command[0] == "b" or command[0] == "s":
			if command[0] == "b":   command[0] = "buy"
			elif command[0] == "s": command[0] = "sell"
			success, message = trader.trade(command[0], float(command[1]), float(command[2]))
			if not success:
				if message: print "[!] trade error: " + message
				else:       print "[!] trade error: other"
			else:           print "[t] trade sent"
		elif command[0] == "cancel" or command[0] == "c":
			if len(command) == 2:
				success = trader.cancel(command[1])
				if success: print "[i] trade cancelled"
				else:       print "[!] error cancelling trade"
			else:
				success = trader.cancel_all()
				if success: print "[i] all trades cancelled"
				else:       print "[!] error cancelling all trades"
		elif command[0] == "positions" or command[0] == "p":
			success, positions = trader.risky.get_positions()
			if success: print positions
		elif command[0] == "volume" or command[0] == "v": print trader.risky.get_volume()
		elif command[0] == "m2m":
			success, m2m = trader.risky.get_position_m2m()
			if success: print m2m
		elif command[0] == "help": print "[i] side price size"
