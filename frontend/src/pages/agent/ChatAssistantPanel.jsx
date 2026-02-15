export default function ChatAssistantPanel({
  messages,
  chatText,
  setChatText,
  sending,
  onSubmit,
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">会话助手</h2>
      <div className="border border-gray-200 rounded-lg p-3 h-72 overflow-auto bg-gray-50">
        {messages.length ? messages.map((item) => (
          <div key={item.id} className="mb-2 text-sm">
            <span className={`font-semibold ${item.role === 'assistant' ? 'text-blue-700' : 'text-gray-900'}`}>
              {item.role === 'assistant' ? 'Agent' : 'You'}:
            </span>
            <span className="ml-2 text-gray-700 whitespace-pre-line">{item.content}</span>
          </div>
        )) : <p className="text-sm text-gray-500">暂无消息。</p>}
      </div>
      <form className="mt-3 flex gap-2" onSubmit={onSubmit}>
        <input
          value={chatText}
          onChange={(event) => setChatText(event.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
          placeholder="输入：请生成一个 RSI 策略"
        />
        <button
          type="submit"
          disabled={sending}
          className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
        >
          {sending ? '发送中...' : '发送'}
        </button>
      </form>
    </div>
  );
}

