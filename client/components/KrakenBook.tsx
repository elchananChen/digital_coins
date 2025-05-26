import React from 'react';
import { Text } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { fetchKrakenBookOrder } from '@/api/krakenApi';
import { Spinner } from '@/components/ui/spinner';
import { ScrollView } from 'react-native-gesture-handler';
import { H2, H3 } from '@expo/html-elements';
import { Box } from '@/components/ui/box';
import { format } from 'date-fns';

type KrakenBookOrderProps = {
  pairSymbol: string;
  coinName: string;
};

const KrakenBookOrder = ({ coinName, pairSymbol }: KrakenBookOrderProps) => {
  const {
    data: orderBookData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['KrakenBookOrder', pairSymbol],
    queryFn: () => fetchKrakenBookOrder(pairSymbol),
    enabled: !!pairSymbol,
  });

  if (isLoading) return <Spinner className="fill-black pt-96" />;

  if (error) {
    return (
      <Box>
        <Text>{`Error fetching order book: ${error.message || 'Please try again later.'}`}</Text>
      </Box>
    );
  }

  if (!orderBookData) {
    return (
      <Box>
        <Text>No order book data available.</Text>
      </Box>
    );
  }

  const pairKey = Object.keys(orderBookData)[0];
  const { bids, asks } = orderBookData[pairKey];

  // const now = new Date();
  // const time = format(now, 'HH:mm:ss');

  return (
    <ScrollView>
      <Box className="mb-20 py-20 ps-9">
        <H2>Order Book for {coinName}</H2>
        {/* <H3>updated at {time}</H3> */}
        <H3>Buy Orders</H3>
        {bids.slice(0, 4).map((pair: any, index: number) => (
          <Box className="mt-5" key={index}>
            <Text className="text-green-600">Price: {pair[0]}</Text>
            <Text className="text-green-600">Amount: {pair[1]}</Text>
          </Box>
        ))}
        <H3>Sell Orders</H3>
        {asks.slice(0, 4).map((pair: any, index: number) => (
          <Box className="mt-5" key={index}>
            <Text className="text-red-600">Price: {pair[0]}</Text>
            <Text className="text-red-600">Amount: {pair[1]}</Text>
          </Box>
        ))}
      </Box>
    </ScrollView>
  );
};

export default KrakenBookOrder;
