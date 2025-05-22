import { ScrollView } from 'react-native-gesture-handler';
import { H1} from '@expo/html-elements';
import CoinBaseBookOrder from '@/components/CoinBaseBookOrder';


export default function CoinBase() {
  
  return (
    <ScrollView className="mb-20 py-20 ps-9">
        <H1>coin base:</H1>
      <CoinBaseBookOrder productId="BTC-USD" coinName="bitcoin"></CoinBaseBookOrder>
        
    </ScrollView>
  );
}
