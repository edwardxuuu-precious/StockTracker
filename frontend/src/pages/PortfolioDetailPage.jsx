import { useCallback, useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, DollarSign, Briefcase, Calendar, Edit, RefreshCw } from 'lucide-react';
import * as portfolioAPI from '../services/portfolioAPI';
import { executeTrade, getTrades } from '../services/holdingAPI';
import { getBatchQuotes } from '../services/quoteAPI';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';

const INITIAL_TRADE_FORM = {
  symbol: '',
  action: 'BUY',
  quantity: '',
  price: '',
  commission: '0',
};

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : NaN;
}

function formatDateTime(value) {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '--';
  return date.toLocaleString('zh-CN');
}

function getQuoteRefreshErrorMessage(error) {
  const raw = getErrorMessage(error, '').trim();
  const lower = raw.toLowerCase();

  // Map backend/provider details to user-facing action-oriented messages.
  if (
    lower.includes('empty history') ||
    lower.includes('no available quote provider') ||
    lower.includes('request failed') ||
    lower.includes('connection') ||
    lower.includes('timeout')
  ) {
    return '实时报价暂时不可用，已保留当前价格。请稍后重试。';
  }

  if (lower.includes('429') || lower.includes('rate limit')) {
    return '报价源请求过于频繁，已保留当前价格。请稍后再试。';
  }

  return raw || '刷新报价失败，已保留当前价格。';
}

export default function PortfolioDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [portfolio, setPortfolio] = useState(null);
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [trading, setTrading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [notice, setNotice] = useState({ type: '', message: '' });
  const [tradeForm, setTradeForm] = useState(INITIAL_TRADE_FORM);
  const [tradeErrors, setTradeErrors] = useState({});
  const [liveQuotes, setLiveQuotes] = useState({});
  const [quoteRefreshState, setQuoteRefreshState] = useState({
    loading: false,
    lastRefreshedAt: null,
    error: '',
  });

  const loadData = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
        setError(null);
      }
      const [portfolioData, tradeData] = await Promise.all([
        portfolioAPI.getPortfolio(id),
        getTrades(id, 20),
      ]);
      setPortfolio(portfolioData);
      setTrades(tradeData);
      setLiveQuotes((previous) => {
        const next = {};
        (portfolioData.holdings || []).forEach((holding) => {
          const symbol = String(holding.symbol || '').toUpperCase();
          if (previous[symbol]) {
            next[symbol] = previous[symbol];
          }
        });
        return next;
      });
    } catch (err) {
      if (showLoading) setError(getErrorMessage(err, '加载组合失败'));
      else {
        setNotice({ type: 'error', message: getErrorMessage(err, '刷新交易数据失败') });
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  const validateTradeForm = () => {
    const errors = {};
    const symbol = String(tradeForm.symbol || '').trim().toUpperCase();
    const quantity = toNumber(tradeForm.quantity);
    const price = toNumber(tradeForm.price);
    const commission = tradeForm.commission === '' ? 0 : toNumber(tradeForm.commission);

    if (!symbol) errors.symbol = '请输入股票代码';
    if (!Number.isFinite(quantity) || quantity <= 0) errors.quantity = '数量必须大于 0';
    if (!Number.isFinite(price) || price <= 0) errors.price = '价格必须大于 0';
    if (!Number.isFinite(commission) || commission < 0) errors.commission = '手续费不能小于 0';

    return { errors, normalized: { symbol, quantity, price, commission } };
  };

  const handleDelete = async () => {
    try {
      setDeleting(true);
      setNotice({ type: '', message: '' });
      await portfolioAPI.deletePortfolio(id);
      navigate('/portfolios');
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err, '删除组合失败') });
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleTradeSubmit = async (event) => {
    event.preventDefault();
    const { errors, normalized } = validateTradeForm();
    setTradeErrors(errors);
    if (Object.keys(errors).length > 0) return;

    try {
      setTrading(true);
      setNotice({ type: '', message: '' });
      await executeTrade(id, {
        symbol: normalized.symbol,
        action: tradeForm.action,
        quantity: normalized.quantity,
        price: normalized.price,
        commission: normalized.commission,
      });
      setTradeForm((prev) => ({
        ...INITIAL_TRADE_FORM,
        symbol: prev.symbol.trim().toUpperCase(),
      }));
      await loadData(false);
      setNotice({
        type: 'success',
        message: `${tradeForm.action === 'BUY' ? '买入' : '卖出'}交易已执行。`,
      });
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err, '交易执行失败') });
    } finally {
      setTrading(false);
    }
  };

  const handleRefreshQuotes = useCallback(async () => {
    if (!portfolio?.holdings?.length) return;
    const symbols = Array.from(new Set(
      portfolio.holdings
        .map((holding) => String(holding.symbol || '').trim().toUpperCase())
        .filter(Boolean)
    ));
    if (symbols.length === 0) return;

    try {
      setQuoteRefreshState((previous) => ({ ...previous, loading: true, error: '' }));
      const quoteList = await getBatchQuotes(symbols, { refresh: true });
      const nextQuotes = {};
      quoteList.forEach((quote) => {
        const symbol = String(quote.symbol || '').toUpperCase();
        if (symbol) nextQuotes[symbol] = quote;
      });
      setLiveQuotes((previous) => ({ ...previous, ...nextQuotes }));

      const missingSymbols = symbols.filter((symbol) => !nextQuotes[symbol]);
      setQuoteRefreshState({
        loading: false,
        lastRefreshedAt: new Date().toISOString(),
        error: missingSymbols.length > 0
          ? `部分报价刷新失败（${missingSymbols.join(', ')}），已保留原有价格。`
          : '',
      });
    } catch (err) {
      setQuoteRefreshState((previous) => ({
        ...previous,
        loading: false,
        error: getQuoteRefreshErrorMessage(err),
      }));
    }
  }, [portfolio]);

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg inline-block">
          <p className="font-semibold">加载失败</p>
          <p className="text-sm">{error}</p>
        </div>
        <div className="mt-4">
          <Link to="/portfolios" className="text-blue-600 hover:text-blue-700">
            返回组合列表
          </Link>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">组合不存在</p>
        <Link to="/portfolios" className="text-blue-600 hover:text-blue-700 mt-4 inline-block">
          返回组合列表
        </Link>
      </div>
    );
  }

  const displayHoldings = (portfolio.holdings || []).map((holding) => {
    const symbol = String(holding.symbol || '').toUpperCase();
    const quote = liveQuotes[symbol];
    if (!quote) return holding;

    const nextPrice = Number(quote.price);
    if (!Number.isFinite(nextPrice) || nextPrice <= 0) return holding;

    const marketValue = holding.quantity * nextPrice;
    const unrealizedPnL = (nextPrice - holding.average_cost) * holding.quantity;
    return {
      ...holding,
      current_price: nextPrice,
      market_value: marketValue,
      unrealized_pnl: unrealizedPnL,
    };
  });

  const totalHoldingsValue = displayHoldings.reduce((sum, holding) => sum + holding.market_value, 0);
  const currentValue = totalHoldingsValue + portfolio.cash_balance;
  const totalReturn = currentValue - portfolio.initial_capital;
  const returnPercentage = (totalReturn / portfolio.initial_capital) * 100;
  const isPositiveReturn = totalReturn >= 0;

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={showDeleteConfirm}
        title="删除投资组合"
        message="确定要删除这个组合吗？此操作无法撤销。"
        confirmText="确认删除"
        cancelText="取消"
        confirmVariant="danger"
        processing={deleting}
        onCancel={() => {
          if (!deleting) setShowDeleteConfirm(false);
        }}
        onConfirm={handleDelete}
      />

      <NoticeBanner
        type={notice.type || 'error'}
        message={notice.message}
        onClose={() => setNotice({ type: '', message: '' })}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/portfolios" className="text-gray-600 hover:text-gray-900 transition-colors">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{portfolio.name}</h1>
            {portfolio.description ? <p className="text-gray-600 mt-1">{portfolio.description}</p> : null}
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to={`/portfolios/${id}/edit`}
            className="px-4 py-2 text-blue-600 hover:text-blue-700 border border-blue-600 hover:border-blue-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <Edit className="h-4 w-4" />
            编辑组合
          </Link>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="px-4 py-2 text-red-600 hover:text-red-700 border border-red-600 hover:border-red-700 rounded-lg transition-colors"
          >
            删除组合
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">当前总值</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${currentValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <DollarSign className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">总收益</p>
              <p className={`text-2xl font-bold mt-1 ${isPositiveReturn ? 'text-green-600' : 'text-red-600'}`}>
                ${totalReturn.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <p className={`text-sm mt-1 ${isPositiveReturn ? 'text-green-600' : 'text-red-600'}`}>
                {returnPercentage >= 0 ? '+' : ''}{returnPercentage.toFixed(2)}%
              </p>
            </div>
            <div className={`p-3 rounded-lg ${isPositiveReturn ? 'bg-green-100' : 'bg-red-100'}`}>
              {isPositiveReturn ? (
                <TrendingUp className="h-6 w-6 text-green-600" />
              ) : (
                <TrendingDown className="h-6 w-6 text-red-600" />
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">初始资金</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${portfolio.initial_capital.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <Briefcase className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">现金余额</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${portfolio.cash_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <DollarSign className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">交易执行</h2>
        <form onSubmit={handleTradeSubmit} className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">方向</label>
            <select
              value={tradeForm.action}
              onChange={(event) => setTradeForm((prev) => ({ ...prev, action: event.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="BUY">买入</option>
              <option value="SELL">卖出</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">股票代码</label>
            <input
              type="text"
              value={tradeForm.symbol}
              onChange={(event) => {
                setTradeForm((prev) => ({ ...prev, symbol: event.target.value }));
                setTradeErrors((prev) => ({ ...prev, symbol: '' }));
              }}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                tradeErrors.symbol ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {tradeErrors.symbol ? <p className="mt-1 text-xs text-red-600">{tradeErrors.symbol}</p> : null}
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">数量</label>
            <input
              type="text"
              inputMode="decimal"
              value={tradeForm.quantity}
              onChange={(event) => {
                setTradeForm((prev) => ({ ...prev, quantity: event.target.value }));
                setTradeErrors((prev) => ({ ...prev, quantity: '' }));
              }}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                tradeErrors.quantity ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {tradeErrors.quantity ? <p className="mt-1 text-xs text-red-600">{tradeErrors.quantity}</p> : null}
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">成交价</label>
            <input
              type="text"
              inputMode="decimal"
              value={tradeForm.price}
              onChange={(event) => {
                setTradeForm((prev) => ({ ...prev, price: event.target.value }));
                setTradeErrors((prev) => ({ ...prev, price: '' }));
              }}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                tradeErrors.price ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {tradeErrors.price ? <p className="mt-1 text-xs text-red-600">{tradeErrors.price}</p> : null}
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">手续费</label>
            <input
              type="text"
              inputMode="decimal"
              value={tradeForm.commission}
              onChange={(event) => {
                setTradeForm((prev) => ({ ...prev, commission: event.target.value }));
                setTradeErrors((prev) => ({ ...prev, commission: '' }));
              }}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                tradeErrors.commission ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {tradeErrors.commission ? <p className="mt-1 text-xs text-red-600">{tradeErrors.commission}</p> : null}
          </div>
          <div className="md:col-span-5">
            <button
              type="submit"
              disabled={trading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {trading ? '执行中...' : '执行交易'}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">持仓明细</h2>
            {quoteRefreshState.lastRefreshedAt ? (
              <p className="text-xs text-gray-500 mt-1">
                上次刷新: {new Date(quoteRefreshState.lastRefreshedAt).toLocaleString('zh-CN')}
              </p>
            ) : null}
            {quoteRefreshState.error ? (
              <p className="text-xs text-red-600 mt-1">{quoteRefreshState.error}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={handleRefreshQuotes}
            disabled={quoteRefreshState.loading || displayHoldings.length === 0}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-blue-600 text-blue-600 hover:text-blue-700 hover:border-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 ${quoteRefreshState.loading ? 'animate-spin' : ''}`} />
            {quoteRefreshState.loading ? '刷新中...' : '刷新报价'}
          </button>
        </div>
        <div className="overflow-x-auto">
          {displayHoldings.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">股票代码</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">数量</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">平均成本</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">当前价格</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">市值</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">未实现盈亏</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">收益率</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayHoldings.map((holding) => {
                  const unrealizedPnL = holding.unrealized_pnl || 0;
                  const costBasis = holding.quantity * holding.average_cost;
                  const returnPct = costBasis > 0 ? (unrealizedPnL / costBasis) * 100 : 0;
                  const isPositive = unrealizedPnL >= 0;
                  const quoteMeta = liveQuotes[String(holding.symbol || '').toUpperCase()];

                  return (
                    <tr key={holding.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium text-gray-900">{holding.symbol}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-900">{holding.quantity}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-900">${holding.average_cost.toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-900">
                        <div>${holding.current_price.toFixed(2)}</div>
                        {quoteMeta ? (
                          <div className="text-[11px] text-gray-500">{quoteMeta.source}</div>
                        ) : null}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-900">
                        ${holding.market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-right font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {isPositive ? '+' : ''}${unrealizedPnL.toFixed(2)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-right font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-12 text-center text-gray-500">
              <Briefcase className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>暂无持仓</p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">最近交易</h2>
        </div>
        <div className="overflow-x-auto">
          {trades.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">方向</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">代码</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">数量</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">价格</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">手续费</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">成交额</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">已实现盈亏</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trades.map((trade) => {
                  const pnl = Number(trade.realized_pnl || 0);
                  return (
                    <tr key={trade.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {new Date(trade.trade_time).toLocaleString('zh-CN')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            trade.action === 'BUY'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-orange-100 text-orange-700'
                          }`}
                        >
                          {trade.action === 'BUY' ? '买入' : '卖出'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.symbol}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">{trade.quantity}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">${Number(trade.price).toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">${Number(trade.commission).toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">${Number(trade.amount).toFixed(2)}</td>
                      <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${
                        pnl > 0 ? 'text-green-600' : pnl < 0 ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {pnl > 0 ? '+' : ''}${pnl.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-10 text-sm text-gray-500 text-center">暂无交易记录</div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">组合信息</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">创建时间</p>
            <div className="flex items-center mt-1 text-gray-900">
              <Calendar className="h-4 w-4 mr-2 text-gray-400" />
              {formatDateTime(portfolio.created_at)}
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-600">最后更新</p>
            <div className="flex items-center mt-1 text-gray-900">
              <Calendar className="h-4 w-4 mr-2 text-gray-400" />
              {formatDateTime(portfolio.updated_at)}
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-600">持仓数量</p>
            <p className="text-lg font-medium text-gray-900 mt-1">
              {portfolio.holdings?.length || 0} 个股票
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">状态</p>
            <p className="mt-1">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                portfolio.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {portfolio.is_active ? '活跃' : '已关闭'}
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
