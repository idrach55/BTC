var BitfinexWS = require ('bitfinex-api-node').WS;
var client = new BitfinexWS();

let pairs = ['BTCUSD', 'LTCUSD', 'LTCBTC', 'BFXUSD', 'BFXBTC', 'ETHUSD', 'ETHBTC'];

var books = {};
for (i = 0; i < pairs.length; i++) {
    books[pairs[i]] = {};
}

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

function getBidAskPrices(book) {
    let bidQuote = getBestQuote(book, 'bid');
    let askQuote = getBestQuote(book, 'ask');
    return {'bid': bidQuote['price'], 'ask': askQuote['price']};
}

function searchTriangleArbs(books) {
    var arbs = {};

    let btcusd = getBidAskPrices(books.BTCUSD);
    let inters = ['LTC', 'ETH', 'BFX'];
    for (i = 0; i < inters.length; i++) {
        let inter = inters[i];
        let interusd = getBidAskPrices(books[inter+'USD']);
        let interbtc = getBidAskPrices(books[inter+'BTC']);

        let cross_btcinter = (1/btcusd.ask)/interbtc.ask * interusd.bid;
        let cross_interbtc = (1/interusd.ask)*interbtc.bid * btcusd.bid;
        arbs['BTC'+inter] = cross_btcinter;
        arbs[inter+'BTC'] = cross_interbtc;
    }
    return arbs;
}

client.on('open', function () {
    for (i = 0; i < pairs.length; i++) {
        client.subscribeOrderBook(pairs[i]);
    }
});

var count = 0;
client.on('orderbook', function (pair, level) {
    //console.log('Order book:', level);
    // Alter the book for this pair off this update.
    count++;
    books[pair][level.price] = level.amount;
    if (count > 500) {
        console.log(searchTriangleArbs(books));
    }
});

client.on('subscribed', function (data) {
    console.log('New subscription', data);
});

client.on('error', console.error);
