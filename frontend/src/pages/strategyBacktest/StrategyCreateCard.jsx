import { PlusCircle } from 'lucide-react';
import { getStrategyHint } from './helpers';

export default function StrategyCreateCard({
  strategyForm,
  setStrategyForm,
  creatingStrategy,
  onSubmit,
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <PlusCircle className="h-4 w-4 text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-900">创建策略</h2>
      </div>
      <form className="space-y-3" onSubmit={onSubmit}>
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
          <p className="text-xs text-gray-500 mt-1">{getStrategyHint(strategyForm.strategy_type)}</p>
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
  );
}

