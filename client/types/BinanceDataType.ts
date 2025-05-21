import { IconsProps } from '@/utils/constants/Icons';

export interface BinanceData {
  name: string;
  symbol: string;
  price: number | null;
  change: number | null;
  lineData: string;
  bgColor: string;
  history: string;
}

export interface LineData {
  time: string;
  price: number;
}

export interface History {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}
