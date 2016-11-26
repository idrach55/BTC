var BitfinexWS = require ('bitfinex-api-node').WS;
var client = new BitfinexWS();

client.on('open', function () {
    client.subscribeOrderBook('BTCUSD');
});

client.on('orderbook', function (pair, book) {
    console.log('Order book:', book);
});

client.on('subscribed', function (data) {
    console.log('New subscription', data);
});

client.on('error', console.error);
