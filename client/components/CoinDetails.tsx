import { View, FlatList } from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';
import { TRootStackParamList } from '@/types/NavigationTypes';
import { H2 } from '@expo/html-elements';
import { EXCHANGES } from '@/shared/constants/exchanges';
import OrderBook from './OrderBook';
type CoinDetailsRouteProp = RouteProp<TRootStackParamList, 'coinDetails'>;

const CoinDetails = () => {
  const route = useRoute<CoinDetailsRouteProp>();
  const { coinInfo } = route.params;
  const exchanges = Object.values(EXCHANGES);

  return (
    <View>
      <H2 className="text-cyan-600">{coinInfo.name}</H2>
      <FlatList
        horizontal
        data={exchanges}
        keyExtractor={(exchange) => exchange.name}
        renderItem={(exchange) => (
          <OrderBook
            queryKey={exchange.item.name}
            symbol={exchange.item.currency === 'usd' ? coinInfo.usdSymbol : coinInfo.usdtSymbol}
            exchange={exchange.item}
          />
        )}
      />
    </View>
  );
};
export default CoinDetails;
