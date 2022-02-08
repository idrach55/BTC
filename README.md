## Research
- paper I wrote for a class at NYU designing a platform to sells equity swaps quanto'd into BTC  
- some examples of microstructure models using GDAX (now Coinbase Pro) tick data
- Glosten Milgrom model for using informed flow to imply fair value distribution <code>GlostenBig.ipynb</code>
- probability of informed trading estimtion <code>PINBig.ipynb</code>

## Deribit
- Bitcoin/Ethereum derivatives exchange https://www.deribit.com/
- futures trading and simple market making algo <code>strategy.py</code>
- fitting volatility surfaces and pricing/scenario analysis for a portfolio <code>vol.ipynb</code>
- alas Deribit has since banned US-domiciled users

## GDAX
- crypto cash exchange, now known as Coinbase Pro https://pro.coinbase.com/
- uses a websocket connection for live order/trade updates <code>book.py</code> and <code>blobprotocol.py</code>
- small attempt at finding triangular arbitrages (though the 20-30bps fees on the site make it uneconomical) <code>arber.py</code>
- older code base and the site's API changed a few years ago


