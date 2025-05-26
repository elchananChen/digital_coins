import React from 'react';
import { ScrollView } from 'react-native-gesture-handler';
import { H1 } from '@expo/html-elements';
import KrakenBookOrder from '@/components/KrakenBook';

export default function Kraken() {
  return (
    <ScrollView className="mb-20 py-20 ps-9">
      <H1>bitstamp</H1>
      <KrakenBookOrder pairSymbol="btcusd" coinName="Bitcoin"></KrakenBookOrder>
      <KrakenBookOrder pairSymbol="ethusd" coinName="Ethereum"></KrakenBookOrder>
    </ScrollView>
  );
}
