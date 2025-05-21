type TCoinsListBody = {
  currency: string; //any valid coin or fiat code
  sort: string; //	sorting parameter, rank, price, volume, code, name, age
  order: string; //	sorting order, ascending or descending
  offset: number; //offset of the list, default 0
  limit: number; //limit of the list, default 10, maximum 100
  meta: boolean; //to include full coin information or not
};
