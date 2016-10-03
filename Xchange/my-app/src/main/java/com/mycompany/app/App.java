package com.mycompany.app;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import org.knowm.xchange.Exchange;
import org.knowm.xchange.ExchangeFactory;
import org.knowm.xchange.coinbase.CoinbaseExchange;
import org.knowm.xchange.coinbase.dto.marketdata.CoinbaseCurrency;
import org.knowm.xchange.coinbase.dto.marketdata.CoinbaseHistoricalSpotPrice;
import org.knowm.xchange.coinbase.dto.marketdata.CoinbaseMoney;
import org.knowm.xchange.coinbase.dto.marketdata.CoinbasePrice;
import org.knowm.xchange.coinbase.dto.marketdata.CoinbaseSpotPriceHistory;
import org.knowm.xchange.coinbase.service.polling.CoinbaseMarketDataService;
import org.knowm.xchange.currency.CurrencyPair;
import org.knowm.xchange.dto.marketdata.OrderBook;
import org.knowm.xchange.service.polling.marketdata.PollingMarketDataService;

public class App
{
    public static void main(String[] args) throws IOException {
        Exchange coinbaseExchange = ExchangeFactory.INSTANCE.createExchange(CoinbaseExchange.class.getName());
        PollingMarketDataService marketDataService = coinbaseExchange.getPollingMarketDataService();

        generic(marketDataService);
        //raw((CoinbaseMarketDataService) marketDataService);
    }

    private static void generic(PollingMarketDataService marketDataService) throws IOException {
        //OrderBook book = marketDataService.getOrderBook(CurrencyPair.BTC_USD, null);
        //System.out.println(book);

        CoinbasePrice sellPrice = marketDataService.getCoinbaseSellPrice();
        CoinbasePrice buyPrice = marketDataService.getCoinbaseBuyPrice();
        System.out.println(buyPrice + " | " + sellPrice);
    }
}
