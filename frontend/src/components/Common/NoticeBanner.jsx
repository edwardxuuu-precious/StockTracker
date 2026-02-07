const STYLES = {
  error: 'bg-red-50 border-red-200 text-red-700',
  success: 'bg-green-50 border-green-200 text-green-700',
  info: 'bg-blue-50 border-blue-200 text-blue-700',
};

export default function NoticeBanner({ type = 'info', message, onClose, className = '' }) {
  if (!message) return null;
  const style = STYLES[type] || STYLES.info;

  return (
    <div className={`border rounded-lg p-4 ${style} ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm leading-6">{message}</p>
        {onClose ? (
          <button
            type="button"
            className="text-current opacity-70 hover:opacity-100"
            onClick={onClose}
            aria-label="关闭提示"
          >
            x
          </button>
        ) : null}
      </div>
    </div>
  );
}

