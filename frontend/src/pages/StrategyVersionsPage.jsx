import { useEffect, useState } from 'react';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';
import { getStrategies } from '../services/strategyAPI';
import {
  compareStrategyVersions,
  createStrategyVersion,
  listStrategyVersions,
} from '../services/strategyVersionAPI';

export default function StrategyVersionsPage() {
  const [notice, setNotice] = useState({ type: '', message: '' });
  const [strategies, setStrategies] = useState([]);
  const [strategyId, setStrategyId] = useState('');
  const [versions, setVersions] = useState([]);
  const [selectedVersionIds, setSelectedVersionIds] = useState([]);
  const [compareResult, setCompareResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const list = await getStrategies(200);
        setStrategies(list || []);
        if (list?.length) setStrategyId(String(list[0].id));
      } catch (error) {
        setNotice({ type: 'error', message: getErrorMessage(error, '加载策略列表失败') });
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (!strategyId) return;
    const loadVersions = async () => {
      try {
        setLoading(true);
        const data = await listStrategyVersions(Number(strategyId));
        setVersions(data || []);
        setSelectedVersionIds([]);
        setCompareResult(null);
      } catch (error) {
        setNotice({ type: 'error', message: getErrorMessage(error, '加载版本列表失败') });
      } finally {
        setLoading(false);
      }
    };
    loadVersions();
  }, [strategyId]);

  const toggleSelect = (id) => {
    setSelectedVersionIds((prev) => {
      if (prev.includes(id)) return prev.filter((item) => item !== id);
      if (prev.length >= 10) return prev;
      return [...prev, id];
    });
  };

  const handleCreateSnapshot = async () => {
    if (!strategyId) return;
    try {
      await createStrategyVersion(Number(strategyId), { note: 'manual snapshot', created_by: 'ui' });
      const data = await listStrategyVersions(Number(strategyId));
      setVersions(data || []);
      setNotice({ type: 'success', message: '版本快照已创建' });
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '创建版本失败') });
    }
  };

  const handleCompare = async () => {
    if (selectedVersionIds.length < 2) {
      setNotice({ type: 'error', message: '请至少选择两个版本进行对比' });
      return;
    }
    try {
      const result = await compareStrategyVersions({ version_ids: selectedVersionIds });
      setCompareResult(result);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '版本对比失败') });
    }
  };

  return (
    <div className="space-y-6">
      <NoticeBanner
        type={notice.type || 'info'}
        message={notice.message}
        onClose={() => setNotice({ type: '', message: '' })}
      />

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">策略版本浏览</h1>
          <p className="text-gray-600 mt-1">查看版本快照并对比回测结果。</p>
        </div>
        <button
          type="button"
          onClick={handleCreateSnapshot}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
        >
          创建当前快照
        </button>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <label className="block text-xs text-gray-600 mb-1">选择策略</label>
        <select
          value={strategyId}
          onChange={(event) => setStrategyId(event.target.value)}
          className="w-full md:w-96 px-3 py-2 border border-gray-300 rounded-lg bg-white"
        >
          {strategies.map((item) => (
            <option key={item.id} value={item.id}>
              {item.id} - {item.name}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">版本列表</h2>
          <button
            type="button"
            onClick={handleCompare}
            className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800"
          >
            对比选中版本
          </button>
        </div>
        {loading ? (
          <p className="text-sm text-gray-500">加载中...</p>
        ) : versions.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-3 py-2 text-left">选择</th>
                  <th className="px-3 py-2 text-left">版本</th>
                  <th className="px-3 py-2 text-left">类型</th>
                  <th className="px-3 py-2 text-left">备注</th>
                  <th className="px-3 py-2 text-left">创建者</th>
                  <th className="px-3 py-2 text-left">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {versions.map((item) => (
                  <tr key={item.id}>
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selectedVersionIds.includes(item.id)}
                        onChange={() => toggleSelect(item.id)}
                      />
                    </td>
                    <td className="px-3 py-2 text-gray-900">v{item.version_no}</td>
                    <td className="px-3 py-2 text-gray-700">{item.strategy_type}</td>
                    <td className="px-3 py-2 text-gray-700">{item.note || '--'}</td>
                    <td className="px-3 py-2 text-gray-700">{item.created_by}</td>
                    <td className="px-3 py-2 text-gray-600">{item.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">暂无版本快照。</p>
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">对比结果</h2>
        {compareResult?.items?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-3 py-2 text-left">版本</th>
                  <th className="px-3 py-2 text-right">回测次数</th>
                  <th className="px-3 py-2 text-right">最佳收益</th>
                  <th className="px-3 py-2 text-right">最佳夏普</th>
                  <th className="px-3 py-2 text-left">最近完成</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {compareResult.items.map((item) => (
                  <tr key={item.version.id}>
                    <td className="px-3 py-2 text-gray-900">v{item.version.version_no}</td>
                    <td className="px-3 py-2 text-right text-gray-700">{item.backtest_count}</td>
                    <td className="px-3 py-2 text-right text-gray-700">
                      {item.best_total_return !== null ? `${Number(item.best_total_return).toFixed(4)}%` : '--'}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-700">
                      {item.best_sharpe_ratio !== null ? Number(item.best_sharpe_ratio).toFixed(4) : '--'}
                    </td>
                    <td className="px-3 py-2 text-gray-600">{item.latest_completed_at || '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">请选择两个或以上版本后执行对比。</p>
        )}
      </div>
    </div>
  );
}
