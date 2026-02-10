const NAME_PATTERN = /^[A-Za-z0-9\u4e00-\u9fa5 _\-()]+$/;
const SYMBOL_PATTERN = /^[A-Za-z0-9._-]{1,20}$/;

function isDecimalWithMaxScale(value, maxScale) {
  return new RegExp(`^\\d+(\\.\\d{1,${maxScale}})?$`).test(value);
}

export function normalizePortfolioName(name) {
  return String(name || '').trim().replace(/\s+/g, ' ');
}

export function validatePortfolioName(name, existingNames = [], currentName = '') {
  const normalized = normalizePortfolioName(name);
  if (!normalized) return '请输入组合名称';
  if (normalized.length < 2) return '组合名称至少 2 个字符';
  if (normalized.length > 50) return '组合名称不能超过 50 个字符';
  if (!NAME_PATTERN.test(normalized)) {
    return '组合名称仅支持中文、英文、数字、空格、下划线、横线和括号';
  }

  const normalizedCurrent = normalizePortfolioName(currentName).toLowerCase();
  const exists = existingNames.some((item) => {
    const normalizedItem = normalizePortfolioName(item).toLowerCase();
    return normalizedItem && normalizedItem === normalized.toLowerCase();
  });

  if (exists && normalized.toLowerCase() !== normalizedCurrent) {
    return '组合名称已存在，请使用其他名称';
  }

  return '';
}

export function validateDescription(description) {
  const value = String(description || '');
  if (value.length > 200) return '描述不能超过 200 个字符';
  return '';
}

export function validateInitialCapital(value) {
  const text = String(value || '').trim();
  if (!text) return '请输入初始资金';
  if (!isDecimalWithMaxScale(text, 2)) return '初始资金最多保留 2 位小数';

  const parsed = Number(text);
  if (!Number.isFinite(parsed) || parsed <= 0) return '初始资金必须大于 0';
  return '';
}

export function validatePortfolioForm(formData, options = {}) {
  const { existingNames = [], currentName = '', requireCapital = false } = options;
  const errors = {};

  const nameError = validatePortfolioName(formData.name, existingNames, currentName);
  if (nameError) errors.name = nameError;

  const descriptionError = validateDescription(formData.description);
  if (descriptionError) errors.description = descriptionError;

  if (requireCapital) {
    const capitalError = validateInitialCapital(formData.initial_capital);
    if (capitalError) errors.initial_capital = capitalError;
  }

  return errors;
}

export function validateHoldingDraft(holding) {
  const errors = {};
  const symbol = String(holding.symbol || '').trim().toUpperCase();
  const quantity = String(holding.quantity || '').trim();
  const averageCost = String(holding.average_cost || '').trim();

  if (!symbol) errors.symbol = '请输入股票代码';
  else if (!SYMBOL_PATTERN.test(symbol)) errors.symbol = '股票代码格式不正确';

  if (!quantity) errors.quantity = '请输入数量';
  else if (!isDecimalWithMaxScale(quantity, 4)) errors.quantity = '数量最多保留 4 位小数';
  else if (Number(quantity) <= 0) errors.quantity = '数量必须大于 0';

  if (!averageCost) errors.average_cost = '请输入平均成本';
  else if (!isDecimalWithMaxScale(averageCost, 2)) errors.average_cost = '平均成本最多保留 2 位小数';
  else if (Number(averageCost) <= 0) errors.average_cost = '平均成本必须大于 0';

  return { errors, normalized: { symbol, quantity, averageCost } };
}

