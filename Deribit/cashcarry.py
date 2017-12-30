import deribit_api as api
client = api.RestClient('4Caxv3HRkcku', 'ALTTSFCPEAJM5NLYOQW3IYDFMPFEBHPM')

# trade = (cash position, contracts, cash avg. price, futures avg. price)
trade = (-0.40, 249, 5752.01, 5495.14)
def profitloss():
    book = client.getorderbook('BTC-24NOV17')
    future = 0.5*(book['bids'][0]['price'] + book['asks'][0]['price'])
    spot   = client.index()['btc']

    futures_pnl = (future - trade[3])*trade[1]*10/future
    cash_pnl    = (spot - trade[2])*trade[0]
    return futures_pnl, cash_pnl

def live_pnl():
    while True:
        futures_pnl, cash_pnl = profitloss()
        print('futures=%0.2f; cash=%0.2f; total=%0.2f     '%(futures_pnl, cash_pnl, futures_pnl+cash_pnl),end='\r')
