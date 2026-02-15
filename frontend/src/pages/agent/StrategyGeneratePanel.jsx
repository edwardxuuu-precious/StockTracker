export default function StrategyGeneratePanel({
  prompt,
  setPrompt,
  generating,
  generated,
  onSubmit,
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">生成策略脚本</h2>
      <form className="space-y-3" onSubmit={onSubmit}>
        <textarea
          rows={4}
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
        />
        <button
          type="submit"
          disabled={generating}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
        >
          {generating ? '生成中...' : '生成并保存'}
        </button>
      </form>
      {generated ? (
        <div className="mt-3 border border-emerald-100 bg-emerald-50 rounded-lg p-3">
          <p className="text-sm text-emerald-900">类型: {generated.detected_strategy_type}</p>
          <p className="text-sm text-emerald-900 mt-1">{generated.rationale}</p>
          <pre className="mt-2 text-xs bg-white border border-emerald-200 rounded p-2 overflow-auto max-h-44">
            {generated.code}
          </pre>
        </div>
      ) : null}
    </div>
  );
}

