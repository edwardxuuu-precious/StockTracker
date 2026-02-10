import { create } from 'zustand';

const usePortfolioStore = create((set) => ({
  portfolios: [],
  currentPortfolio: null,
  loading: false,
  error: null,

  setPortfolios: (portfolios) => set({ portfolios }),

  setCurrentPortfolio: (portfolio) => set({ currentPortfolio: portfolio }),

  addPortfolio: (portfolio) =>
    set((state) => ({
      portfolios: [...state.portfolios, portfolio],
    })),

  updatePortfolio: (id, updates) =>
    set((state) => ({
      portfolios: state.portfolios.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
      currentPortfolio:
        state.currentPortfolio?.id === id
          ? { ...state.currentPortfolio, ...updates }
          : state.currentPortfolio,
    })),

  removePortfolio: (id) =>
    set((state) => ({
      portfolios: state.portfolios.filter((p) => p.id !== id),
      currentPortfolio: state.currentPortfolio?.id === id ? null : state.currentPortfolio,
    })),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),
}));

export default usePortfolioStore;
