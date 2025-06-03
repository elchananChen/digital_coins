import { FlatList, StyleSheet, Text } from 'react-native';
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Spinner } from '@/components/ui/spinner';
import { H2, H3 } from '@expo/html-elements';
import { Box } from '@/components/ui/box';
import { format } from 'date-fns';
import { TUsdSymbol, TUsdtSymbol } from '@/types/OrderBookTypes';
import { TExchange } from '@/shared/constants/exchanges';
import { fetchOrderBook } from '@/api/orderBookApi';

type OrderBookProps = {
  symbol: TUsdtSymbol | TUsdSymbol;
  queryKey: string;
  exchange: TExchange;
};
const OrderBook = ({ symbol, queryKey, exchange }: OrderBookProps) => {
  const {
    data: orderBook,
    isLoading,
    error,
  } = useQuery({
    queryKey: [queryKey, symbol],
    queryFn: () => fetchOrderBook(exchange.currency, symbol, exchange.name),
    enabled: !!symbol, // only if coinSymbol is provided
    refetchInterval: 1000, // refetch every second
  });

  if (isLoading) return <Spinner className="fill-black pt-96" />;

  if (error) {
    return (
      <Box>
        <Text> {`Error fetching order book: ${error || 'Please try again later.'}`}</Text>
      </Box>
    );
  }

  if (!orderBook) {
    return (
      <Box>
        <Text>No order book data available.</Text>
      </Box>
    );
  }

  const date = orderBook.timestamp;
  const time = format(date, 'HH:mm:ss');
  return (
    <Box className="w-40">
      <H2>{exchange.displayName}</H2>
      <Text className="w-1/2">updated at {time}</Text>
      <H3>Buy Orders</H3>
      <FlatList
        data={orderBook.bids}
        renderItem={({ item: bid }) => (
          <Box className="mt-2">
            <Text className="text-green-600">Price: {bid.price}</Text>
            <Text className="text-green-600">Amount: {bid.amount}</Text>
          </Box>
        )}
        keyExtractor={(pair) => pair.price.toString()}
        scrollEnabled={true}
        nestedScrollEnabled={true}
        style={styles.innerList}
      />
      <H3>Sell Orders</H3>
      <FlatList
        data={orderBook.asks}
        renderItem={({ item: ask }) => (
          <Box className="mt-2">
            <Text className="text-red-600">Price: {ask.price}</Text>
            <Text className="text-red-600">Amount: {ask.amount}</Text>
          </Box>
        )}
        keyExtractor={(pair) => pair.price.toString()}
        scrollEnabled={true}
        nestedScrollEnabled={true}
        style={styles.innerList}
      />
    </Box>
  );
};

export default OrderBook;
const styles = StyleSheet.create({
  innerList: {
    height: 300,
  },
});
