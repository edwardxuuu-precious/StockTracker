import { useCallback, useEffect, useMemo, useState } from 'react';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';
import { getStrategies } from '../services/strategyAPI';
import { createChatSession, getChatMessages, postChatMessage } from '../services/chatAPI';
import {
  buildBacktestReportByAgent,
  generateStrategyByPrompt,
  tuneStrategyByAgent,
} from '../services/agentAPI';

function defaultDateRange() {
  const end = new Date();
  const start = new Date();
  start.setMonth(start.getMonth() - 3);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

export default function AgentPage() {
  const dates = useMemo(() => defaultDateRange(), []);
  const [notice, setNotice] = useState({ type: '', message: '' });
  const [strategies, setStrategies] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [chatText, setChatText] = useState('');

  const [prompt, setPrompt] = useState('请生成一个均线策略，短线5长线20');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(null);

  const [tuning, setTuning] = useState(false);
  const [tuneResult, setTuneResult] = useState(null);
  const [tuneForm, setTuneForm] = useState({
    strategy_id: '',
    symbols: 'AAPL',
    market: 'US',
    interval: '1d',
    start_date: dates.start,
    end_date: dates.end,
    initial_capital: '100000',
    objective: 'total_return',
    max_trials: '12',
    top_k: '5',
    parameter_grid: '{"short_window":[3,5,8],"long_window":[15,20,30]}',
  });

  const [reporting, setReporting] = useState(false);
  const [reportForm, setReportForm] = useState({ backtest_id: '', question: '如何降低回撤？' });
  const [report, setReport] = useState(null);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const [session, strategyList] = await Promise.all([createChatSession(), getStrategies(200)]);
        setSessionId(session.id);
        setStrategies(strategyList || []);
        if (strategyList?.length) {
          setTuneForm((prev) => ({ ...prev, strategy_id: String(strategyList[0].id) }));
        }
      } catch (error) {
        setNotice({ type: 'error', message: getErrorMessage(error, '初始化 Agent 页面失败') });
      }
    };
    bootstrap();
  }, []);

  const refreshMessages = useCallback(async () => {
    if (!sessionId) return;
    try {
      const list = await getChatMessages(sessionId, { limit: 200 });
      setMessages(list || []);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '加载聊天记录失败') });
    }
  }, [sessionId]);

  useEffect(() => {
    refreshMessages();
  }, [refreshMessages]);

  const handleSendChat = async (event) => {
    event.preventDefault();
    if (!sessionId || !chatText.trim()) return;
    try {
      setSending(true);
      await postChatMessage(sessionId, { content: chatText.trim() });
      setChatText('');
      await refreshMessages();
      const strategyList = await getStrategies(200);
      setStrategies(strategyList || []);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '发送消息失败') });
    } finally {
      setSending(false);
    }
  };

  const handleGenerate = async (event) => {
    event.preventDefault();
    if (!prompt.trim()) {
      setNotice({ type: 'error', message: '请输入策略描述' });
      return;
    }
    try {
      setGenerating(true);
      const data = await generateStrategyByPrompt({ prompt, save_strategy: true });
      setGenerated(data);
      const strategyList = await getStrategies(200);
      setStrategies(strategyList || []);
      if (data.strategy?.id) {
        setTuneForm((prev) => ({ ...prev, strategy_id: String(data.strategy.id) }));
      }
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '生成策略失败') });
    } finally {
      setGenerating(false);
    }
  };

  const handleTune = async (event) => {
    event.preventDefault();
    if (!tuneForm.strategy_id) {
      setNotice({ type: 'error', message: '请选择策略' });
      return;
    }
    let parameterGrid;
    try {
      parameterGrid = JSON.parse(tuneForm.parameter_grid || '{}');
    } catch {
      setNotice({ type: 'error', message: '参数网格 JSON 格式错误' });
      return;
    }
    try {
      setTuning(true);
      const data = await tuneStrategyByAgent({
        strategy_id: Number(tuneForm.strategy_id),
        symbols: tuneForm.symbols.split(',').map((item) => item.trim().toUpperCase()).filter(Boolean),
        start_date: tuneForm.start_date,
        end_date: tuneForm.end_date,
        initial_capital: Number(tuneForm.initial_capital),
        market: tuneForm.market,
        interval: tuneForm.interval,
        objective: tuneForm.objective,
        max_trials: Number(tuneForm.max_trials),
        top_k: Number(tuneForm.top_k),
        parameter_grid: parameterGrid,
      });
      setTuneResult(data);
      setReportForm((prev) => ({ ...prev, backtest_id: String(data.best_trial.backtest_id) }));
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '自动调参失败') });
    } finally {
      setTuning(false);
    }
  };

  const handleBuildReport = async (event) => {
    event.preventDefault();
    if (!reportForm.backtest_id) {
      setNotice({ type: 'error', message: '请输入回测 ID' });
      return;
    }
    try {
      setReporting(true);
      const data = await buildBacktestReportByAgent(Number(reportForm.backtest_id), {
        question: reportForm.question,
        top_k_sources: 3,
      });
      setReport(data);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '生成报告失败') });
    } finally {
      setReporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <NoticeBanner
        type={notice.type || 'info'}
        message={notice.message}
        onClose={() => setNotice({ type: '', message: '' })}
      />

      <div>
        <h1 className="text-3xl font-bold text-gray-900">Agent 工作台</h1>
        <p className="text-gray-600 mt-1">自然语言生成策略、自动调参、复盘报告。</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">会话助手</h2>
          <div className="border border-gray-200 rounded-lg p-3 h-72 overflow-auto bg-gray-50">
            {messages.length ? messages.map((item) => (
              <div key={item.id} className="mb-2 text-sm">
                <span className={`font-semibold ${item.role === 'assistant' ? 'text-blue-700' : 'text-gray-900'}`}>
                  {item.role === 'assistant' ? 'Agent' : 'You'}:
                </span>
                <span className="ml-2 text-gray-700 whitespace-pre-line">{item.content}</span>
              </div>
            )) : <p className="text-sm text-gray-500">暂无消息。</p>}
          </div>
          <form className="mt-3 flex gap-2" onSubmit={handleSendChat}>
            <input
              value={chatText}
              onChange={(event) => setChatText(event.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
              placeholder="输入：请生成一个 RSI 策略"
            />
            <button
              type="submit"
              disabled={sending}
              className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
            >
              {sending ? '发送中...' : '发送'}
            </button>
          </form>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">生成策略脚本</h2>
          <form className="space-y-3" onSubmit={handleGenerate}>
            <textarea
              rows={4}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
            />
            <button
              type="submit"
              disabled={generating}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {generating ? '生成中...' : '生成并保存'}
            </button>
          </form>
          {generated ? (
            <div className="mt-3 border border-emerald-100 bg-emerald-50 rounded-lg p-3">
              <p className="text-sm text-emerald-900">类型: {generated.detected_strategy_type}</p>
              <p className="text-sm text-emerald-900 mt-1">{generated.rationale}</p>
              <pre className="mt-2 text-xs bg-white border border-emerald-200 rounded p-2 overflow-auto max-h-44">
                {generated.code}
              </pre>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">自动调参</h2>
          <form className="space-y-3" onSubmit={handleTune}>
            <select
              value={tuneForm.strategy_id}
              onChange={(event) => setTuneForm((prev) => ({ ...prev, strategy_id: event.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
            >
              {strategies.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.id} - {item.name}
                </option>
              ))}
            </select>
            <div className="grid grid-cols-2 gap-3">
              <input
                value={tuneForm.symbols}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, symbols: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="AAPL,MSFT"
              />
              <select
                value={tuneForm.market}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, market: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg bg-white"
              >
                <option value="US">US</option>
                <option value="CN">CN</option>
              </select>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <input
                type="date"
                value={tuneForm.start_date}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, start_date: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              />
              <input
                type="date"
                value={tuneForm.end_date}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, end_date: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              />
              <input
                value={tuneForm.initial_capital}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, initial_capital: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <select
                value={tuneForm.interval}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, interval: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg bg-white"
              >
                <option value="1d">1d</option>
                <option value="1m">1m</option>
              </select>
              <select
                value={tuneForm.objective}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, objective: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg bg-white"
              >
                <option value="total_return">total_return</option>
                <option value="sharpe_ratio">sharpe_ratio</option>
                <option value="win_rate">win_rate</option>
                <option value="min_drawdown">min_drawdown</option>
              </select>
              <input
                value={tuneForm.max_trials}
                onChange={(event) => setTuneForm((prev) => ({ ...prev, max_trials: event.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="max trials"
              />
            </div>
            <textarea
              rows={3}
              value={tuneForm.parameter_grid}
              onChange={(event) => setTuneForm((prev) => ({ ...prev, parameter_grid: event.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-xs"
            />
            <button
              type="submit"
              disabled={tuning}
              className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
            >
              {tuning ? '调参中...' : '执行调参'}
            </button>
          </form>
          {tuneResult ? (
            <div className="mt-3 border border-blue-100 bg-blue-50 rounded-lg p-3 text-sm">
              <p className="font-semibold text-blue-900">Best Trial #{tuneResult.best_trial.trial_no}</p>
              <p className="text-blue-900">Backtest ID: {tuneResult.best_trial.backtest_id}</p>
              <p className="text-blue-900">Total Return: {tuneResult.best_trial.total_return.toFixed(4)}%</p>
              <p className="text-blue-900">Sharpe: {tuneResult.best_trial.sharpe_ratio.toFixed(4)}</p>
            </div>
          ) : null}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">复盘报告</h2>
          <form className="space-y-3" onSubmit={handleBuildReport}>
            <input
              value={reportForm.backtest_id}
              onChange={(event) => setReportForm((prev) => ({ ...prev, backtest_id: event.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              placeholder="Backtest ID"
            />
            <textarea
              rows={3}
              value={reportForm.question}
              onChange={(event) => setReportForm((prev) => ({ ...prev, question: event.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
            />
            <button
              type="submit"
              disabled={reporting}
              className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-900 disabled:opacity-50"
            >
              {reporting ? '生成中...' : '生成报告'}
            </button>
          </form>
          {report ? (
            <pre className="mt-3 text-xs bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-auto max-h-96 whitespace-pre-wrap">
              {report.markdown}
            </pre>
          ) : (
            <p className="text-sm text-gray-500 mt-2">暂无报告。</p>
          )}
        </div>
      </div>
    </div>
  );
}
