import { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';
import { createStrategy, getStrategies, updateStrategy } from '../services/strategyAPI';
import { getBacktest, getBacktests, runBacktest } from '../services/backtestAPI';
import BacktestResultSection from './strategyBacktest/BacktestResultSection';
import BacktestRunCard from './strategyBacktest/BacktestRunCard';
import BacktestTaskListSection from './strategyBacktest/BacktestTaskListSection';
import StrategyCreateCard from './strategyBacktest/StrategyCreateCard';
import StrategyManagementSection from './strategyBacktest/StrategyManagementSection';
import {
  STRATEGY_FORM_DEFAULTS,
  buildBacktestErrorMessage,
  buildStrategyParametersByType,
  makeStrategyFormFromRecord,
  oneYearAgoDateString,
  toNumber,
  todayDateString,
} from './strategyBacktest/helpers';

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
        <StrategyCreateCard
          strategyForm={strategyForm}
          setStrategyForm={setStrategyForm}
          creatingStrategy={creatingStrategy}
          onSubmit={handleCreateStrategy}
        />
        <BacktestRunCard
          backtestForm={backtestForm}
          setBacktestForm={setBacktestForm}
          runningBacktest={runningBacktest}
          onSubmit={handleRunBacktest}
          strategies={strategies}
          runningStrategy={runningStrategy}
        />
      </div>

      <StrategyManagementSection
        strategies={strategies}
        selectedManagedStrategyId={selectedManagedStrategyId}
        setSelectedManagedStrategyId={setSelectedManagedStrategyId}
        managedStrategyForm={managedStrategyForm}
        setManagedStrategyForm={setManagedStrategyForm}
        selectedManagedStrategy={selectedManagedStrategy}
        setBacktestForm={setBacktestForm}
        savingManagedStrategy={savingManagedStrategy}
        onSubmit={handleSaveManagedStrategy}
      />

      <BacktestTaskListSection
        backtests={backtests}
        selectedBacktest={selectedBacktest}
        runStateHint={runStateHint}
        onSelectBacktest={handleSelectBacktest}
      />

      <BacktestResultSection selectedBacktest={selectedBacktest} />
    </div>
  );
}
