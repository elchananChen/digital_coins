import { ScrollView } from 'react-native-gesture-handler';
import { H1 } from '@expo/html-elements';
import CoinBaseBookOrder from '@/components/CoinBaseBookOrder';
import { Text, TouchableOpacity } from 'react-native';
import { Props } from '@/types/NavigationTypes';

const CoinBase: React.FC<Props> = ({ navigation }) => {
  return (
    <ScrollView className="mb-20 py-20 ps-9">
      <H1>coin base:</H1>
      <CoinBaseBookOrder productId="BTC-USD" coinName="bitcoin"></CoinBaseBookOrder>
      <TouchableOpacity onPress={() => navigation.navigate('platforms')}>
        <Text>back</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

export default CoinBase;
