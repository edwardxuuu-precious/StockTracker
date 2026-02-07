import test from 'node:test';
import assert from 'node:assert/strict';
import {
  normalizePortfolioName,
  validateHoldingDraft,
  validateInitialCapital,
  validatePortfolioForm,
  validatePortfolioName,
} from './portfolioValidation.js';

test('normalizePortfolioName trims and collapses spaces', () => {
  assert.equal(normalizePortfolioName('  My   Portfolio  '), 'My Portfolio');
});

test('validatePortfolioName detects duplicates', () => {
  const message = validatePortfolioName('Alpha', ['alpha']);
  assert.equal(message, '组合名称已存在，请使用其他名称');
});

test('validateInitialCapital enforces decimal scale and positive value', () => {
  assert.equal(validateInitialCapital('12.345'), '初始资金最多保留 2 位小数');
  assert.equal(validateInitialCapital('0'), '初始资金必须大于 0');
  assert.equal(validateInitialCapital('100.50'), '');
});

test('validatePortfolioForm returns field errors for invalid create payload', () => {
  const errors = validatePortfolioForm(
    {
      name: '@@',
      description: 'x'.repeat(201),
      initial_capital: '12.345',
    },
    { requireCapital: true }
  );

  assert.equal(errors.name, '组合名称仅支持中文、英文、数字、空格、下划线、横线和括号');
  assert.equal(errors.description, '描述不能超过 200 个字符');
  assert.equal(errors.initial_capital, '初始资金最多保留 2 位小数');
});

test('validateHoldingDraft validates and normalizes holding input', () => {
  const invalid = validateHoldingDraft({
    symbol: '',
    quantity: '1.23456',
    average_cost: '-1',
  });
  assert.equal(invalid.errors.symbol, '请输入股票代码');
  assert.equal(invalid.errors.quantity, '数量最多保留 4 位小数');
  assert.equal(invalid.errors.average_cost, '平均成本最多保留 2 位小数');

  const valid = validateHoldingDraft({
    symbol: 'aapl',
    quantity: '2.5',
    average_cost: '123.45',
  });
  assert.deepEqual(valid.errors, {});
  assert.equal(valid.normalized.symbol, 'AAPL');
  assert.equal(valid.normalized.quantity, '2.5');
  assert.equal(valid.normalized.averageCost, '123.45');
});

