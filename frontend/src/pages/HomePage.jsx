import { TrendingUp, Briefcase, MessageSquare, LineChart } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          欢迎使用 StockTracker
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          基于 AI 的智能股票组合管理与交易策略系统
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Link
          to="/portfolios"
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mb-4">
            <Briefcase className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">组合管理</h3>
          <p className="text-gray-600 text-sm">
            创建和管理您的股票投资组合,实时跟踪表现
          </p>
        </Link>

        <Link
          to="/chat"
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mb-4">
            <MessageSquare className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">AI 助手</h3>
          <p className="text-gray-600 text-sm">
            通过自然语言与 AI 对话,轻松创建投资策略
          </p>
        </Link>

        <Link
          to="/strategies"
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mb-4">
            <TrendingUp className="h-6 w-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">交易策略</h3>
          <p className="text-gray-600 text-sm">
            设计和测试各种交易策略,优化投资收益
          </p>
        </Link>

        <Link
          to="/analytics"
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-center w-12 h-12 bg-orange-100 rounded-lg mb-4">
            <LineChart className="h-6 w-6 text-orange-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">数据分析</h3>
          <p className="text-gray-600 text-sm">
            查看收益拆解、持仓分布和月度表现,并支持导出 CSV 报表
          </p>
        </Link>
      </div>

      {/* Quick Stats (Placeholder) */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">快速开始</h2>
        <div className="space-y-3 text-gray-600">
          <p>
            ✨ <strong>第一步:</strong> 点击"组合管理"创建您的第一个投资组合
          </p>
          <p>
            🤖 <strong>第二步:</strong> 使用"AI 助手"通过自然语言创建策略
          </p>
          <p>
            📊 <strong>第三步:</strong> 在"数据分析"中复盘组合收益和交易表现
          </p>
        </div>
      </div>
    </div>
  );
}
