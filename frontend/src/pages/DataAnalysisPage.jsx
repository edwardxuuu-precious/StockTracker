import { useEffect, useMemo, useState } from 'react';
import { BarChart3, Download, PieChart, RefreshCw, TrendingUp } from 'lucide-react';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import NoticeBanner from '../components/Common/NoticeBanner';
import * as portfolioAPI from '../services/portfolioAPI';
import { exportPortfolioAnalyticsCsv, getPortfolioAnalytics } from '../services/analyticsAPI';
import { getErrorMessage } from '../utils/errorMessage';

const PIE_COLORS = ['#2563eb', '#16a34a', '#ea580c', '#7c3aed', '#0891b2', '#db2777', '#4f46e5'];

function fmtCurrency(value) {
  return Number(value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtPercent(value) {
  const num = Number(value || 0);
  return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
}

function RealizedTrendChart({ points }) {
  if (!points?.length || points.length < 2) {
    return <p className="text-sm text-gray-500">交易数据不足，暂无趋势图。</p>;
  }

  const width = 760;
  const height = 240;
  const padding = 26;
  const values = points.map((item) => Number(item.cumulative_realized_pnl || 0));
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);
  const range = max - min || 1;

  const dots = points.map((item, index) => {
    const x = padding + (index / (points.length - 1)) * (width - padding * 2);
    const normalized = (Number(item.cumulative_realized_pnl || 0) - min) / range;
    const y = height - padding - normalized * (height - padding * 2);
    return { x, y };
  });

  const path = dots.map((dot) => `${dot.x},${dot.y}`).join(' ');
  const zeroY = height - padding - ((0 - min) / range) * (height - padding * 2);

  return (
    <div className="space-y-2">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56 bg-slate-50 rounded-lg border border-slate-200">
        <line x1={padding} y1={zeroY} x2={width - padding} y2={zeroY} stroke="#cbd5e1" strokeDasharray="4 4" />
        <polyline fill="none" stroke="#2563eb" strokeWidth="3" points={path} />
        {dots.map((dot, idx) => (
          <circle key={`${dot.x}-${dot.y}-${idx}`} cx={dot.x} cy={dot.y} r="3" fill="#1d4ed8" />
        ))}
      </svg>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{points[0]?.label || '起点'}</span>
        <span>{points[points.length - 1]?.label || '终点'}</span>
      </div>
    </div>
  );
}

function MonthlyPnlChart({ monthly }) {
  if (!monthly?.length) {
    return <p className="text-sm text-gray-500">暂无月度成交记录。</p>;
  }

  const maxAbs = Math.max(...monthly.map((item) => Math.abs(Number(item.realized_pnl || 0))), 1);

  return (
    <div className="space-y-3">
      {monthly.map((item) => {
        const pnl = Number(item.realized_pnl || 0);
        const widthPct = Math.max((Math.abs(pnl) / maxAbs) * 100, 2);
        const positive = pnl >= 0;
        return (
          <div key={item.month} className="space-y-1">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>{item.month}</span>
              <span className={positive ? 'text-emerald-700' : 'text-red-700'}>
                {positive ? '+' : ''}{pnl.toFixed(2)} ({item.trade_count} 笔)
              </span>
            </div>
            <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
              <div
                className={`h-3 ${positive ? 'bg-emerald-500' : 'bg-red-500'}`}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AllocationPie({ allocation }) {
  if (!allocation?.length) {
    return <p className="text-sm text-gray-500">暂无持仓分布数据。</p>;
  }

  const segmentState = allocation.reduce(
    (acc, item, idx) => {
      const weight = Number(item.weight_pct || 0);
      const start = acc.cursor;
      const end = start + weight;
      return {
        cursor: end,
        segments: [
          ...acc.segments,
          {
            ...item,
            color: PIE_COLORS[idx % PIE_COLORS.length],
            start,
            end,
          },
        ],
      };
    },
    { cursor: 0, segments: [] }
  );
  const segments = segmentState.segments;
  const gradient = `conic-gradient(${segments
    .map((segment) => `${segment.color} ${segment.start}% ${segment.end}%`)
    .join(', ')})`;

  return (
    <div className="grid lg:grid-cols-[240px,1fr] gap-4 items-center">
      <div className="mx-auto h-52 w-52 rounded-full border border-slate-200" style={{ background: gradient }} />
      <div className="space-y-2">
        {segments.map((item) => (
          <div key={item.symbol} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: item.color }} />
              <span className="text-gray-800">{item.symbol}</span>
            </div>
            <span className="text-gray-600">{Number(item.weight_pct || 0).toFixed(2)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DataAnalysisPage() {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [exporting, setExporting] = useState('');
  const [reloadToken, setReloadToken] = useState(0);
  const [notice, setNotice] = useState({ type: '', message: '' });

  useEffect(() => {
    const loadPortfolios = async () => {
      try {
        setLoading(true);
        const list = await portfolioAPI.getPortfolios();
        setPortfolios(list);
        if (list.length > 0) {
          setSelectedPortfolioId(String(list[0].id));
        }
      } catch (error) {
        setNotice({ type: 'error', message: getErrorMessage(error, '加载组合列表失败') });
      } finally {
        setLoading(false);
      }
    };
    loadPortfolios();
  }, []);

  useEffect(() => {
    const loadAnalytics = async () => {
      if (!selectedPortfolioId) {
        setAnalytics(null);
        return;
      }
      try {
        setRefreshing(true);
        const data = await getPortfolioAnalytics(selectedPortfolioId);
        setAnalytics(data);
      } catch (error) {
        setNotice({ type: 'error', message: getErrorMessage(error, '加载分析数据失败') });
      } finally {
        setRefreshing(false);
      }
    };
    loadAnalytics();
  }, [selectedPortfolioId, reloadToken]);

  const selectedPortfolioName = useMemo(() => {
    const found = portfolios.find((item) => String(item.id) === String(selectedPortfolioId));
    return found?.name || '';
  }, [portfolios, selectedPortfolioId]);

  const handleExport = async (report) => {
    if (!selectedPortfolioId) return;
    try {
      setExporting(report);
      const { blob, filename } = await exportPortfolioAnalyticsCsv(selectedPortfolioId, report);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setNotice({ type: 'success', message: `已导出 ${filename}` });
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '导出 CSV 失败') });
    } finally {
      setExporting('');
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

      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">数据分析面板</h1>
          <p className="text-gray-600 mt-1">组合收益拆解、基础图表和 CSV 报表导出。</p>
        </div>
        <div className="flex items-center gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">选择组合</label>
            <select
              value={selectedPortfolioId}
              onChange={(event) => setSelectedPortfolioId(event.target.value)}
              className="min-w-[220px] px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {portfolios.length === 0 ? <option value="">暂无组合</option> : null}
              {portfolios.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={() => setReloadToken((token) => token + 1)}
            disabled={!selectedPortfolioId || refreshing}
            className="inline-flex items-center gap-2 px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:text-blue-700 hover:border-blue-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? '刷新中...' : '刷新'}
          </button>
        </div>
      </div>

      {!selectedPortfolioId ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          请先创建投资组合后再查看分析数据。
        </div>
      ) : null}

      {selectedPortfolioId && analytics?.summary ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">当前总资产</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">${fmtCurrency(analytics.summary.current_value)}</p>
              <p className="text-xs text-gray-500 mt-1">{selectedPortfolioName}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">总收益</p>
              <p className={`text-2xl font-bold mt-1 ${analytics.summary.total_return >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {analytics.summary.total_return >= 0 ? '+' : ''}${fmtCurrency(analytics.summary.total_return)}
              </p>
              <p className={`text-xs mt-1 ${analytics.summary.total_return >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {fmtPercent(analytics.summary.total_return_pct)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">已实现 / 未实现</p>
              <p className="text-sm mt-2 text-gray-700">
                已实现: <span className="font-semibold">${fmtCurrency(analytics.summary.realized_pnl)}</span>
              </p>
              <p className="text-sm mt-1 text-gray-700">
                未实现: <span className="font-semibold">${fmtCurrency(analytics.summary.unrealized_pnl)}</span>
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm text-gray-500">交易与持仓</p>
              <p className="text-sm mt-2 text-gray-700">
                交易笔数: <span className="font-semibold">{analytics.summary.total_trades}</span>
              </p>
              <p className="text-sm mt-1 text-gray-700">
                持仓数量: <span className="font-semibold">{analytics.summary.active_holdings}</span>
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
              <div className="flex items-center gap-2 text-gray-900">
                <TrendingUp className="h-4 w-4 text-blue-600" />
                <h2 className="text-lg font-semibold">收益趋势（已实现）</h2>
              </div>
              <RealizedTrendChart points={analytics.trend} />
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
              <div className="flex items-center gap-2 text-gray-900">
                <PieChart className="h-4 w-4 text-orange-600" />
                <h2 className="text-lg font-semibold">持仓分布</h2>
              </div>
              <AllocationPie allocation={analytics.allocation} />
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
              <div className="flex items-center gap-2 text-gray-900">
                <BarChart3 className="h-4 w-4 text-emerald-600" />
                <h2 className="text-lg font-semibold">月度已实现收益</h2>
              </div>
              <MonthlyPnlChart monthly={analytics.monthly_realized_pnl} />
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
              <div className="flex items-center gap-2 text-gray-900">
                <Download className="h-4 w-4 text-indigo-600" />
                <h2 className="text-lg font-semibold">导出报表 (CSV)</h2>
              </div>
              <p className="text-sm text-gray-600">可导出收益汇总、持仓明细和交易明细，便于本地复盘与二次分析。</p>
              <div className="flex flex-wrap gap-3">
                {[
                  { key: 'summary', label: '导出收益汇总' },
                  { key: 'holdings', label: '导出持仓明细' },
                  { key: 'trades', label: '导出交易明细' },
                ].map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => handleExport(item.key)}
                    disabled={exporting !== ''}
                    className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:border-slate-400 hover:bg-slate-50 disabled:opacity-50"
                  >
                    {exporting === item.key ? '导出中...' : item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
