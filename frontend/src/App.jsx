import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Layout from './components/Common/Layout';
import HomePage from './pages/HomePage';
import PortfoliosPage from './pages/PortfoliosPage';
import CreatePortfolioPage from './pages/CreatePortfolioPage';
import PortfolioDetailPage from './pages/PortfolioDetailPage';
import EditPortfolioPage from './pages/EditPortfolioPage';
import DataAnalysisPage from './pages/DataAnalysisPage';
import StrategyBacktestPage from './pages/StrategyBacktestPage';
import MarketDataPage from './pages/MarketDataPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import AgentPage from './pages/AgentPage';
import StrategyVersionsPage from './pages/StrategyVersionsPage';
function NavTelemetry() {
  const location = useLocation();

  useEffect(() => {
    const payload = {
      path: `${location.pathname}${location.search}`,
      ts: Date.now(),
    };

    fetch(`/api/v1/telemetry/nav`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {});
  }, [location.pathname, location.search]);

  return null;
}

function App() {
  useEffect(() => {
    const handler = (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const clickable = target.closest('a,button,[role="button"]');
      if (!clickable) return;

      const label = (clickable.textContent || '').trim().slice(0, 80);
      const href = clickable.getAttribute('href') || '';
      const payload = {
        path: `${window.location.pathname}${window.location.search}`,
        label,
        href,
        ts: Date.now(),
      };

      fetch(`/api/v1/telemetry/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(() => {});
    };

    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
  }, []);

  return (
    <BrowserRouter>
      <NavTelemetry />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="portfolios" element={<PortfoliosPage />} />
          <Route path="portfolios/new" element={<CreatePortfolioPage />} />
          <Route path="portfolios/:id" element={<PortfolioDetailPage />} />
          <Route path="portfolios/:id/edit" element={<EditPortfolioPage />} />

          <Route path="chat" element={<AgentPage />} />
          <Route path="strategies" element={<StrategyBacktestPage />} />
          <Route path="strategy-versions" element={<StrategyVersionsPage />} />
          <Route path="market-data" element={<MarketDataPage />} />
          <Route path="knowledge-base" element={<KnowledgeBasePage />} />
          <Route path="analytics" element={<DataAnalysisPage />} />
          <Route path="backtests" element={<DataAnalysisPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
