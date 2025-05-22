import { createStackNavigator } from '@react-navigation/stack';
import { NavigationContainer } from '@react-navigation/native';
import React from 'react';

// 🚀 Lazy Load Screens (Except Settings, which loads instantly)

// 📌 Regular Imports (SettingsScreen Now Loads Instantly)
import LiveCoin from './LiveCoin';
import Bitstamp from './Bitstamp';
import CoinBase from './CoinBase';

const Stack = createStackNavigator();

// ✅ Main Stack Navigator
const StackNavigator = () => {
  return (
    <NavigationContainer>
      {/* 🏆 Settings Screens (Instant Load) */}
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          detachPreviousScreen: true,
        }}>
        <Stack.Screen name="coinbase" component={CoinBase} />
        <Stack.Screen name="bitstamp" component={Bitstamp} />
        <Stack.Screen name="liveCoin" component={LiveCoin} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default StackNavigator;
