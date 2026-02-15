import { BarChart3 } from 'lucide-react';
import { fmtPercent } from './helpers';

export default function BacktestTaskListSection({
  backtests,
  selectedBacktest,
  runStateHint,
  onSelectBacktest,
}) {
  return (
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
                        onClick={() => onSelectBacktest(item.id)}
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
  );
}
