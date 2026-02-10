const STYLES = {
  error: 'bg-red-50 border-red-200 text-red-700',
  success: 'bg-green-50 border-green-200 text-green-700',
  info: 'bg-blue-50 border-blue-200 text-blue-700',
};

const TITLES = {
  error: '提交未完成',
  success: '操作成功',
  info: '提示信息',
};

export default function NoticeBanner({
  type = 'info',
  title,
  message,
  onClose,
  className = '',
}) {
  if (!message) return null;
  const style = STYLES[type] || STYLES.info;
  const resolvedTitle = title || TITLES[type] || TITLES.info;

  return (
    <div className={`border rounded-2xl p-4 shadow-sm ${style} ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold">{resolvedTitle}</p>
          <p className="mt-1 text-sm leading-6 whitespace-pre-line">{message}</p>
        </div>
        {onClose ? (
          <button
            type="button"
            className="text-current opacity-70 hover:opacity-100 text-lg leading-none"
            onClick={onClose}
            aria-label="关闭提示"
          >
            ×
          </button>
        ) : null}
      </div>
    </div>
  );
}
