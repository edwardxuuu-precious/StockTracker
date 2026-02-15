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
import BacktestReportPanel from './agent/BacktestReportPanel';
import ChatAssistantPanel from './agent/ChatAssistantPanel';
import StrategyGeneratePanel from './agent/StrategyGeneratePanel';
import StrategyTunePanel from './agent/StrategyTunePanel';
import { createDefaultReportForm, createDefaultTuneForm, defaultDateRange } from './agent/helpers';

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
  const [tuneForm, setTuneForm] = useState(() => createDefaultTuneForm(dates));

  const [reporting, setReporting] = useState(false);
  const [reportForm, setReportForm] = useState(createDefaultReportForm);
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
        <p className="text-gray-600 mt-1">自然语言生成策略、自动调参、回测复盘。</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <ChatAssistantPanel
          messages={messages}
          chatText={chatText}
          setChatText={setChatText}
          sending={sending}
          onSubmit={handleSendChat}
        />
        <StrategyGeneratePanel
          prompt={prompt}
          setPrompt={setPrompt}
          generating={generating}
          generated={generated}
          onSubmit={handleGenerate}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <StrategyTunePanel
          strategies={strategies}
          tuneForm={tuneForm}
          setTuneForm={setTuneForm}
          tuning={tuning}
          tuneResult={tuneResult}
          onSubmit={handleTune}
        />
        <BacktestReportPanel
          reportForm={reportForm}
          setReportForm={setReportForm}
          reporting={reporting}
          report={report}
          onSubmit={handleBuildReport}
        />
      </div>
    </div>
  );
}

