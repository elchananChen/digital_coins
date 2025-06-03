export const COINS = {
  BTC: {
    name: 'Bitcoin',
    usdSymbol: 'BTCUSD',
    usdtSymbol: 'BTCUSDT',
    icon: 'https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/32/btc.png',
  },
  ETH: {
    name: 'Ethereum',
    usdSymbol: 'ETHUSD',
    usdtSymbol: 'ETHUSDT',
    icon: 'https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/32/eth.png',
  },
  LTC: {
    name: 'Litecoin',
    usdSymbol: 'LTCUSD',
    usdtSymbol: 'LTCUSDT',
    icon: 'https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/32/ltc.png',
  },
  XRP: {
    name: 'Ripple',
    usdSymbol: 'XRPUSD',
    usdtSymbol: 'XRPUSDT',
    icon: 'https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/32/xrp.png',
  },
  BCH: {
    name: 'Bitcoin Cash',
    usdSymbol: 'BCHUSD',
    usdtSymbol: 'BCHUSDT',
    icon: 'https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/32/bch.png',
  },
} as const;

export type TCoinKey = keyof typeof COINS;
export type TCoinInfo = (typeof COINS)[TCoinKey];
export type TCoinName = TCoinInfo['name'];
export type TUsdSymbols = TCoinInfo['usdSymbol'];
export type TUsdtSymbols = TCoinInfo['usdtSymbol'];
export type TCoinIcons = TCoinInfo['icon'];
