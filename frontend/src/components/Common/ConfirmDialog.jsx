import { useEffect } from 'react';

export default function ConfirmDialog({
  open,
  title = '确认操作',
  message = '',
  confirmText = '确认',
  cancelText = '取消',
  confirmVariant = 'danger',
  processing = false,
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    if (!open) return undefined;
    const onKeydown = (event) => {
      if (event.key === 'Escape' && !processing) {
        onCancel?.();
      }
    };
    document.addEventListener('keydown', onKeydown);
    return () => document.removeEventListener('keydown', onKeydown);
  }, [open, processing, onCancel]);

  if (!open) return null;

  const confirmClass =
    confirmVariant === 'danger'
      ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
      : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-white shadow-xl">
        <div className="px-6 py-5 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="px-6 py-4">
          <p className="text-sm text-gray-600 leading-6">{message}</p>
        </div>
        <div className="px-6 py-4 flex justify-end gap-3 border-t border-gray-200">
          <button
            type="button"
            onClick={onCancel}
            disabled={processing}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={processing}
            className={`px-4 py-2 rounded-lg text-white focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60 ${confirmClass}`}
          >
            {processing ? '处理中...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

