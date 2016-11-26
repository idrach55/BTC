var BitfinexWS = require ('bitfinex-api-node').WS;
var client = new BitfinexWS();

var books = {'BTCUSD': {}, 'LTCUSD': {}, 'LTCBTC': {}};

function getBestQuote(book, type) {
    var levels = Object.keys(book).sort();
    if (type == 'ask') levels.reverse();
    var quote = {};
    for (i = 0; i < levels.length; i++) {
        if (type == 'bid') {
            if (book[levels[i]] >= 0) quote = {'price': levels[i], 'size': book[levels[i]]};
            if (book[levels[i]] < 0) break;
        } else if (type == 'ask') {
            if (book[levels[i]] <= 0) quote = {'price': levels[i], 'size': book[levels[i]]};
            if (book[levels[i]] > 0) break;
        }
    }
    return quote;
}

client.on('open', function () {
    client.subscribeOrderBook('BTCUSD');
    client.subscribeOrderBook('LTCUSD');
    client.subscribeOrderBook('LTCBTC');
});

client.on('orderbook', function (pair, level) {
    //console.log('Order book:', level);
    books[pair][level['price']] = level['amount'];
    bestBid = getBestQuote(books[pair], 'bid');
    bestAsk = getBestQuote(books[pair], 'ask');
    console.log(pair+': '+bestBid['price']+' | '+bestAsk['price']);
});

client.on('subscribed', function (data) {
    console.log('New subscription', data);
});

client.on('error', console.error);

