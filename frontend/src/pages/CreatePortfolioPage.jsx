import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, X } from 'lucide-react';
import { useCreatePortfolio } from '../hooks/usePortfolio';
import portfolioAPI from '../services/portfolioAPI';
import NoticeBanner from '../components/Common/NoticeBanner';
import { getErrorMessage } from '../utils/errorMessage';
import {
  normalizePortfolioName,
  validateHoldingDraft,
  validatePortfolioForm,
} from '../utils/portfolioValidation';

const EMPTY_HOLDING = { symbol: '', quantity: '', average_cost: '' };

export default function CreatePortfolioPage() {
  const navigate = useNavigate();
  const { createPortfolio } = useCreatePortfolio();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    initial_capital: '',
    holdings: [],
  });
  const [newHolding, setNewHolding] = useState(EMPTY_HOLDING);
  const [existingNames, setExistingNames] = useState([]);
  const [formErrors, setFormErrors] = useState({});
  const [holdingErrors, setHoldingErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState({ type: '', message: '' });

  useEffect(() => {
    const fetchNames = async () => {
      try {
        const portfolios = await portfolioAPI.getPortfolios();
        setExistingNames(portfolios.map((item) => item.name || ''));
      } catch (err) {
        setNotice({ type: 'error', message: getErrorMessage(err, '获取组合列表失败，暂时无法校验重名') });
      }
    };
    fetchNames();
  }, []);

  const canSubmit = useMemo(() => !submitting, [submitting]);

  const updateField = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    setFormErrors((prev) => ({ ...prev, [key]: '' }));
    if (notice.message) setNotice({ type: '', message: '' });
  };

  const handleAddHolding = () => {
    const { errors, normalized } = validateHoldingDraft(newHolding);
    if (Object.keys(errors).length > 0) {
      setHoldingErrors(errors);
      return;
    }

    setFormData((prev) => ({
      ...prev,
      holdings: [
        ...prev.holdings,
        {
          symbol: normalized.symbol,
          quantity: Number(normalized.quantity),
          average_cost: Number(normalized.averageCost),
        },
      ],
    }));
    setHoldingErrors({});
    setNewHolding(EMPTY_HOLDING);
  };

  const handleRemoveHolding = (index) => {
    setFormData((prev) => ({
      ...prev,
      holdings: prev.holdings.filter((_, currentIndex) => currentIndex !== index),
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setNotice({ type: '', message: '' });

    const errors = validatePortfolioForm(formData, {
      existingNames,
      requireCapital: true,
    });
    setFormErrors(errors);

    if (Object.keys(errors).length > 0) {
      setNotice({ type: 'error', message: '请先修正表单错误后再提交。' });
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: normalizePortfolioName(formData.name),
        description: formData.description.trim() || null,
        initial_capital: Number(formData.initial_capital),
        holdings: formData.holdings,
      };

      const created = await createPortfolio(payload);
      navigate(`/portfolios/${created.id}`);
    } catch (err) {
      setNotice({
        type: 'error',
        message: getErrorMessage(err, '创建组合失败，请稍后重试'),
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">创建投资组合</h1>
        <p className="text-gray-600 mt-2">填写以下信息创建新的投资组合</p>
      </div>

      <NoticeBanner
        type={notice.type || 'error'}
        message={notice.message}
        onClose={() => setNotice({ type: '', message: '' })}
        className="mb-6"
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                组合名称 *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(event) => updateField('name', event.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  formErrors.name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="例如: 科技股成长组合"
              />
              {formErrors.name ? (
                <p className="mt-1 text-sm text-red-600">{formErrors.name}</p>
              ) : null}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                描述
              </label>
              <textarea
                value={formData.description}
                onChange={(event) => updateField('description', event.target.value)}
                rows={3}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  formErrors.description ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="简要描述这个投资组合的目标和策略"
              />
              <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
                <span>{formData.description.length}/200</span>
                {formErrors.description ? (
                  <span className="text-red-600">{formErrors.description}</span>
                ) : null}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                初始资金 ($) *
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={formData.initial_capital}
                onChange={(event) => updateField('initial_capital', event.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  formErrors.initial_capital ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="10000.00"
              />
              {formErrors.initial_capital ? (
                <p className="mt-1 text-sm text-red-600">{formErrors.initial_capital}</p>
              ) : null}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            初始持仓 (可选)
          </h2>

          {formData.holdings.length > 0 ? (
            <div className="mb-4 space-y-2">
              {formData.holdings.map((holding, index) => (
                <div
                  key={`${holding.symbol}-${index}`}
                  className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
                >
                  <div className="flex space-x-4 text-sm">
                    <span className="font-medium">{holding.symbol}</span>
                    <span className="text-gray-600">数量: {holding.quantity}</span>
                    <span className="text-gray-600">成本: ${holding.average_cost}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveHolding(index)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          ) : null}

          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <input
                  type="text"
                  placeholder="股票代码"
                  value={newHolding.symbol}
                  onChange={(event) => {
                    setNewHolding((prev) => ({ ...prev, symbol: event.target.value }));
                    setHoldingErrors((prev) => ({ ...prev, symbol: '' }));
                  }}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    holdingErrors.symbol ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {holdingErrors.symbol ? (
                  <p className="mt-1 text-xs text-red-600">{holdingErrors.symbol}</p>
                ) : null}
              </div>
              <div>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="数量"
                  value={newHolding.quantity}
                  onChange={(event) => {
                    setNewHolding((prev) => ({ ...prev, quantity: event.target.value }));
                    setHoldingErrors((prev) => ({ ...prev, quantity: '' }));
                  }}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    holdingErrors.quantity ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {holdingErrors.quantity ? (
                  <p className="mt-1 text-xs text-red-600">{holdingErrors.quantity}</p>
                ) : null}
              </div>
              <div>
                <input
                  type="text"
                  inputMode="decimal"
                  placeholder="平均成本"
                  value={newHolding.average_cost}
                  onChange={(event) => {
                    setNewHolding((prev) => ({ ...prev, average_cost: event.target.value }));
                    setHoldingErrors((prev) => ({ ...prev, average_cost: '' }));
                  }}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    holdingErrors.average_cost ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {holdingErrors.average_cost ? (
                  <p className="mt-1 text-xs text-red-600">{holdingErrors.average_cost}</p>
                ) : null}
              </div>
            </div>
            <button
              type="button"
              onClick={handleAddHolding}
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 font-medium text-sm"
            >
              <Plus className="h-4 w-4" />
              <span>添加持仓</span>
            </button>
          </div>
        </div>

        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={!canSubmit}
            className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {submitting ? '创建中...' : '创建组合'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/portfolios')}
            className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            取消
          </button>
        </div>
      </form>
    </div>
  );
}

