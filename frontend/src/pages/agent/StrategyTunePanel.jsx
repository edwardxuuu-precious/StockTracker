export default function StrategyTunePanel({
  strategies,
  tuneForm,
  setTuneForm,
  tuning,
  tuneResult,
  onSubmit,
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">自动调参</h2>
      <form className="space-y-3" onSubmit={onSubmit}>
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
  );
}

