import { Text } from 'react-native';
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBookstampBookOrder } from '@/api/bitstampApi';
import { Spinner } from '@/components/ui/spinner';
import { ScrollView } from 'react-native-gesture-handler';
import { H1, H2, H3 } from '@expo/html-elements';
import { Box } from '@/components/ui/box';
import { format } from 'date-fns';

type BitstampBookOrderProps = {
  coinSymbol: string;
  coinName: string;
};
const BitstampBookOrder = ({ coinName, coinSymbol }: BitstampBookOrderProps) => {
  const {
    data: orderBook,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['BookstampBookOrder', coinSymbol],
    queryFn: () => fetchBookstampBookOrder(coinSymbol),
    enabled: !!coinSymbol, // only if coinSymbol is provided
  });

  // console.log('currencies in component:', currencies);

  if (isLoading) return <Spinner className="fill-black pt-96" />;

  if (error) {
    return (
      <Box>
        <Text> {`Error fetching order book: ${error.message || 'Please try again later.'}`}</Text>
      </Box>
    );
  }

  if (!orderBook || orderBook.length === 0) {
    return (
      <Box>
        <Text>No order book data available.</Text>
      </Box>
    );
  }
  const date = new Date(orderBook.timestamp * 1000);

  const time = format(date, 'HH:mm:ss');
  return (
    <Box className="mb-20 py-20 ps-9">
      <H2>Order Book for {coinName}</H2>
      <H3>updated at {time}</H3>
      <H3>Buy Orders</H3>
      {orderBook.bids.slice(0, 4).map((pair: any, index: number) => (
        <Box className="mt-5" key={index}>
          <Text className="text-green-600">Price: {pair[0]}</Text>
          <Text className="text-green-600">Amount: {pair[1]}</Text>
        </Box>
      ))}
      <H3>Sell Orders</H3>
      {orderBook.asks.slice(0, 4).map((pair: any, index: number) => (
        <Box className="mt-5" key={index}>
          <Text className="text-red-600">Price: {pair[0]}</Text>
          <Text className="text-red-600">Amount: {pair[1]}</Text>
        </Box>
      ))}
    </Box>
  );
};

export default BitstampBookOrder;
