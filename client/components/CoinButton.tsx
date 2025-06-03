import React from 'react';
import { Button } from './ui/button';
import { TCoinInfo } from '@/shared/constants/coins';
import { Image } from './ui/image';
import { TRootStackParamList } from '@/types/NavigationTypes';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { Text } from './ui/text';

type CoinProps = {
  coinInfo: TCoinInfo;
};

type NavigationProp = StackNavigationProp<TRootStackParamList, 'coins'>;
const CoinButton = ({ coinInfo }: CoinProps) => {
  const navigation = useNavigation<NavigationProp>();

  return (
    <Button onPress={() => navigation.navigate('coinDetails', { coinInfo })}>
      <Text className="text-white">{coinInfo.name}</Text>
      <Image
        size="xs"
        alt={`${coinInfo.name} icon`}
        source={{
          uri:
            coinInfo.icon ||
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQmJCKBJkPzrQAL3DR2B62UoIxD7atqRa9yyA&s',
        }}
      />
    </Button>
  );
};

export default CoinButton;
