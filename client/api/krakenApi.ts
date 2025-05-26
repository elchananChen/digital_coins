const KRAKEN_BASE_URL = 'https://api.kraken.com/0/public';

export const fetchKrakenTicker = async (pair: string) => {
  try {
    const response = await fetch(`${KRAKEN_BASE_URL}/Ticker?pair=${pair}`);
    const data = await response.json();

    if (!data || !data.result || Object.keys(data.result).length === 0) {
      console.warn('No data for Kraken ticker');
      return null;
    }

    return data.result;
  } catch (error) {
    console.error('Error fetching Kraken ticker:', error);
    throw error;
  }
};

export const fetchKrakenBookOrder = async (pair: string, depth = 10) => {
  try {
    const response = await fetch(`${KRAKEN_BASE_URL}/Depth?pair=${pair}&count=${depth}`);
    const data = await response.json();

    if (!data || !data.result || Object.keys(data.result).length === 0) {
      console.warn('No data for Kraken order book');
      return null;
    }

    return data.result;
  } catch (error) {
    console.error('Error fetching Kraken book order:', error);
    throw error;
  }
};
