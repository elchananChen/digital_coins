import { NavigationProp, ParamListBase } from '@react-navigation/native';
import { TCoinInfo } from '@/shared/constants/coins';

export type Props = {
  navigation: TNavigation;
  route?: any;
};

export type TNavigation = NavigationProp<ParamListBase>;

export type TTheme = 'light' | 'dark';

export type TRootStackParamList = {
  platforms: undefined;
  coins: undefined;
  coinDetails: { coinInfo: TCoinInfo };
  coinbase: undefined;
  bitstamp: undefined;
  kraken: undefined;
  binance: undefined;
};
