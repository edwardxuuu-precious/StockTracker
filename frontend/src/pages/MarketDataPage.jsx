import { useCallback, useEffect, useState } from 'react';
import { Database, RefreshCw } from 'lucide-react';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';
import { getMarketDataStatus, getIngestionLogs, runIngestion } from '../services/marketDataAPI';

function toIsoString(value) {
  if (!value) return undefined;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return undefined;
  return parsed.toISOString();
}

export default function MarketDataPage() {
  const [notice, setNotice] = useState({ type: '', message: '' });
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [runningIngest, setRunningIngest] = useState(false);

  const [statusForm, setStatusForm] = useState({
    symbol: '600519',
    market: 'CN',
    interval: '1m',
    start: '',
    end: '',
  });
  const [statusResult, setStatusResult] = useState(null);

  const [logFilter, setLogFilter] = useState({
    symbol: '',
    market: '',
    interval: '',
    limit: '50',
  });
  const [ingestionLogs, setIngestionLogs] = useState([]);

  const [ingestForm, setIngestForm] = useState({
    symbols: '600519',
    market: 'CN',
    interval: '1m',
    start: '',
    end: '',
    provider: '',
  });
  const [ingestResults, setIngestResults] = useState([]);

  const loadLogs = useCallback(async () => {
    try {
      setLoadingLogs(true);
      const params = {
        symbol: logFilter.symbol || undefined,
        market: logFilter.market || undefined,
        interval: logFilter.interval || undefined,
        limit: Number(logFilter.limit) || 50,
      };
      const data = await getIngestionLogs(params);
      setIngestionLogs(data || []);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '加载入库日志失败') });
    } finally {
      setLoadingLogs(false);
    }
  }, [logFilter]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const handleStatusSubmit = async (event) => {
    event.preventDefault();
    if (!statusForm.symbol) {
      setNotice({ type: 'error', message: '请输入股票代码' });
      return;
    }
    try {
      setLoadingStatus(true);
      const params = {
        symbol: statusForm.symbol.trim(),
        market: statusForm.market,
        interval: statusForm.interval,
        start: toIsoString(statusForm.start),
        end: toIsoString(statusForm.end),
      };
      const data = await getMarketDataStatus(params);
      setStatusResult(data);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '加载数据状态失败') });
    } finally {
      setLoadingStatus(false);
    }
  };

  const handleRunIngest = async (event) => {
    event.preventDefault();
    const symbols = ingestForm.symbols
      .split(',')
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean);
    if (!symbols.length) {
      setNotice({ type: 'error', message: '请输入至少一个股票代码' });
      return;
    }
    try {
      setRunningIngest(true);
      const payload = {
        symbols,
        market: ingestForm.market,
        interval: ingestForm.interval,
        start: toIsoString(ingestForm.start),
        end: toIsoString(ingestForm.end),
        provider: ingestForm.provider || undefined,
      };
      const data = await runIngestion(payload);
      setIngestResults(data.results || []);
      setNotice({ type: 'success', message: '入库任务已完成' });
      loadLogs();
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '执行入库失败') });
    } finally {
      setRunningIngest(false);
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
          <h1 className="text-3xl font-bold text-gray-900">市场数据</h1>
          <p className="text-gray-600 mt-1">查看本地数据健康度、执行入库任务与查看日志。</p>
        </div>
        <button
          type="button"
          onClick={loadLogs}
          disabled={loadingLogs}
          className="inline-flex items-center gap-2 px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:border-blue-700 hover:text-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loadingLogs ? 'animate-spin' : ''}`} />
          {loadingLogs ? '刷新中...' : '刷新日志'}
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">数据健康检查</h2>
          </div>
          <form className="space-y-3" onSubmit={handleStatusSubmit}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">股票代码</label>
                <input
                  value={statusForm.symbol}
                  onChange={(event) => setStatusForm((prev) => ({ ...prev, symbol: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">市场</label>
                <select
                  value={statusForm.market}
                  onChange={(event) => setStatusForm((prev) => ({ ...prev, market: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
                >
                  <option value="CN">CN</option>
                  <option value="US">US</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">间隔</label>
                <select
                  value={statusForm.interval}
                  onChange={(event) => setStatusForm((prev) => ({ ...prev, interval: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
                >
                  <option value="1m">1m</option>
                  <option value="1d">1d</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">开始时间</label>
                <input
                  type="datetime-local"
                  value={statusForm.start}
                  onChange={(event) => setStatusForm((prev) => ({ ...prev, start: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">结束时间</label>
              <input
                type="datetime-local"
                value={statusForm.end}
                onChange={(event) => setStatusForm((prev) => ({ ...prev, end: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <button
              type="submit"
              disabled={loadingStatus}
              className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
            >
              {loadingStatus ? '查询中...' : '查询数据状态'}
            </button>
          </form>

          {statusResult ? (
            <div className="border border-blue-100 bg-blue-50 rounded-lg p-4 text-sm text-blue-900 space-y-2">
              <div className="flex flex-wrap gap-2">
                <span className="font-semibold">{statusResult.symbol}</span>
                <span>{statusResult.market}</span>
                <span>{statusResult.interval}</span>
              </div>
              <div>总条数: {statusResult.total_bars}</div>
              <div>起始: {statusResult.first_bar_ts || '--'}</div>
              <div>最新: {statusResult.last_bar_ts || '--'}</div>
              <div>缺口估算: {statusResult.gap_estimate}</div>
              <div>最近入库: {statusResult.last_ingest?.updated_at || '--'}</div>
              <div>最近错误: {statusResult.last_ingest?.last_error || '--'}</div>
            </div>
          ) : null}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">手动入库</h2>
          <form className="space-y-3" onSubmit={handleRunIngest}>
            <div>
              <label className="block text-xs text-gray-600 mb-1">股票代码（逗号分隔）</label>
              <input
                value={ingestForm.symbols}
                onChange={(event) => setIngestForm((prev) => ({ ...prev, symbols: event.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">市场</label>
                <select
                  value={ingestForm.market}
                  onChange={(event) => setIngestForm((prev) => ({ ...prev, market: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
                >
                  <option value="CN">CN</option>
                  <option value="US">US</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">间隔</label>
                <select
                  value={ingestForm.interval}
                  onChange={(event) => setIngestForm((prev) => ({ ...prev, interval: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
                >
                  <option value="1m">1m</option>
                  <option value="1d">1d</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Provider</label>
                <input
                  value={ingestForm.provider}
                  onChange={(event) => setIngestForm((prev) => ({ ...prev, provider: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="akshare"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">开始时间</label>
                <input
                  type="datetime-local"
                  value={ingestForm.start}
                  onChange={(event) => setIngestForm((prev) => ({ ...prev, start: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">结束时间</label>
                <input
                  type="datetime-local"
                  value={ingestForm.end}
                  onChange={(event) => setIngestForm((prev) => ({ ...prev, end: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={runningIngest}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {runningIngest ? '执行中...' : '执行入库'}
            </button>
          </form>
          {ingestResults.length ? (
            <div className="border border-emerald-100 bg-emerald-50 rounded-lg p-4 text-sm text-emerald-900 space-y-1">
              {ingestResults.map((item) => (
                <div key={`${item.symbol}-${item.interval}`}>
                  {item.symbol} {item.market} {item.interval} {item.status} (ingested: {item.ingested})
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">入库日志</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
          <input
            placeholder="Symbol"
            value={logFilter.symbol}
            onChange={(event) => setLogFilter((prev) => ({ ...prev, symbol: event.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          />
          <input
            placeholder="Market"
            value={logFilter.market}
            onChange={(event) => setLogFilter((prev) => ({ ...prev, market: event.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          />
          <input
            placeholder="Interval"
            value={logFilter.interval}
            onChange={(event) => setLogFilter((prev) => ({ ...prev, interval: event.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          />
          <input
            placeholder="Limit"
            value={logFilter.limit}
            onChange={(event) => setLogFilter((prev) => ({ ...prev, limit: event.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          />
        </div>
        {loadingLogs ? (
          <p className="text-sm text-gray-500">加载中...</p>
        ) : ingestionLogs.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-3 py-2 text-left">时间</th>
                  <th className="px-3 py-2 text-left">代码</th>
                  <th className="px-3 py-2 text-left">市场</th>
                  <th className="px-3 py-2 text-left">间隔</th>
                  <th className="px-3 py-2 text-left">状态</th>
                  <th className="px-3 py-2 text-left">消息</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ingestionLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-3 py-2 text-gray-700">{log.created_at || '--'}</td>
                    <td className="px-3 py-2 text-gray-900">{log.symbol || '--'}</td>
                    <td className="px-3 py-2 text-gray-700">{log.market}</td>
                    <td className="px-3 py-2 text-gray-700">{log.interval}</td>
                    <td className="px-3 py-2">
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700">
                        {log.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-600">{log.message || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">暂无入库日志。</p>
        )}
      </div>
    </div>
  );
}
