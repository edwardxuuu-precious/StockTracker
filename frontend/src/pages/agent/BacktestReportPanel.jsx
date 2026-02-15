export default function BacktestReportPanel({
  reportForm,
  setReportForm,
  reporting,
  report,
  onSubmit,
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">复盘报告</h2>
      <form className="space-y-3" onSubmit={onSubmit}>
        <input
          value={reportForm.backtest_id}
          onChange={(event) => setReportForm((prev) => ({ ...prev, backtest_id: event.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          placeholder="Backtest ID"
        />
        <textarea
          rows={3}
          value={reportForm.question}
          onChange={(event) => setReportForm((prev) => ({ ...prev, question: event.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
        />
        <button
          type="submit"
          disabled={reporting}
          className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-900 disabled:opacity-50"
        >
          {reporting ? '生成中...' : '生成报告'}
        </button>
      </form>
      {report ? (
        <pre className="mt-3 text-xs bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-auto max-h-96 whitespace-pre-wrap">
          {report.markdown}
        </pre>
      ) : (
        <p className="text-sm text-gray-500 mt-2">暂无报告。</p>
      )}
    </div>
  );
}

