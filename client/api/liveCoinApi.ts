const BASE_API_LIVE_COIN_URL = process.env.BASE_API_LIVE_COIN_URL;

// const BASE_API_LIVE_COIN_URL = 'http://172.20.10.2:3000/api/live_coin';
export const fetchCoinList = async () => {
  try {
    const response = await fetch(`${BASE_API_LIVE_COIN_URL}/coins/list`, {
      method: 'post',

      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        currency: 'USD',
        sort: 'rank',
        order: 'ascending',
        offset: 0,
        limit: 10,
        meta: false,
      }),
    });

    const data = await response.json();

    console.log(data);

    if (!data || data.length === 0) {
      console.warn(`No data for coin list `);
      return [];
    }

    return data;
  } catch (error) {
    console.error('Error fetching  :', error);
    throw error;
  }
};
