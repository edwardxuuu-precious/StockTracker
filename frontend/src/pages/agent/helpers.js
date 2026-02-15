export function defaultDateRange() {
  const end = new Date();
  const start = new Date();
  start.setMonth(start.getMonth() - 3);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

export function createDefaultTuneForm(dates) {
  return {
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
  };
}

export function createDefaultReportForm() {
  return {
    backtest_id: '',
    question: '如何降低回撤？',
  };
}

