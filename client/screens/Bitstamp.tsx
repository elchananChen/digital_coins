import React from 'react';
import { ScrollView } from 'react-native-gesture-handler';
import { H1 } from '@expo/html-elements';
import BitstampBookOrder from '@/components/BitstampBookOrder';

export default function Bitstamp() {
  return (
    <ScrollView className="mb-20 py-20 ps-9">
      <H1>Order Book bitstamp </H1>
      <BitstampBookOrder coinSymbol="btcusd" coinName="Bitcoin"></BitstampBookOrder>
      <BitstampBookOrder coinSymbol="ethusd" coinName="Ethereum"></BitstampBookOrder>
    </ScrollView>
  );
}
