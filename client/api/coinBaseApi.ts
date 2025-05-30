const COIN_BASE_URL = process.env.COIN_BASE_URL;

export const fetchCoinBaseBookOrder = async (productId: string) => {
  try {
    // console.log(COIN_BASE_URL);
    const response = await fetch(`${COIN_BASE_URL}/products/${productId}/book`);
    const data = await response.json();
    // console.log(data);
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
