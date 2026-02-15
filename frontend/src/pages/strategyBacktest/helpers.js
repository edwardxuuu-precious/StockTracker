export function todayDateString() {
  return new Date().toISOString().slice(0, 10);
}

export function oneYearAgoDateString() {
  const date = new Date();
  date.setFullYear(date.getFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

export function toNumber(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : NaN;
}

export function fmtCurrency(value) {
  return Number(value || 0).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function fmtPercent(value) {
  const num = Number(value || 0);
  return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
}

export const STRATEGY_FORM_DEFAULTS = {
  name: '',
  description: '',
  strategy_type: 'moving_average',
  short_window: '5',
  long_window: '20',
  rsi_period: '14',
  rsi_buy: '30',
  rsi_sell: '70',
  momentum_period: '10',
  momentum_threshold: '0.015',
};

export function getStrategyHint(strategyType) {
  if (strategyType === 'rsi') {
    return 'RSI 低于买入阈值开仓，高于卖出阈值平仓。';
  }
  if (strategyType === 'momentum') {
    return '动量高于阈值开仓，低于负阈值平仓。';
  }
  return '短均线上穿长均线开仓，下穿平仓。';
}

export function buildStrategyParametersByType(form) {
  const strategyType = form.strategy_type;
  if (strategyType === 'rsi') {
    return {
      rsi_period: Math.max(2, Math.floor(toNumber(form.rsi_period))),
      rsi_buy: toNumber(form.rsi_buy),
      rsi_sell: toNumber(form.rsi_sell),
    };
  }
  if (strategyType === 'momentum') {
    return {
      momentum_period: Math.max(2, Math.floor(toNumber(form.momentum_period))),
      momentum_threshold: toNumber(form.momentum_threshold),
    };
  }
  return {
    short_window: Math.max(2, Math.floor(toNumber(form.short_window))),
    long_window: Math.max(3, Math.floor(toNumber(form.long_window))),
  };
}

export function makeStrategyFormFromRecord(strategy) {
  if (!strategy) return { ...STRATEGY_FORM_DEFAULTS };
  const params = strategy.parameters || {};
  return {
    ...STRATEGY_FORM_DEFAULTS,
    name: String(strategy.name || ''),
    description: String(strategy.description || ''),
    strategy_type: String(strategy.strategy_type || 'moving_average'),
    short_window: String(params.short_window ?? STRATEGY_FORM_DEFAULTS.short_window),
    long_window: String(params.long_window ?? STRATEGY_FORM_DEFAULTS.long_window),
    rsi_period: String(params.rsi_period ?? STRATEGY_FORM_DEFAULTS.rsi_period),
    rsi_buy: String(params.rsi_buy ?? STRATEGY_FORM_DEFAULTS.rsi_buy),
    rsi_sell: String(params.rsi_sell ?? STRATEGY_FORM_DEFAULTS.rsi_sell),
    momentum_period: String(params.momentum_period ?? STRATEGY_FORM_DEFAULTS.momentum_period),
    momentum_threshold: String(params.momentum_threshold ?? STRATEGY_FORM_DEFAULTS.momentum_threshold),
  };
}

export function formatStrategyParameters(strategy) {
  if (!strategy) return '';
  const params = strategy.parameters || {};
  if (strategy.strategy_type === 'rsi') {
    return `RSI周期 ${params.rsi_period ?? '--'} / 买入 ${params.rsi_buy ?? '--'} / 卖出 ${params.rsi_sell ?? '--'}`;
  }
  if (strategy.strategy_type === 'momentum') {
    return `动量周期 ${params.momentum_period ?? '--'} / 阈值 ${params.momentum_threshold ?? '--'}`;
  }
  return `短均线 ${params.short_window ?? '--'} / 长均线 ${params.long_window ?? '--'}`;
}

export function buildBacktestErrorMessage(rawMessage) {
  const message = String(rawMessage || '').trim();
  if (!message) {
    return '回测执行失败，请检查输入后重试。';
  }
  if (message.includes('start_date must be earlier than or equal to end_date')) {
    return [
      '日期范围不正确：开始日期不能晚于结束日期。',
      '请将【开始日期】调整为更早日期，或将【结束日期】调整为同一天或更晚日期。',
    ].join('\n');
  }
  return message;
}
