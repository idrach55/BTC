from control import Control
from cbe import Authorizer, CBEProtocol, read_keys

auth = Authorizer(read_keys("keys.txt"))
cbe = CBEProtocol(auth)
control = Control(cbe)

success, trade = control.trade(0.01, "buy")
print success, trade