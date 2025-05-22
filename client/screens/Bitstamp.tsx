import { View, Text } from 'react-native';
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBitstampCurrencies } from '@/api/bitstampApi';
import { Spinner } from '@/components/ui/spinner';
import { ScrollView } from 'react-native-gesture-handler';
import { H1, H2 } from '@expo/html-elements';
import { Box } from '@/components/ui/box';
import BitstampBookOrder from '@/components/BitstampBookOrder';

export default function Bitstamp() {
  const {
    data: currencies,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['bitstampCurrencies'],
    queryFn: fetchBitstampCurrencies,
  });

  // console.log('currencies in component:', currencies);

  if (isLoading) return <Spinner className="fill-black pt-96" />;

  if (error) {
    return (
      <Box>
        <Text>Error: {error.message || 'Something went wrong'}</Text>
      </Box>
    );
  }

  if (!currencies || currencies.length === 0) {
    return (
      <Box>
        <Text>No currencies available</Text>
      </Box>
    );
  }

  return (
    <ScrollView className="mb-20 py-20 ps-9">
      <H1>bitstamp</H1>
      <BitstampBookOrder coinSymbol="btcusd" coinName="bitcoin"></BitstampBookOrder>
      <H2>currencies</H2>
      {currencies.slice(0, 2).map((currency: any, index: number) => (
        <Box className="mt-5" key={index}>
          <Text>{currency.symbol}</Text>
          <Text>{currency.currency}</Text>
          <Text>{currency.name}</Text>
          <Text>{currency.decimals}</Text>
          <Text>{currency.available_supply}</Text>
        </Box>
      ))}
    </ScrollView>
  );
}
