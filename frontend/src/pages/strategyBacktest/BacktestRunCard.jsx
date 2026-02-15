import { PlayCircle } from 'lucide-react';
import { formatStrategyParameters } from './helpers';

export default function BacktestRunCard({
  backtestForm,
  setBacktestForm,
  runningBacktest,
  onSubmit,
  strategies,
  runningStrategy,
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <PlayCircle className="h-4 w-4 text-emerald-600" />
        <h2 className="text-lg font-semibold text-gray-900">运行回测</h2>
      </div>
      <form className="space-y-3" onSubmit={onSubmit}>
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
  );
}

