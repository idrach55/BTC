'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Base class for strategies.
'''

from protocol import Authorizer, CBEProtocol, read_keys
from book.book import Book
from control import Control
from risky import Risky

class Strategy:
	def __init__(self, keyfile):
		auth = Authorizer(read_keys(keyfile))
		self.cbe = CBEProtocol(auth)
		self.state = {"control": Control(self.cbe),
				 	  "risky":   Risky(self.cbe)}

	def create_book(self):
		Book(self.cbe, 5.0, (self, self.state))

	def update(self, book, state):
		pass