import { create } from 'zustand';

type DataState = {
  isDataLoaded: boolean;
  setDataLoaded: (loaded: boolean) => void;
  data: any;
  setData: (newData: any) => void;
};

export const useDataStore = create<DataState>((set) => ({
  isDataLoaded: false,
  setDataLoaded: (loaded) => set({ isDataLoaded: loaded }),
  data: null,
  setData: (newData) => set({ data: newData }),
}));
