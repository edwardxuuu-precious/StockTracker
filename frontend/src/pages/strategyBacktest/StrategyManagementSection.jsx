import { formatStrategyParameters, getStrategyHint } from './helpers';

export default function StrategyManagementSection({
  strategies,
  selectedManagedStrategyId,
  setSelectedManagedStrategyId,
  managedStrategyForm,
  setManagedStrategyForm,
  selectedManagedStrategy,
  setBacktestForm,
  savingManagedStrategy,
  onSubmit,
}) {
  return (
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

        <form className="space-y-3" onSubmit={onSubmit}>
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
  );
}

