const COIN_BASE_URL =  process.env.COIN_BASE_URL

export const fetchCoinBaseBookOrder = async (productId: string) => {
  try {
    const response = await fetch(`${COIN_BASE_URL}/products/${productId}/book`);
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

