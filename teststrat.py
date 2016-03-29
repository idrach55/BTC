'''
Author: Isaac Drachman
Date:   12/17/2015
Description:
'''

import sys

from strategy import Strategy
from multiprocessing import Process, Pipe

class TestStrat(Strategy):
	def __init__(self, keyfile, conn):
		Strategy.__init__(self, keyfile)
		self.conn = conn
		self.book()

	def update(self, book, msg):
		Strategy.update(self, book, msg)
		if self.conn.poll():
			command = self.conn.recv()
			self.conn.send("< " + command)

if __name__ == "__main__":
	parent, child = Pipe()
	p = Process(target=TestStrat, args=("keys.txt", child,))
	p.start()

	while True:
		command = raw_input("> ")
		parent.send(command)
		print parent.recv()