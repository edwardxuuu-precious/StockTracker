import { useEffect } from 'react';
import usePortfolioStore from '../store/portfolioStore';
import * as portfolioAPI from '../services/portfolioAPI';
import { getErrorMessage } from '../utils/errorMessage';

export const usePortfolios = () => {
  const { portfolios, loading, error, setPortfolios, setLoading, setError } =
    usePortfolioStore();

  useEffect(() => {
    const fetchPortfolios = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await portfolioAPI.getPortfolios();
        setPortfolios(data);
      } catch (err) {
        setError(getErrorMessage(err, '获取投资组合列表失败'));
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolios();
  }, [setPortfolios, setLoading, setError]);

  return { portfolios, loading, error };
};

export const usePortfolio = (id) => {
  const { currentPortfolio, loading, error, setCurrentPortfolio, setLoading, setError } =
    usePortfolioStore();

  useEffect(() => {
    if (!id) return;

    const fetchPortfolio = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await portfolioAPI.getPortfolio(id);
        setCurrentPortfolio(data);
      } catch (err) {
        setError(getErrorMessage(err, '获取投资组合详情失败'));
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolio();
  }, [id, setCurrentPortfolio, setLoading, setError]);

  return { portfolio: currentPortfolio, loading, error };
};

export const useCreatePortfolio = () => {
  const { addPortfolio, setLoading, setError } = usePortfolioStore();

  const createPortfolio = async (portfolioData) => {
    setLoading(true);
    setError(null);
    try {
      const newPortfolio = await portfolioAPI.createPortfolio(portfolioData);
      addPortfolio(newPortfolio);
      return newPortfolio;
    } catch (err) {
      setError(getErrorMessage(err, '创建投资组合失败'));
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { createPortfolio };
};

export const useUpdatePortfolio = () => {
  const { updatePortfolio: updateStore, setLoading, setError } = usePortfolioStore();

  const updatePortfolio = async (id, portfolioData) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await portfolioAPI.updatePortfolio(id, portfolioData);
      updateStore(id, updated);
      return updated;
    } catch (err) {
      setError(getErrorMessage(err, '更新投资组合失败'));
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { updatePortfolio };
};

export const useDeletePortfolio = () => {
  const { removePortfolio, setLoading, setError } = usePortfolioStore();

  const deletePortfolio = async (id) => {
    setLoading(true);
    setError(null);
    try {
      await portfolioAPI.deletePortfolio(id);
      removePortfolio(id);
    } catch (err) {
      setError(getErrorMessage(err, '删除投资组合失败'));
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { deletePortfolio };
};
