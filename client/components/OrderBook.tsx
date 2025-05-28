import { Text } from 'react-native';
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBookstampBookOrder } from '@/api/bitstampApi';
import { Spinner } from '@/components/ui/spinner';
import { ScrollView } from 'react-native-gesture-handler';
import { H1, H2, H3 } from '@expo/html-elements';
import { Box } from '@/components/ui/box';
import { format } from 'date-fns';
import { TOrderBookRes, TPriceAmount, TUsdSymbol, TUsdtSymbol } from '@/types/OrderBookTypes';

type OrderBookProps = {
  symbol: TUsdtSymbol | TUsdSymbol;
  coinName: string;
  queryKey: string;
  fetchOrderBook: (symbol: TUsdtSymbol | TUsdSymbol) => Promise<undefined | TOrderBookRes>;
};
const OrderBook = ({ coinName, symbol, fetchOrderBook, queryKey }: OrderBookProps) => {
  const {
    data: orderBook,
    isLoading,
    error,
  } = useQuery({
    queryKey: [queryKey, symbol],
    queryFn: () => fetchOrderBook(symbol),
    enabled: !!symbol, // only if coinSymbol is provided
    refetchInterval: 5000, // refetch every second
  });

  // console.log('orderBook', orderBook?.bids);

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
    <Box className="py-4 ps-9">
      <H2>{coinName}</H2>
      <H3>updated at {time}</H3>
      <H3>Buy Orders</H3>
      {orderBook.bids.slice(0, 4).map((pair: TPriceAmount, index: number) => (
        <Box className="mt-5" key={index}>
          <Text className="text-green-600">Price: {pair.price}</Text>
          <Text className="text-green-600">Amount: {pair.amount}</Text>
        </Box>
      ))}
      <H3>Sell Orders</H3>
      {orderBook.asks.slice(0, 4).map((pair: TPriceAmount, index: number) => (
        <Box className="mt-5" key={index}>
          <Text className="text-red-600">Price: {pair.price}</Text>
          <Text className="text-red-600">Amount: {pair.amount}</Text>
        </Box>
      ))}
    </Box>
  );
};

export default OrderBook;
