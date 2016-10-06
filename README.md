# BTCX
Bitcoin (coinbase) algorithmic trading API

# Usage info
Using python3, run the file `testbook.py` to view live top-of-book sizes and prices. Might be a bit finicky since it downloads the current book via REST and then is fed websocket messages. Leaves a potential gap in which the book becomes confused.
