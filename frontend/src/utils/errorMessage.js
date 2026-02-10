export function getErrorMessage(error, fallback = '操作失败，请稍后重试') {
  if (!error) return fallback;
  if (typeof error === 'string') return error;

  const data = error.response?.data;
  const detail = data?.detail;

  if (Array.isArray(detail)) {
    const first = detail[0];
    if (typeof first === 'string') return first;
    if (first?.msg) return first.msg;
  }

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (typeof data?.message === 'string' && data.message.trim()) {
    return data.message;
  }

  if (error.request && !error.response) {
    return '无法连接后端服务，请确认后端已启动。';
  }

  if (typeof error.message === 'string' && error.message.trim()) {
    return error.message;
  }

  return fallback;
}

