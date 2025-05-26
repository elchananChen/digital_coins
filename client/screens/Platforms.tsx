import React from 'react';

// types
import { Props } from '@/types/NavigationTypes';

// components
import { Text, TouchableOpacity } from 'react-native';

// ui components
import { Box } from '@/components/ui/box';
import { Image } from '@/components/ui/image';

const Platforms: React.FC<Props> = ({ navigation }) => {
  return (
    <Box className="mb-20 py-20 ps-9">
      <TouchableOpacity onPress={() => navigation.navigate('coinbase')}>
        <Text>Coinbase</Text>
        <Image
          size="xs"
          source={{ uri: 'https://www.coinbase.com/assets/sw-cache/a_B4aDYo-G.png' }}
        />
      </TouchableOpacity>
      <TouchableOpacity onPress={() => navigation.navigate('bitstamp')}>
        <Text>bitstamp</Text>
        <Image
          size="xs"
          source={{
            uri: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQmJCKBJkPzrQAL3DR2B62UoIxD7atqRa9yyA&s',
          }}
        />
      </TouchableOpacity>
      <TouchableOpacity onPress={() => navigation.navigate('kraken')}>
        <Text>kraken</Text>
        <Image
          size="xs"
          source={{
            uri: 'https://static-00.iconduck.com/assets.00/kraken-icon-512x512-icmwhmh8.png',
          }}
        />
      </TouchableOpacity>
    </Box>
  );
};

export default Platforms;
