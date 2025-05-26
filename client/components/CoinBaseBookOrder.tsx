import { Text } from 'react-native';
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchCoinBaseBookOrder } from '@/api/coinBaseApi';
import { Spinner } from '@/components/ui/spinner';
import { H2, H3 } from '@expo/html-elements';
import { Box } from '@/components/ui/box';

type CoinBaseBookOrderProps = {
  productId: string;
  coinName: string;
};

const CoinBaseBookOrder = ({ coinName, productId }: CoinBaseBookOrderProps) => {
  const {
    data: orderBook,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['CoinBaseBookOrder', productId],
    queryFn: () => fetchCoinBaseBookOrder(productId),
    enabled: !!productId, // only if coinSymbol is provided
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
  // const isoTime = "2025-05-22T14:13:10.683276Z";
  const date = new Date(orderBook.time);
  const timeStr = date.toTimeString().split(' ')[0];

  return (
    <Box className="mb-20 py-20 ps-9">
      <H2>Order Book for {coinName}</H2>
      <H3>updated at {timeStr}</H3>
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

export default CoinBaseBookOrder;
