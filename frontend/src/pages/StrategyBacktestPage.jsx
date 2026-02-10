import { useCallback, useEffect, useMemo, useState } from 'react';
import { BarChart3, PlayCircle, PlusCircle, RefreshCw, TrendingUp } from 'lucide-react';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';
import { createStrategy, getStrategies, updateStrategy } from '../services/strategyAPI';
import { getBacktest, getBacktests, runBacktest } from '../services/backtestAPI';

function todayDateString() {
  return new Date().toISOString().slice(0, 10);
}

function oneYearAgoDateString() {
  const date = new Date();
  date.setFullYear(date.getFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

function toNumber(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : NaN;
}

function fmtCurrency(value) {
  return Number(value || 0).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function fmtPercent(value) {
  const num = Number(value || 0);
  return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
}

const STRATEGY_FORM_DEFAULTS = {
  name: '',
  description: '',
  strategy_type: 'moving_average',
  short_window: '5',
  long_window: '20',
  rsi_period: '14',
  rsi_buy: '30',
  rsi_sell: '70',
  momentum_period: '10',
  momentum_threshold: '0.015',
};

function getStrategyHint(strategyType) {
  if (strategyType === 'rsi') {
    return 'RSI 低于买入阈值开仓，高于卖出阈值平仓。';
  }
  if (strategyType === 'momentum') {
    return '动量高于阈值开仓，低于负阈值平仓。';
  }
  return '短均线上穿长均线开仓，下穿平仓。';
}

function buildStrategyParametersByType(form) {
  const strategyType = form.strategy_type;
  if (strategyType === 'rsi') {
    return {
      rsi_period: Math.max(2, Math.floor(toNumber(form.rsi_period))),
      rsi_buy: toNumber(form.rsi_buy),
      rsi_sell: toNumber(form.rsi_sell),
    };
  }
  if (strategyType === 'momentum') {
    return {
      momentum_period: Math.max(2, Math.floor(toNumber(form.momentum_period))),
      momentum_threshold: toNumber(form.momentum_threshold),
    };
  }
  return {
    short_window: Math.max(2, Math.floor(toNumber(form.short_window))),
    long_window: Math.max(3, Math.floor(toNumber(form.long_window))),
  };
}

function makeStrategyFormFromRecord(strategy) {
  if (!strategy) return { ...STRATEGY_FORM_DEFAULTS };
  const params = strategy.parameters || {};
  return {
    ...STRATEGY_FORM_DEFAULTS,
    name: String(strategy.name || ''),
    description: String(strategy.description || ''),
    strategy_type: String(strategy.strategy_type || 'moving_average'),
    short_window: String(params.short_window ?? STRATEGY_FORM_DEFAULTS.short_window),
    long_window: String(params.long_window ?? STRATEGY_FORM_DEFAULTS.long_window),
    rsi_period: String(params.rsi_period ?? STRATEGY_FORM_DEFAULTS.rsi_period),
    rsi_buy: String(params.rsi_buy ?? STRATEGY_FORM_DEFAULTS.rsi_buy),
    rsi_sell: String(params.rsi_sell ?? STRATEGY_FORM_DEFAULTS.rsi_sell),
    momentum_period: String(params.momentum_period ?? STRATEGY_FORM_DEFAULTS.momentum_period),
    momentum_threshold: String(params.momentum_threshold ?? STRATEGY_FORM_DEFAULTS.momentum_threshold),
  };
}

function formatStrategyParameters(strategy) {
  if (!strategy) return '';
  const params = strategy.parameters || {};
  if (strategy.strategy_type === 'rsi') {
    return `RSI周期 ${params.rsi_period ?? '--'} / 买入 ${params.rsi_buy ?? '--'} / 卖出 ${params.rsi_sell ?? '--'}`;
  }
  if (strategy.strategy_type === 'momentum') {
    return `动量周期 ${params.momentum_period ?? '--'} / 阈值 ${params.momentum_threshold ?? '--'}`;
  }
  return `短均线 ${params.short_window ?? '--'} / 长均线 ${params.long_window ?? '--'}`;
}

function buildBacktestErrorMessage(rawMessage) {
  const message = String(rawMessage || '').trim();
  if (!message) {
    return '回测执行失败，请检查输入后重试。';
  }
  if (message.includes('start_date must be earlier than or equal to end_date')) {
    return [
      '日期范围不正确：开始日期不能晚于结束日期。',
      '请将【开始日期】调整为更早日期，或将【结束日期】调整为同一天或更晚日期。',
    ].join('\n');
  }
  return message;
}

function EquityCurveChart({ points }) {
  if (!points?.length || points.length < 2) {
    return <p className="text-sm text-gray-500">暂无收益曲线数据。</p>;
  }

  const width = 760;
  const height = 240;
  const pad = 24;
  const values = points.map((item) => Number(item.value || 0));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;

  const dots = points.map((item, idx) => {
    const x = pad + (idx / (points.length - 1)) * (width - pad * 2);
    const y = height - pad - ((Number(item.value || 0) - min) / span) * (height - pad * 2);
    return { x, y };
  });

  const path = dots.map((dot) => `${dot.x},${dot.y}`).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56 bg-slate-50 border border-slate-200 rounded-lg">
      <polyline fill="none" stroke="#2563eb" strokeWidth="3" points={path} />
      {dots.map((dot, idx) => (
        <circle key={`${dot.x}-${dot.y}-${idx}`} cx={dot.x} cy={dot.y} r="2.5" fill="#1d4ed8" />
      ))}
    </svg>
  );
}

export default function StrategyBacktestPage() {
  const [strategies, setStrategies] = useState([]);
  const [backtests, setBacktests] = useState([]);
  const [selectedBacktest, setSelectedBacktest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [creatingStrategy, setCreatingStrategy] = useState(false);
  const [savingManagedStrategy, setSavingManagedStrategy] = useState(false);
  const [runningBacktest, setRunningBacktest] = useState(false);
  const [notice, setNotice] = useState({ type: '', message: '' });
  const [runStateHint, setRunStateHint] = useState('');

  const [strategyForm, setStrategyForm] = useState({ ...STRATEGY_FORM_DEFAULTS });
  const [selectedManagedStrategyId, setSelectedManagedStrategyId] = useState('');
  const [managedStrategyForm, setManagedStrategyForm] = useState({ ...STRATEGY_FORM_DEFAULTS });

  const [backtestForm, setBacktestForm] = useState({
    strategy_id: '',
    symbols: 'AAPL,MSFT',
    start_date: oneYearAgoDateString(),
    end_date: todayDateString(),
    initial_capital: '100000',
    allocation_per_trade: '0.25',
    commission_rate: '0.001',
  });

  const loadOverview = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      else setRefreshing(true);
      const [strategyList, backtestList] = await Promise.all([
        getStrategies(100),
        getBacktests({ limit: 50 }),
      ]);
      setStrategies(strategyList);
      setBacktests(backtestList);
      setSelectedManagedStrategyId((previous) => {
        const keepCurrent = strategyList.some((item) => String(item.id) === String(previous));
        if (keepCurrent) return previous;
        return strategyList.length > 0 ? String(strategyList[0].id) : '';
      });

      const currentStrategyId = String(backtestForm.strategy_id || '');
      if (!currentStrategyId && strategyList.length > 0) {
        setBacktestForm((prev) => ({ ...prev, strategy_id: String(strategyList[0].id) }));
      }

      if (backtestList.length > 0) {
        const detail = await getBacktest(backtestList[0].id);
        setSelectedBacktest(detail);
      } else {
        setSelectedBacktest(null);
      }
      setRunStateHint('');
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '加载策略回测数据失败') });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [backtestForm.strategy_id]);

  useEffect(() => {
    loadOverview(true);
  }, [loadOverview]);

  const strategyHint = useMemo(() => getStrategyHint(strategyForm.strategy_type), [strategyForm.strategy_type]);

  const selectedManagedStrategy = useMemo(
    () => strategies.find((item) => String(item.id) === String(selectedManagedStrategyId)) || null,
    [strategies, selectedManagedStrategyId],
  );

  const runningStrategy = useMemo(
    () => strategies.find((item) => String(item.id) === String(backtestForm.strategy_id)) || null,
    [strategies, backtestForm.strategy_id],
  );

  useEffect(() => {
    if (!selectedManagedStrategy) {
      setManagedStrategyForm({ ...STRATEGY_FORM_DEFAULTS });
      return;
    }
    setManagedStrategyForm(makeStrategyFormFromRecord(selectedManagedStrategy));
  }, [selectedManagedStrategy]);

  const buildStrategyParameters = () => buildStrategyParametersByType(strategyForm);

  const handleCreateStrategy = async (event) => {
    event.preventDefault();
    const name = String(strategyForm.name || '').trim();
    if (!name) {
      setNotice({ type: 'error', message: '策略名称不能为空' });
      return;
    }

    try {
      setCreatingStrategy(true);
      const payload = {
        name,
        description: String(strategyForm.description || '').trim(),
        strategy_type: strategyForm.strategy_type,
        parameters: buildStrategyParameters(),
      };
      const created = await createStrategy(payload);
      const nextStrategies = [created, ...strategies];
      setStrategies(nextStrategies);
      setStrategyForm((prev) => ({ ...prev, name: '', description: '' }));
      setSelectedManagedStrategyId(String(created.id));
      setBacktestForm((prev) => ({ ...prev, strategy_id: String(created.id) }));
      setNotice({ type: 'success', message: `策略已创建: ${created.name}` });
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '创建策略失败') });
    } finally {
      setCreatingStrategy(false);
    }
  };

  const handleRunBacktest = async (event) => {
    event.preventDefault();
    const strategyId = Number(backtestForm.strategy_id);
    const initialCapital = toNumber(backtestForm.initial_capital);
    const allocation = toNumber(backtestForm.allocation_per_trade);
    const commissionRate = toNumber(backtestForm.commission_rate);
    const symbols = String(backtestForm.symbols || '')
      .split(',')
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean);

    if (!strategyId) {
      setNotice({ type: 'error', message: '请先选择策略' });
      return;
    }
    if (!symbols.length) {
      setNotice({ type: 'error', message: '请至少输入一个股票代码' });
      return;
    }
    if (!Number.isFinite(initialCapital) || initialCapital <= 0) {
      setNotice({ type: 'error', message: '初始资金必须大于 0' });
      return;
    }
    if (backtestForm.start_date && backtestForm.end_date && backtestForm.start_date > backtestForm.end_date) {
      setSelectedBacktest(null);
      setRunStateHint('当前显示的是历史回测任务列表，不代表本次提交结果。');
      setNotice({
        type: 'error',
        message: [
          '日期范围不正确：开始日期不能晚于结束日期。',
          '请将【开始日期】调整为更早日期，或将【结束日期】调整为同一天或更晚日期。',
        ].join('\n'),
      });
      return;
    }

    try {
      setRunningBacktest(true);
      const created = await runBacktest({
        strategy_id: strategyId,
        symbols,
        start_date: backtestForm.start_date,
        end_date: backtestForm.end_date,
        initial_capital: initialCapital,
        parameters: {
          allocation_per_trade: Number.isFinite(allocation) ? allocation : 0.25,
          commission_rate: Number.isFinite(commissionRate) ? commissionRate : 0.001,
        },
      });
      const [list, detail] = await Promise.all([
        getBacktests({ limit: 50 }),
        getBacktest(created.id),
      ]);
      setBacktests(list);
      setSelectedBacktest(detail);
      setRunStateHint('');
      setNotice({ type: 'success', message: `回测完成 (ID: ${created.id})` });
    } catch (error) {
      const rawMessage = getErrorMessage(error, '执行回测失败');
      setSelectedBacktest(null);
      setRunStateHint('当前显示的是历史回测任务列表，不代表本次提交结果。');
      setNotice({ type: 'error', message: buildBacktestErrorMessage(rawMessage) });
    } finally {
      setRunningBacktest(false);
    }
  };

  const handleSaveManagedStrategy = async (event) => {
    event.preventDefault();
    if (!selectedManagedStrategy) {
      setNotice({ type: 'error', message: '请先在策略列表中选择一个策略' });
      return;
    }

    const name = String(managedStrategyForm.name || '').trim();
    if (!name) {
      setNotice({ type: 'error', message: '策略名称不能为空' });
      return;
    }

    try {
      setSavingManagedStrategy(true);
      const payload = {
        name,
        description: String(managedStrategyForm.description || '').trim(),
        strategy_type: managedStrategyForm.strategy_type,
        parameters: buildStrategyParametersByType(managedStrategyForm),
      };
      const updated = await updateStrategy(Number(selectedManagedStrategy.id), payload);
      setStrategies((previous) =>
        previous.map((item) => (item.id === updated.id ? updated : item))
      );
      setNotice({ type: 'success', message: `策略已保存: ${updated.name}` });
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '保存策略失败') });
    } finally {
      setSavingManagedStrategy(false);
    }
  };

  const handleSelectBacktest = async (backtestId) => {
    try {
      const detail = await getBacktest(backtestId);
      setSelectedBacktest(detail);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '加载回测详情失败') });
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <NoticeBanner
        type={notice.type || 'info'}
        message={notice.message}
        onClose={() => setNotice({ type: '', message: '' })}
      />

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">策略回测</h1>
          <p className="text-gray-600 mt-1">创建参数化策略，执行回测并持久化查询结果。</p>
        </div>
        <button
          type="button"
          onClick={() => loadOverview(false)}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:border-blue-700 hover:text-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? '刷新中...' : '刷新列表'}
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center gap-2 mb-4">
            <PlusCircle className="h-4 w-4 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">创建策略</h2>
          </div>
          <form className="space-y-3" onSubmit={handleCreateStrategy}>
            <div>
              <label className="block text-xs text-gray-600 mb-1">策略名称</label>
              <input
                value={strategyForm.name}
                onChange={(event) => setStrategyForm((prev) => ({ ...prev, name: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="例如: MA Crossover"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">策略类型</label>
              <select
                value={strategyForm.strategy_type}
                onChange={(event) => setStrategyForm((prev) => ({ ...prev, strategy_type: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
              >
                <option value="moving_average">均线策略</option>
                <option value="rsi">RSI 策略</option>
                <option value="momentum">动量策略</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">{strategyHint}</p>
            </div>
            {strategyForm.strategy_type === 'moving_average' ? (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">短均线窗口</label>
                  <input
                    value={strategyForm.short_window}
                    onChange={(event) => setStrategyForm((prev) => ({ ...prev, short_window: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">长均线窗口</label>
                  <input
                    value={strategyForm.long_window}
                    onChange={(event) => setStrategyForm((prev) => ({ ...prev, long_window: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            ) : null}
            {strategyForm.strategy_type === 'rsi' ? (
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">RSI 周期</label>
                  <input
                    value={strategyForm.rsi_period}
                    onChange={(event) => setStrategyForm((prev) => ({ ...prev, rsi_period: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">买入阈值</label>
                  <input
                    value={strategyForm.rsi_buy}
                    onChange={(event) => setStrategyForm((prev) => ({ ...prev, rsi_buy: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">卖出阈值</label>
                  <input
                    value={strategyForm.rsi_sell}
                    onChange={(event) => setStrategyForm((prev) => ({ ...prev, rsi_sell: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            ) : null}
            {strategyForm.strategy_type === 'momentum' ? (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">动量周期</label>
                  <input
                    value={strategyForm.momentum_period}
                    onChange={(event) => setStrategyForm((prev) => ({ ...prev, momentum_period: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">动量阈值</label>
                  <input
                    value={strategyForm.momentum_threshold}
                    onChange={(event) => setStrategyForm((prev) => ({ ...prev, momentum_threshold: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            ) : null}
            <div>
              <label className="block text-xs text-gray-600 mb-1">描述</label>
              <textarea
                rows={2}
                value={strategyForm.description}
                onChange={(event) => setStrategyForm((prev) => ({ ...prev, description: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
              />
            </div>
            <button
              type="submit"
              disabled={creatingStrategy}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {creatingStrategy ? '创建中...' : '创建策略'}
            </button>
          </form>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center gap-2 mb-4">
            <PlayCircle className="h-4 w-4 text-emerald-600" />
            <h2 className="text-lg font-semibold text-gray-900">运行回测</h2>
          </div>
          <form className="space-y-3" onSubmit={handleRunBacktest}>
            <div>
              <label className="block text-xs text-gray-600 mb-1">选择策略</label>
              <select
                value={backtestForm.strategy_id}
                onChange={(event) => setBacktestForm((prev) => ({ ...prev, strategy_id: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
              >
                <option value="">请选择策略</option>
                {strategies.map((item) => (
                  <option key={item.id} value={item.id}>{item.name} ({item.strategy_type})</option>
                ))}
              </select>
              {runningStrategy ? (
                <p className="mt-1 text-xs text-gray-600">
                  当前参数: {formatStrategyParameters(runningStrategy)}
                </p>
              ) : null}
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">股票代码（逗号分隔）</label>
              <input
                value={backtestForm.symbols}
                onChange={(event) => setBacktestForm((prev) => ({ ...prev, symbols: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="AAPL,MSFT,GOOGL"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">开始日期</label>
                <input
                  type="date"
                  value={backtestForm.start_date}
                  onChange={(event) => setBacktestForm((prev) => ({ ...prev, start_date: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">结束日期</label>
                <input
                  type="date"
                  value={backtestForm.end_date}
                  onChange={(event) => setBacktestForm((prev) => ({ ...prev, end_date: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">初始资金</label>
                <input
                  value={backtestForm.initial_capital}
                  onChange={(event) => setBacktestForm((prev) => ({ ...prev, initial_capital: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">单次仓位比例</label>
                <input
                  value={backtestForm.allocation_per_trade}
                  onChange={(event) => setBacktestForm((prev) => ({ ...prev, allocation_per_trade: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">手续费率</label>
                <input
                  value={backtestForm.commission_rate}
                  onChange={(event) => setBacktestForm((prev) => ({ ...prev, commission_rate: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={runningBacktest}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {runningBacktest ? '执行中...' : '运行回测'}
            </button>
          </form>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">已创建策略管理</h2>
            <p className="text-sm text-gray-600">在这里查看、修改并保存已有策略参数，不影响上方“创建策略”流程。</p>
          </div>
          {selectedManagedStrategy ? (
            <button
              type="button"
              onClick={() => setBacktestForm((prev) => ({ ...prev, strategy_id: String(selectedManagedStrategy.id) }))}
              className="px-3 py-2 text-sm border border-blue-600 text-blue-600 rounded-lg hover:border-blue-700 hover:text-blue-700"
            >
              应用到运行回测
            </button>
          ) : null}
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-3 py-2 text-left">策略</th>
                  <th className="px-3 py-2 text-left">类型</th>
                  <th className="px-3 py-2 text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {strategies.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-3 py-5 text-sm text-gray-500 text-center">暂无策略，请先创建。</td>
                  </tr>
                ) : strategies.map((item) => {
                  const isSelected = String(item.id) === String(selectedManagedStrategyId);
                  return (
                    <tr key={item.id} className={isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'}>
                      <td className="px-3 py-2 text-sm text-gray-900">
                        <div className="font-medium">{item.name}</div>
                        <div className="text-xs text-gray-500">{formatStrategyParameters(item)}</div>
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-700">{item.strategy_type}</td>
                      <td className="px-3 py-2 text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedManagedStrategyId(String(item.id))}
                          className={`px-2 py-1 text-xs rounded-md ${
                            isSelected
                              ? 'bg-blue-700 text-white'
                              : 'text-blue-600 hover:text-blue-700 hover:bg-blue-50'
                          }`}
                        >
                          {isSelected ? '当前' : '编辑'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <form className="space-y-3" onSubmit={handleSaveManagedStrategy}>
            <div>
              <label className="block text-xs text-gray-600 mb-1">策略名称</label>
              <input
                value={managedStrategyForm.name}
                onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, name: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="选择左侧策略后可编辑"
                disabled={!selectedManagedStrategy}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">策略类型</label>
              <select
                value={managedStrategyForm.strategy_type}
                onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, strategy_type: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
                disabled={!selectedManagedStrategy}
              >
                <option value="moving_average">均线策略</option>
                <option value="rsi">RSI 策略</option>
                <option value="momentum">动量策略</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">{getStrategyHint(managedStrategyForm.strategy_type)}</p>
            </div>
            {managedStrategyForm.strategy_type === 'moving_average' ? (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">短均线窗口</label>
                  <input
                    value={managedStrategyForm.short_window}
                    onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, short_window: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!selectedManagedStrategy}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">长均线窗口</label>
                  <input
                    value={managedStrategyForm.long_window}
                    onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, long_window: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!selectedManagedStrategy}
                  />
                </div>
              </div>
            ) : null}
            {managedStrategyForm.strategy_type === 'rsi' ? (
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">RSI 周期</label>
                  <input
                    value={managedStrategyForm.rsi_period}
                    onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, rsi_period: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!selectedManagedStrategy}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">买入阈值</label>
                  <input
                    value={managedStrategyForm.rsi_buy}
                    onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, rsi_buy: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!selectedManagedStrategy}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">卖出阈值</label>
                  <input
                    value={managedStrategyForm.rsi_sell}
                    onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, rsi_sell: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!selectedManagedStrategy}
                  />
                </div>
              </div>
            ) : null}
            {managedStrategyForm.strategy_type === 'momentum' ? (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">动量周期</label>
                  <input
                    value={managedStrategyForm.momentum_period}
                    onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, momentum_period: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!selectedManagedStrategy}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">动量阈值</label>
                  <input
                    value={managedStrategyForm.momentum_threshold}
                    onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, momentum_threshold: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!selectedManagedStrategy}
                  />
                </div>
              </div>
            ) : null}
            <div>
              <label className="block text-xs text-gray-600 mb-1">描述</label>
              <textarea
                rows={2}
                value={managedStrategyForm.description}
                onChange={(event) => setManagedStrategyForm((prev) => ({ ...prev, description: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
                disabled={!selectedManagedStrategy}
              />
            </div>
            <button
              type="submit"
              disabled={savingManagedStrategy || !selectedManagedStrategy}
              className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
            >
              {savingManagedStrategy ? '保存中...' : '保存策略修改'}
            </button>
          </form>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className="h-4 w-4 text-purple-600" />
          <h2 className="text-lg font-semibold text-gray-900">回测任务列表</h2>
        </div>
        {selectedBacktest ? (
          <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-blue-300 bg-blue-100 px-3 py-2 text-sm text-blue-900">
            <span className="inline-flex h-2.5 w-2.5 rounded-full bg-blue-700" />
            <span className="font-semibold">当前选中任务 #{selectedBacktest.id}</span>
            <span>（下方展示的是该任务的回测结果）</span>
          </div>
        ) : null}
        {runStateHint ? (
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
            {runStateHint}
          </p>
        ) : null}
        {backtests.length === 0 ? (
          <p className="text-sm text-gray-500">暂无回测任务，先创建策略并执行一次回测。</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-3 py-2 text-left">ID</th>
                  <th className="px-3 py-2 text-left">状态</th>
                  <th className="px-3 py-2 text-left">代码</th>
                  <th className="px-3 py-2 text-right">收益率</th>
                  <th className="px-3 py-2 text-right">交易数</th>
                  <th className="px-3 py-2 text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {backtests.map((item) => {
                  const isSelected = Number(selectedBacktest?.id) === Number(item.id);
                  const selectedCellClass = isSelected ? 'bg-blue-100 text-blue-950 border-y border-blue-300' : '';
                  return (
                  <tr key={item.id} className={`${isSelected ? 'bg-blue-100 shadow-[inset_0_0_0_2px_rgba(30,64,175,0.45)]' : 'hover:bg-gray-50'}`}>
                    <td className={`px-3 py-2 text-sm text-gray-900 ${selectedCellClass} ${isSelected ? 'border-l-4 border-blue-600 font-semibold' : ''}`}>
                      <div className="flex items-center gap-2">
                        <span>#{item.id}</span>
                        {isSelected ? (
                          <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-700 text-white font-semibold shadow-sm">当前</span>
                        ) : null}
                      </div>
                    </td>
                    <td className={`px-3 py-2 text-sm ${selectedCellClass}`}>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        item.status === 'completed'
                          ? 'bg-emerald-100 text-emerald-700'
                          : item.status === 'failed'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-slate-100 text-slate-700'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                    <td className={`px-3 py-2 text-sm text-gray-700 ${selectedCellClass}`}>{(item.symbols || []).join(', ')}</td>
                    <td className={`px-3 py-2 text-sm text-right ${item.total_return >= 0 ? 'text-emerald-700' : 'text-red-700'} ${selectedCellClass}`}>
                      {fmtPercent(item.total_return)}
                    </td>
                    <td className={`px-3 py-2 text-sm text-right text-gray-700 ${selectedCellClass}`}>{item.trade_count}</td>
                    <td className={`px-3 py-2 text-right ${selectedCellClass} ${isSelected ? 'border-r-4 border-blue-600' : ''}`}>
                      <button
                        type="button"
                        onClick={() => handleSelectBacktest(item.id)}
                        aria-current={isSelected ? 'true' : 'false'}
                        className={`text-sm px-3 py-1 rounded-md transition-colors ${
                          isSelected
                            ? 'bg-blue-700 text-white shadow-sm ring-2 ring-blue-300 hover:bg-blue-800'
                            : 'text-blue-600 hover:text-blue-700 hover:bg-blue-50'
                        }`}
                      >
                        {isSelected ? '当前查看中' : '查看'}
                      </button>
                    </td>
                  </tr>
                );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedBacktest ? (
        <>
          <div className="rounded-lg border border-blue-700 bg-gradient-to-r from-blue-700 to-blue-600 px-4 py-3 shadow-sm">
            <div className="flex flex-wrap items-center gap-2 text-sm text-blue-50">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-white text-blue-700 text-xs font-semibold">当前任务</span>
              <span className="font-semibold text-white">当前回测结果</span>
              <span className="text-blue-200">·</span>
              <span>任务 #{selectedBacktest.id}</span>
              <span className="text-blue-200">·</span>
              <span>状态 {selectedBacktest.status}</span>
              <span className="text-blue-200">·</span>
              <span>{(selectedBacktest.symbols || []).join(', ')}</span>
              <span className="text-blue-200">·</span>
              <span>{selectedBacktest.start_date} ~ {selectedBacktest.end_date}</span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">最终资产</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">${fmtCurrency(selectedBacktest.final_value)}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">总收益率</p>
              <p className={`text-2xl font-bold mt-1 ${selectedBacktest.total_return >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {fmtPercent(selectedBacktest.total_return)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">夏普 / 最大回撤</p>
              <p className="text-sm mt-2 text-gray-700">
                夏普比率: <span className="font-semibold">{Number(selectedBacktest.sharpe_ratio || 0).toFixed(4)}</span>
              </p>
              <p className="text-sm mt-1 text-gray-700">
                最大回撤: <span className="font-semibold">{fmtPercent(-Math.abs(selectedBacktest.max_drawdown || 0))}</span>
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">胜率 / 交易</p>
              <p className="text-sm mt-2 text-gray-700">
                胜率: <span className="font-semibold">{fmtPercent(selectedBacktest.win_rate || 0)}</span>
              </p>
              <p className="text-sm mt-1 text-gray-700">
                交易次数: <span className="font-semibold">{selectedBacktest.trade_count}</span>
              </p>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">收益曲线</h2>
            </div>
            <EquityCurveChart points={selectedBacktest.results?.equity_curve || []} />
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">交易记录</h2>
            {selectedBacktest.trades?.length ? (
              <div className="overflow-x-auto max-h-96">
                <table className="w-full">
                  <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                    <tr>
                      <th className="px-3 py-2 text-left">时间</th>
                      <th className="px-3 py-2 text-left">代码</th>
                      <th className="px-3 py-2 text-left">方向</th>
                      <th className="px-3 py-2 text-right">数量</th>
                      <th className="px-3 py-2 text-right">价格</th>
                      <th className="px-3 py-2 text-right">手续费</th>
                      <th className="px-3 py-2 text-right">PnL</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {selectedBacktest.trades.map((trade) => (
                      <tr key={trade.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-sm text-gray-700">
                          {new Date(trade.timestamp).toLocaleString('zh-CN')}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-900">{trade.symbol}</td>
                        <td className="px-3 py-2 text-sm">{trade.action}</td>
                        <td className="px-3 py-2 text-sm text-right">{Number(trade.quantity || 0).toFixed(2)}</td>
                        <td className="px-3 py-2 text-sm text-right">${Number(trade.price || 0).toFixed(2)}</td>
                        <td className="px-3 py-2 text-sm text-right">${Number(trade.commission || 0).toFixed(2)}</td>
                        <td className={`px-3 py-2 text-sm text-right ${trade.pnl >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                          {trade.pnl >= 0 ? '+' : ''}{Number(trade.pnl || 0).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-500">该回测没有生成交易记录。</p>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}
