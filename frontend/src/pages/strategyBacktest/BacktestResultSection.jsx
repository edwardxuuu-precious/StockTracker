import { TrendingUp } from 'lucide-react';
import EquityCurveChart from './EquityCurveChart';
import { fmtCurrency, fmtPercent } from './helpers';

export default function BacktestResultSection({ selectedBacktest }) {
  if (!selectedBacktest) {
    return null;
  }

  return (
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
  );
}
