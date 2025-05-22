const BASE_API_BITSTAMP_URL = 'http://172.20.10.2:3000/api/bitstamp';

export const fetchBitstampCurrencies = async () => {
  try {
    const response = await fetch(`${BASE_API_BITSTAMP_URL}/tickers/Currencies`);
    const data = await response.json();

    // console.log(data);
    // console.log('baba');

    if (!data || data.length === 0) {
      console.warn(`No data for coin list `);
      return [];
    }

    return data;
  } catch (error) {
    console.error('Error fetching :', error);
    throw error;
  }
};

export const fetchBookstampBookOrder = async (coinSymbol: string) => {
  try {
    const response = await fetch(`${BASE_API_BITSTAMP_URL}/book_order/${coinSymbol}`);
    const data = await response.json();

    if (!data || data.length === 0) {
      console.warn(`No data for bookstamp book order`);
      return [];
    }

    return data;
  } catch (error) {
    console.error('Error fetching :', error);
    throw error;
  }
};
