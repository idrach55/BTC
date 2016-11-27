var BitfinexWS = require ('bitfinex-api-node').WS;
var client = new BitfinexWS();

let pairs = ['BTCUSD', 'BFXUSD', 'BFXBTC'];
/*
             'LTCUSD', 'LTCBTC',
             'ETHUSD', 'ETHBTC',
             'ETCUSD', 'ETCBTC',
             'RRTUSD', 'RRTBTC'];
*/

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

function checkTriangle(books, arbs, inter) {
    let btcusd = getBidAskPrices(books.BTCUSD);
    var interusd = getBidAskPrices(books[inter+'USD']);
    var interbtc = getBidAskPrices(books[inter+'BTC']);
    var cross_btcinter = (1/btcusd.ask)/interbtc.ask * interusd.bid;
    var cross_interbtc = (1/interusd.ask)*interbtc.bid * btcusd.bid;
    arbs['BTC'+inter] = cross_btcinter;
    arbs[inter+'BTC'] = cross_interbtc;
    return arbs;
}

function searchTriangleArbs(books) {
    var inter = 'BFX';
    var arbs = checkTriangle(books, {}, inter);
    /*
    inter = 'LTC';
    arbs = checkTriangle(books, arbs, inter);
    inter = 'ETH';
    arbs = checkTriangle(books, arbs, inter);
    inter = 'ETC';
    arbs = checkTriangle(books, arbs, inter);
    inter = 'RRT';
    arbs = checkTriangle(books, arbs, inter);
    */
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
    books[pair][level.price] = level.amount;

    count++;
    if (count > 500) {
        let arbs = searchTriangleArbs(books);
        let keys = Object.keys(arbs);
        for (i = 0; i < keys.length; i++) {
            if (arbs[keys[i]] > 1) console.log(keys[i],':',arbs[keys[i]]);
        }
    }
});

client.on('subscribed', function (data) {
    console.log('New subscription', data);
});

client.on('error', console.error);
