import { useMemo, useState } from 'react';
import { usePortfolios, useDeletePortfolio } from '../hooks/usePortfolio';
import { Link } from 'react-router-dom';
import { Plus, Trash2, Briefcase, Search } from 'lucide-react';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { format } from 'date-fns';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';

export default function PortfoliosPage() {
  const { portfolios, loading, error } = usePortfolios();
  const { deletePortfolio } = useDeletePortfolio();
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [actionError, setActionError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(null);

  const filteredPortfolios = useMemo(() => {
    const keyword = searchText.trim().toLowerCase();
    return portfolios.filter((portfolio) => {
      if (statusFilter === 'active' && !portfolio.is_active) return false;
      if (statusFilter === 'inactive' && portfolio.is_active) return false;

      if (!keyword) return true;
      const name = String(portfolio.name || '').toLowerCase();
      const description = String(portfolio.description || '').toLowerCase();
      return name.includes(keyword) || description.includes(keyword);
    });
  }, [portfolios, searchText, statusFilter]);

  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;
    try {
      setDeleting(true);
      setActionError('');
      await deletePortfolio(pendingDelete.id);
      setPendingDelete(null);
    } catch (err) {
      setActionError(getErrorMessage(err, '删除组合失败'));
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        错误: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="删除投资组合"
        message={
          pendingDelete
            ? `确认删除组合 "${pendingDelete.name}"？此操作不可撤销。`
            : ''
        }
        confirmText="确认删除"
        cancelText="取消"
        confirmVariant="danger"
        processing={deleting}
        onCancel={() => {
          if (!deleting) setPendingDelete(null);
        }}
        onConfirm={handleConfirmDelete}
      />

      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">我的投资组合</h1>
        <Link
          to="/portfolios/new"
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-5 w-5" />
          <span>创建组合</span>
        </Link>
      </div>

      <NoticeBanner
        type="error"
        message={actionError}
        onClose={() => setActionError('')}
      />

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="md:col-span-2 relative">
            <Search className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="搜索组合名称或描述"
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">全部状态</option>
            <option value="active">仅活跃</option>
            <option value="inactive">仅停用</option>
          </select>
        </div>
      </div>

      {/* Portfolio List */}
      {portfolios.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Briefcase className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            还没有投资组合
          </h3>
          <p className="text-gray-600 mb-6">
            创建您的第一个投资组合,开始追踪股票表现
          </p>
          <Link
            to="/portfolios/new"
            className="inline-flex items-center space-x-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-5 w-5" />
            <span>创建组合</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPortfolios.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-10 text-center">
              <p className="text-gray-700 font-medium">没有匹配的组合</p>
              <p className="text-sm text-gray-500 mt-2">
                尝试修改搜索关键词或筛选条件。
              </p>
            </div>
          ) : null}

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPortfolios.map((portfolio) => {
            const isActive = portfolio.is_active !== false;
            return (
            <div
              key={portfolio.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <Link
                    to={`/portfolios/${portfolio.id}`}
                    className="text-lg font-semibold text-gray-900 hover:text-blue-600"
                  >
                    {portfolio.name}
                  </Link>
                  {portfolio.description && (
                    <p className="text-sm text-gray-600 mt-1">
                      {portfolio.description}
                    </p>
                  )}
                  <div className="mt-2">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        isActive
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {isActive ? '活跃' : '停用'}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() =>
                    setPendingDelete({ id: portfolio.id, name: portfolio.name })
                  }
                  className="text-gray-400 hover:text-red-600 transition-colors"
                  title="删除"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">当前价值</span>
                  <span className="text-lg font-semibold text-gray-900">
                    ${portfolio.current_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">初始资金</span>
                  <span className="text-sm text-gray-900">
                    ${portfolio.initial_capital.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">现金余额</span>
                  <span className="text-sm text-gray-900">
                    ${portfolio.cash_balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>

                {portfolio.holdings && portfolio.holdings.length > 0 && (
                  <div className="pt-3 border-t border-gray-200">
                    <span className="text-sm text-gray-600">
                      持仓数量: {portfolio.holdings.length}
                    </span>
                  </div>
                )}

                <div className="text-xs text-gray-500 pt-2">
                  创建于 {format(new Date(portfolio.created_at), 'yyyy-MM-dd')}
                </div>
              </div>

              <Link
                to={`/portfolios/${portfolio.id}`}
                className="mt-4 block text-center text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                查看详情 →
              </Link>
            </div>
            );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
