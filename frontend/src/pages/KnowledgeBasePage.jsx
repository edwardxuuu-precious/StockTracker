import { useCallback, useEffect, useState } from 'react';
import { FileSearch, UploadCloud } from 'lucide-react';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';
import {
  ingestKbFile,
  ingestKbText,
  listKbDocuments,
  searchKb,
} from '../services/knowledgeBaseAPI';

export default function KnowledgeBasePage() {
  const [notice, setNotice] = useState({ type: '', message: '' });
  const [uploading, setUploading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const [file, setFile] = useState(null);
  const [fileTitle, setFileTitle] = useState('');
  const [textForm, setTextForm] = useState({
    sourceName: '',
    sourceType: 'txt',
    title: '',
    content: '',
  });

  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('hybrid');
  const [hits, setHits] = useState([]);
  const [documents, setDocuments] = useState([]);

  const loadDocuments = useCallback(async () => {
    try {
      setLoadingDocs(true);
      const data = await listKbDocuments({ limit: 50 });
      setDocuments(data || []);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '加载知识库文档失败') });
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleUploadFile = async (event) => {
    event.preventDefault();
    if (!file) {
      setNotice({ type: 'error', message: '请选择要上传的文件' });
      return;
    }
    try {
      setUploading(true);
      const data = await ingestKbFile({ file, title: fileTitle || undefined });
      setNotice({
        type: 'success',
        message: `文件已入库: ${data.document.source_name} (chunks: ${data.chunk_count})`,
      });
      setFile(null);
      setFileTitle('');
      loadDocuments();
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '文件入库失败') });
    } finally {
      setUploading(false);
    }
  };

  const handleUploadText = async (event) => {
    event.preventDefault();
    if (!textForm.sourceName || !textForm.content) {
      setNotice({ type: 'error', message: '请输入资料名称和内容' });
      return;
    }
    try {
      setUploading(true);
      const data = await ingestKbText({
        sourceName: textForm.sourceName,
        sourceType: textForm.sourceType,
        title: textForm.title || undefined,
        content: textForm.content,
      });
      setNotice({
        type: 'success',
        message: `文本已入库: ${data.document.source_name} (chunks: ${data.chunk_count})`,
      });
      setTextForm({ sourceName: '', sourceType: 'txt', title: '', content: '' });
      loadDocuments();
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '文本入库失败') });
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async (event) => {
    event.preventDefault();
    if (!query.trim()) {
      setNotice({ type: 'error', message: '请输入检索问题' });
      return;
    }
    try {
      setSearching(true);
      const data = await searchKb({ query: query.trim(), top_k: 6, mode });
      setHits(data.hits || []);
    } catch (error) {
      setNotice({ type: 'error', message: getErrorMessage(error, '检索失败') });
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      <NoticeBanner
        type={notice.type || 'info'}
        message={notice.message}
        onClose={() => setNotice({ type: '', message: '' })}
      />

      <div>
        <h1 className="text-3xl font-bold text-gray-900">知识库</h1>
        <p className="text-gray-600 mt-1">导入资料并进行检索，供策略复盘与参数优化使用。</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <UploadCloud className="h-4 w-4 text-emerald-600" />
            <h2 className="text-lg font-semibold text-gray-900">上传资料</h2>
          </div>
          <form className="space-y-3" onSubmit={handleUploadFile}>
            <div>
              <label className="block text-xs text-gray-600 mb-1">选择文件（PDF/TXT/JSON）</label>
              <input
                type="file"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">标题（可选）</label>
              <input
                value={fileTitle}
                onChange={(event) => setFileTitle(event.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <button
              type="submit"
              disabled={uploading}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {uploading ? '入库中...' : '上传并入库'}
            </button>
          </form>

          <div className="border-t border-gray-100 pt-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">快速文本入库</h3>
            <form className="space-y-3" onSubmit={handleUploadText}>
              <div>
                <label className="block text-xs text-gray-600 mb-1">资料名称</label>
                <input
                  value={textForm.sourceName}
                  onChange={(event) => setTextForm((prev) => ({ ...prev, sourceName: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">类型</label>
                  <select
                    value={textForm.sourceType}
                    onChange={(event) => setTextForm((prev) => ({ ...prev, sourceType: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
                  >
                    <option value="txt">txt</option>
                    <option value="json">json</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">标题</label>
                  <input
                    value={textForm.title}
                    onChange={(event) => setTextForm((prev) => ({ ...prev, title: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">内容</label>
                <textarea
                  rows={4}
                  value={textForm.content}
                  onChange={(event) => setTextForm((prev) => ({ ...prev, content: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
                />
              </div>
              <button
                type="submit"
                disabled={uploading}
                className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-900 disabled:opacity-50"
              >
                {uploading ? '入库中...' : '保存文本'}
              </button>
            </form>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <FileSearch className="h-4 w-4 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">知识库检索</h2>
          </div>
          <form className="space-y-3" onSubmit={handleSearch}>
            <div>
              <label className="block text-xs text-gray-600 mb-1">问题 / 关键词</label>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">检索模式</label>
                <select
                  value={mode}
                  onChange={(event) => setMode(event.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
                >
                  <option value="hybrid">hybrid</option>
                  <option value="fts">fts</option>
                  <option value="vector">vector</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={searching}
                  className="w-full px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
                >
                  {searching ? '检索中...' : '检索'}
                </button>
              </div>
            </div>
          </form>

          {hits.length ? (
            <div className="space-y-3">
              {hits.map((hit) => (
                <div key={hit.chunk.id} className="border border-blue-100 bg-blue-50 rounded-lg p-3">
                  <div className="text-xs text-blue-800 font-semibold">
                    {hit.document.source_name} · score {hit.score.toFixed(4)}
                  </div>
                  <p className="text-sm text-blue-900 mt-1 whitespace-pre-line">
                    {hit.chunk.content}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">暂无检索结果。</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">已入库文档</h2>
          <button
            type="button"
            onClick={loadDocuments}
            disabled={loadingDocs}
            className="px-3 py-2 border border-slate-300 text-slate-700 rounded-lg hover:border-slate-400 disabled:opacity-50"
          >
            {loadingDocs ? '加载中...' : '刷新列表'}
          </button>
        </div>
        {documents.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-3 py-2 text-left">名称</th>
                  <th className="px-3 py-2 text-left">类型</th>
                  <th className="px-3 py-2 text-left">标题</th>
                  <th className="px-3 py-2 text-left">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td className="px-3 py-2 text-gray-900">{doc.source_name}</td>
                    <td className="px-3 py-2 text-gray-700">{doc.source_type}</td>
                    <td className="px-3 py-2 text-gray-700">{doc.title || '--'}</td>
                    <td className="px-3 py-2 text-gray-600">{doc.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">尚无文档记录。</p>
        )}
      </div>
    </div>
  );
}
