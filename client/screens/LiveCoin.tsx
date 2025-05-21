import { Text } from 'react-native';
import React from 'react';
import { fetchCoinList } from '@/api/liveCoinApi';
import { useQuery } from '@tanstack/react-query';
import { Spinner } from '@/components/ui/spinner';
import { Box } from '@/components/ui/box';
import { H1 } from '@expo/html-elements';
import { TCoin } from '@/types/LiveCoinTypes';
import { ScrollView } from 'react-native-gesture-handler';

export default function LiveCoin() {
  const {
    data: coinsList,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['coinsList'],
    queryFn: fetchCoinList,
  });

  console.log('Coins list in component:', coinsList);

  if (isLoading) return <Spinner />;

  if (error) {
    return (
      <Box>
        <Text>Error: {error.message || 'Something went wrong'}</Text>
      </Box>
    );
  }

  if (!coinsList || coinsList.length === 0) {
    return (
      <Box>
        <Text>No coins available</Text>
      </Box>
    );
  }

  return (
    <ScrollView className="mb-20 py-20 ps-9">
      <H1>live coin watch</H1>
      {coinsList.map((coin: TCoin, index: number) => (
        <Box className="mt-5" key={coin.code || index}>
          <Text>{coin.code}</Text>
          <Text>{coin.rate}</Text>
          <Text>{coin.volume}</Text>
          <Text>{coin.cap}</Text>
        </Box>
      ))}
    </ScrollView>
  );
}
