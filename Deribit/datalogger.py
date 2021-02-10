import asyncio
import websockets
import json
import pandas as pd

# To subscribe to this channel:
msg = {
'jsonrpc': '2.0',
'method': 'public/subscribe',
'id': 42,
'params': {'channels': ['trades.BTC-25SEP20.raw']}
}

async def call_api(msg):
    data = pd.DataFrame()
    tick_count = 0
    async with websockets.connect('wss://www.deribit.com/ws/api/v2') as websocket:
        await websocket.send(msg)
        while websocket.open:
            response = await websocket.recv()
            response = json.loads(response)
            if response.get('params') is None:
                continue
            trade_data = response['params']['data'][0]
            print('TRADE: %s %d @ %0.2f'%(trade_data['direction'], trade_data['amount'], trade_data['price']),end='\r')

            data = data.append(pd.Series(trade_data),ignore_index=True)
            tick_count += 1
            if tick_count == 50:
                data.to_csv('BTC-25SEP20.csv')
                tick_count = 0

asyncio.get_event_loop().run_until_complete(call_api(json.dumps(msg)))
