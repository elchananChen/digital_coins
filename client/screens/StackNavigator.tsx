import { createStackNavigator } from '@react-navigation/stack';
import { NavigationContainer } from '@react-navigation/native';
import React from 'react';

// 🚀 Lazy Load Screens (Except Settings, which loads instantly)

// 📌 Regular Imports (SettingsScreen Now Loads Instantly)
import LiveCoin from './LiveCoin';

import Binance from './Binance';
import Bitstamp from './Bitstamp';
import Platforms from './Platforms';
import Kraken from './Kraken';
import Coins from './Coins';
import CoinDetails from '@/components/CoinDetails';
import { TRootStackParamList } from '@/types/NavigationTypes';
import { withLayout } from '@/utils/WithLayout';

const Stack = createStackNavigator<TRootStackParamList>();

// ✅ Main Stack Navigator
const StackNavigator = () => {
  return (
    <NavigationContainer>
      {/* 🏆 Settings Screens (Instant Load) */}
      <Stack.Navigator
        initialRouteName="coins"
        screenOptions={{
          headerShown: false,
          detachPreviousScreen: true,
        }}>
        <Stack.Screen name="platforms" component={withLayout(Platforms)} />
        <Stack.Screen name="coins" component={withLayout(Coins)} />
        <Stack.Screen name="coinDetails" component={withLayout(CoinDetails)} />
        <Stack.Screen name="bitstamp" component={withLayout(Bitstamp)} />
        <Stack.Screen name="kraken" component={withLayout(Kraken)} />
        <Stack.Screen name="binance" component={withLayout(Binance)} />

        {/* <Stack.Screen name="liveCoin" component={LiveCoin} /> */}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default StackNavigator;
