import { View, FlatList } from 'react-native';
import React from 'react';
import { COINS } from '@/shared/constants/coins';
import CoinButton from '@/components/CoinButton';

const coinArray = Object.values(COINS);

const Coins = () => {
  return (
    <View>
      <FlatList
        data={coinArray}
        renderItem={(coin) => <CoinButton coinInfo={coin.item} />}
        keyExtractor={(coin) => coin.name}
        ItemSeparatorComponent={() => <View className="h-5" />}
      />
    </View>
  );
};

export default Coins;
