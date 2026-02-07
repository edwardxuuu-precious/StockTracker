import test from 'node:test';
import assert from 'node:assert/strict';
import { getErrorMessage } from './errorMessage.js';

test('getErrorMessage prefers API detail string', () => {
  const error = { response: { data: { detail: '后端错误详情' } } };
  assert.equal(getErrorMessage(error), '后端错误详情');
});

test('getErrorMessage handles validation detail array', () => {
  const error = {
    response: {
      data: {
        detail: [{ msg: '字段校验失败' }],
      },
    },
  };
  assert.equal(getErrorMessage(error), '字段校验失败');
});

test('getErrorMessage handles network failures', () => {
  const error = { request: {}, message: 'Network Error' };
  assert.equal(getErrorMessage(error), '无法连接后端服务，请确认后端已启动。');
});

test('getErrorMessage falls back to message and fallback text', () => {
  assert.equal(getErrorMessage({ message: '普通错误' }), '普通错误');
  assert.equal(getErrorMessage(null, '兜底文案'), '兜底文案');
});

