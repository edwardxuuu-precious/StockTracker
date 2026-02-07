import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Save, Trash2, X } from 'lucide-react';
import portfolioAPI from '../services/portfolioAPI';
import { addHolding, removeHolding } from '../services/holdingAPI';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import NoticeBanner from '../components/Common/NoticeBanner';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import { getErrorMessage } from '../utils/errorMessage';
import {
  normalizePortfolioName,
  validateHoldingDraft,
  validatePortfolioForm,
} from '../utils/portfolioValidation';

const EMPTY_HOLDING = { symbol: '', quantity: '', average_cost: '' };

function EditPortfolioPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState({ type: '', message: '' });

  const [portfolio, setPortfolio] = useState(null);
  const [existingNames, setExistingNames] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_active: true,
  });
  const [formErrors, setFormErrors] = useState({});

  const [holdings, setHoldings] = useState([]);
  const [newHolding, setNewHolding] = useState(EMPTY_HOLDING);
  const [holdingErrors, setHoldingErrors] = useState({});
  const [pendingRemoveHolding, setPendingRemoveHolding] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError('');

        const [portfolioDetail, portfolios] = await Promise.all([
          portfolioAPI.getPortfolio(id),
          portfolioAPI.getPortfolios(),
        ]);

        setPortfolio(portfolioDetail);
        setFormData({
          name: portfolioDetail.name || '',
          description: portfolioDetail.description || '',
          is_active: portfolioDetail.is_active !== false,
        });
        setHoldings(portfolioDetail.holdings || []);
        setExistingNames(
          portfolios
            .filter((item) => String(item.id) !== String(id))
            .map((item) => item.name || '')
        );
      } catch (err) {
        setError(getErrorMessage(err, '获取组合信息失败'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const canSave = useMemo(() => !saving, [saving]);

  const refreshPortfolio = async () => {
    const data = await portfolioAPI.getPortfolio(id);
    setPortfolio(data);
    setHoldings(data.holdings || []);
    setFormData({
      name: data.name || '',
      description: data.description || '',
      is_active: data.is_active !== false,
    });
  };

  const handleBasicInfoChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'is_active' ? value === 'true' : value,
    }));
    setFormErrors((prev) => ({ ...prev, [name]: '' }));
    if (notice.message) setNotice({ type: '', message: '' });
  };

  const handleUpdateBasicInfo = async () => {
    const errors = validatePortfolioForm(
      { ...formData, initial_capital: '1' },
      { existingNames, currentName: portfolio?.name, requireCapital: false }
    );
    setFormErrors(errors);
    if (Object.keys(errors).length > 0) {
      setNotice({ type: 'error', message: '请先修正表单错误后再保存。' });
      return;
    }

    try {
      setSaving(true);
      await portfolioAPI.updatePortfolio(id, {
        name: normalizePortfolioName(formData.name),
        description: formData.description.trim() || null,
        is_active: formData.is_active,
      });
      await refreshPortfolio();
      setNotice({ type: 'success', message: '组合信息已更新。' });
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err, '更新组合信息失败') });
    } finally {
      setSaving(false);
    }
  };

  const handleAddHolding = async (event) => {
    event.preventDefault();
    const { errors, normalized } = validateHoldingDraft(newHolding);
    if (Object.keys(errors).length > 0) {
      setHoldingErrors(errors);
      return;
    }

    try {
      setSaving(true);
      await addHolding(id, {
        symbol: normalized.symbol,
        quantity: Number(normalized.quantity),
        average_cost: Number(normalized.averageCost),
      });
      setNewHolding(EMPTY_HOLDING);
      setHoldingErrors({});
      await refreshPortfolio();
      setNotice({ type: 'success', message: `持仓 ${normalized.symbol} 已添加。` });
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err, '添加持仓失败') });
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmRemoveHolding = async () => {
    if (!pendingRemoveHolding) return;
    try {
      setSaving(true);
      await removeHolding(id, pendingRemoveHolding.id);
      await refreshPortfolio();
      setPendingRemoveHolding(null);
      setNotice({
        type: 'success',
        message: `持仓 ${pendingRemoveHolding.symbol} 已删除。`,
      });
    } catch (err) {
      setNotice({ type: 'error', message: getErrorMessage(err, '删除持仓失败') });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button
          onClick={() => navigate('/portfolios')}
          className="mt-4 text-blue-600 hover:underline"
        >
          返回组合列表
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={Boolean(pendingRemoveHolding)}
        title="删除持仓"
        message={
          pendingRemoveHolding
            ? `确认删除持仓 ${pendingRemoveHolding.symbol}？`
            : ''
        }
        confirmText="确认删除"
        cancelText="取消"
        confirmVariant="danger"
        processing={saving}
        onCancel={() => {
          if (!saving) setPendingRemoveHolding(null);
        }}
        onConfirm={handleConfirmRemoveHolding}
      />

      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">编辑组合</h1>
        <button
          onClick={() => navigate(`/portfolios/${id}`)}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900"
        >
          <X className="w-5 h-5" />
          返回
        </button>
      </div>

      <NoticeBanner
        type={notice.type || 'error'}
        message={notice.message}
        onClose={() => setNotice({ type: '', message: '' })}
      />

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">基本信息</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              组合名称
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleBasicInfoChange}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                formErrors.name ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {formErrors.name ? (
              <p className="mt-1 text-sm text-red-600">{formErrors.name}</p>
            ) : null}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              描述
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleBasicInfoChange}
              rows={3}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                formErrors.description ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
              <span>{formData.description.length}/200</span>
              {formErrors.description ? (
                <span className="text-red-600">{formErrors.description}</span>
              ) : null}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              组合状态
            </label>
            <select
              name="is_active"
              value={formData.is_active ? 'true' : 'false'}
              onChange={handleBasicInfoChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="true">活跃</option>
              <option value="false">停用</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              停用后可在列表中通过“仅停用”筛选查看。
            </p>
          </div>

          <button
            onClick={handleUpdateBasicInfo}
            disabled={!canSave}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-5 h-5" />
            保存基本信息
          </button>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">持仓管理</h2>

        {holdings.length > 0 ? (
          <div className="mb-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    股票代码
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    数量
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    平均成本
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    市值
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {holdings.map((holding) => (
                  <tr key={holding.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {holding.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {holding.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${holding.average_cost.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${holding.market_value.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() =>
                          setPendingRemoveHolding({ id: holding.id, symbol: holding.symbol })
                        }
                        disabled={saving}
                        className="text-red-600 hover:text-red-800 disabled:opacity-50"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 mb-6">暂无持仓</p>
        )}

        <form onSubmit={handleAddHolding} className="border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">添加新持仓</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                股票代码
              </label>
              <input
                type="text"
                value={newHolding.symbol}
                onChange={(event) => {
                  setNewHolding((prev) => ({ ...prev, symbol: event.target.value }));
                  setHoldingErrors((prev) => ({ ...prev, symbol: '' }));
                }}
                placeholder="例如: AAPL"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  holdingErrors.symbol ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {holdingErrors.symbol ? (
                <p className="mt-1 text-xs text-red-600">{holdingErrors.symbol}</p>
              ) : null}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                数量
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={newHolding.quantity}
                onChange={(event) => {
                  setNewHolding((prev) => ({ ...prev, quantity: event.target.value }));
                  setHoldingErrors((prev) => ({ ...prev, quantity: '' }));
                }}
                placeholder="10"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  holdingErrors.quantity ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {holdingErrors.quantity ? (
                <p className="mt-1 text-xs text-red-600">{holdingErrors.quantity}</p>
              ) : null}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                平均成本
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={newHolding.average_cost}
                onChange={(event) => {
                  setNewHolding((prev) => ({ ...prev, average_cost: event.target.value }));
                  setHoldingErrors((prev) => ({ ...prev, average_cost: '' }));
                }}
                placeholder="150.00"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  holdingErrors.average_cost ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {holdingErrors.average_cost ? (
                <p className="mt-1 text-xs text-red-600">{holdingErrors.average_cost}</p>
              ) : null}
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="mt-4 flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            <Plus className="w-5 h-5" />
            添加持仓
          </button>
        </form>
      </div>

      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">组合信息</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">初始资金:</span>
            <span className="ml-2 font-medium">${portfolio?.initial_capital.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-gray-500">现金余额:</span>
            <span className="ml-2 font-medium">${portfolio?.cash_balance.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-gray-500">持仓数量:</span>
            <span className="ml-2 font-medium">{holdings.length}</span>
          </div>
          <div>
            <span className="text-gray-500">组合ID:</span>
            <span className="ml-2 font-medium">#{portfolio?.id}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EditPortfolioPage;
