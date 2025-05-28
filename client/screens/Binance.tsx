import React from 'react';
import { ScrollView } from 'react-native-gesture-handler';
import { H1 } from '@expo/html-elements';
import OrderBook from '@/components/OrderBook';
import { fetchBinanceOrderBook } from '@/api/binanceApi';

export default function Binance() {
  return (
    <ScrollView className="mb-20 py-20 ps-9">
      <H1>Order Book binance </H1>
      <OrderBook
        coinName="Bitcoin"
        symbol="BTCUSDT"
        fetchOrderBook={fetchBinanceOrderBook}
        queryKey="binanceOrderBook"
      />
      <OrderBook
        coinName="Ethereum"
        symbol="ETHUSDT"
        fetchOrderBook={fetchBinanceOrderBook}
        queryKey="binanceOrderBook"
      />
    </ScrollView>
  );
}
