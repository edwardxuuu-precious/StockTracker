# Project Cleaner Skill 创建完成 ✅

## 📦 已创建的文件

### Skill 核心文件 (.claude-code/skills/project-cleaner/)
```
✅ skill.json       - Skill 配置文件（触发器、规则、模式）
✅ index.py         - 主程序（核心清理逻辑）
✅ test.py          - 测试套件（5个单元测试）
✅ README.md        - 完整使用文档
✅ QUICKREF.md      - 快速参考卡
```

### 便捷工具（项目根目录）
```
✅ run_cleaner.bat  - Windows 批处理启动器
```

## 🎯 核心功能

### 1️⃣ 重复文件检测
- 使用 MD5 哈希算法检测完全相同的文件
- 自动识别重复文件组
- 建议保留一份，删除其他副本

### 2️⃣ 相似文件分析
- 使用序列匹配算法计算文件相似度
- 默认阈值 95%（可配置）
- 发现高度相似的文件对（可能需要手动合并）

### 3️⃣ 无用文件清理
自动检测并清理：
- 临时文件（.tmp）
- 备份文件（.bak, .old）
- 日志文件（.log）
- 系统文件（Thumbs.db, .DS_Store）

### 4️⃣ 性能问题检测
识别性能瓶颈：
- **大文件**: > 10MB
- **空文件**: 0 字节
- **重复依赖**: 重复的 node_modules 或 venv

### 5️⃣ 智能归档整理
按照规则自动归档：
- **文档** → `docs/` 目录
- **脚本** → `scripts/` 目录
- **配置** → `config/` 目录
- **测试** → `tests/` 目录

## 🚀 使用方法

### 方法 1: 双击运行（最简单）
```bash
双击 run_cleaner.bat
```

### 方法 2: Claude Code 命令
```bash
/clean
/cleanup
/organize
/tidy
```

### 方法 3: 命令行运行
```bash
python .claude-code/skills/project-cleaner/index.py
```

### 方法 4: 运行测试
```bash
python .claude-code/skills/project-cleaner/test.py
```

## 📊 测试结果

所有测试已通过 ✅：
```
✅ 测试 1: 重复文件检测
✅ 测试 2: 无用文件检测
✅ 测试 3: 性能问题检测
✅ 测试 4: 归档建议
✅ 测试 5: 完整工作流程
```

## ⚙️ 配置说明

配置文件：[.claude-code/skills/project-cleaner/skill.json](.claude-code/skills/project-cleaner/skill.json)

### 关键配置项：

```json
{
  "duplicateThreshold": 0.95,        // 相似度阈值（0-1）

  "excludePatterns": [               // 排除目录（永不触碰）
    "**/node_modules/**",
    "**/venv/**",
    "**/.git/**"
  ],

  "unusedFilePatterns": [            // 无用文件模式
    "**/*.tmp",
    "**/*.bak",
    "**/*.old",
    "**/*.log"
  ],

  "archiveRules": {                  // 归档规则
    "docs": {
      "patterns": ["**/*.md"],
      "targetDir": "docs"
    },
    "scripts": {
      "patterns": ["**/*.bat", "**/*.sh"],
      "targetDir": "scripts"
    }
  }
}
```

## 🔒 安全特性

1. **默认干运行模式** - 仅分析不执行，先预览结果
2. **自动备份机制** - 操作前备份到 `.cleanup_backup/`
3. **排除保护** - 永不触碰关键目录（node_modules, venv, .git）
4. **详细日志** - 所有操作可追溯
5. **错误处理** - 单个文件出错不影响整体流程

## 📈 典型工作流

```
第 1 步: 运行工具（干运行模式）
   └─> 双击 run_cleaner.bat 或运行命令

第 2 步: 查看报告
   └─> 打开 cleanup_report.txt
   └─> 检查将要执行的操作

第 3 步: 调整配置（可选）
   └─> 编辑 skill.json
   └─> 修改规则和阈值

第 4 步: 实际执行（可选）
   └─> 编辑 index.py
   └─> 设置 dry_run=False
   └─> 再次运行

第 5 步: 提交变更
   └─> git add .
   └─> git commit -m "Project cleanup"
```

## 📋 输出报告示例

运行后会生成 `cleanup_report.txt`：

```
================================================================================
📊 项目清理分析报告
================================================================================

📋 重复文件: 发现 2 组
  组 1:
    - backend/venv/Scripts/python.exe
    - venv/Scripts/python.exe

📋 相似文件: 发现 3 对
  - config.js ↔ config.backup.js (相似度: 98.50%)

📋 无用文件: 发现 15 个
  - temp/cache.tmp
  - logs/debug.log

📋 性能问题: 发现 5 个
  - 文件过大: 15.23MB: data/dataset.csv
  - 空文件: test/empty.js

📋 归档建议:
  docs: 12 个文件待整理
  scripts: 8 个文件待整理
```

## 🎨 自定义扩展

### 添加新的无用文件类型
```json
"unusedFilePatterns": [
  "**/*.tmp",
  "**/*.cache",      // 新增缓存文件
  "**/debug_*.log"   // 新增调试日志
]
```

### 创建新的归档规则
```json
"archiveRules": {
  "images": {
    "patterns": ["**/*.png", "**/*.jpg", "**/*.svg"],
    "targetDir": "assets/images"
  },
  "data": {
    "patterns": ["**/*.csv", "**/*.json"],
    "targetDir": "data"
  }
}
```

### 调整相似度检测
```json
"duplicateThreshold": 0.90  // 从 95% 降低到 90%
```

## 🛠️ 故障排查

| 问题 | 解决方法 |
|------|----------|
| 权限不足 | 以管理员身份运行 |
| 路径过长 | 启用 Windows 长路径支持 |
| 编码错误 | 已自动处理 UTF-8 |
| 文件被占用 | 关闭相关程序后重试 |

## 📚 文档索引

- **快速参考**: [QUICKREF.md](.claude-code/skills/project-cleaner/QUICKREF.md)
- **完整文档**: [README.md](.claude-code/skills/project-cleaner/README.md)
- **配置文件**: [skill.json](.claude-code/skills/project-cleaner/skill.json)
- **源代码**: [index.py](.claude-code/skills/project-cleaner/index.py)
- **测试代码**: [test.py](.claude-code/skills/project-cleaner/test.py)

## 🌟 使用建议

1. **定期运行** - 建议每周运行一次保持项目整洁
2. **重构前运行** - 重构前清理可以减少混乱
3. **合并前检查** - 合并分支前检查重复文件
4. **优化性能** - 发现大文件和性能问题
5. **新人友好** - 帮助新团队成员理解项目结构

## ⚡ 性能优化

对于大型项目：
1. 使用 `excludePatterns` 排除不必要的目录
2. 限制 `scanPatterns` 到特定文件类型
3. 分批处理不同目录
4. 考虑缓存哈希值（未来功能）

## 🎯 下一步建议

针对你的 StockTracker 项目：

1. **立即运行一次分析**
   ```bash
   python .claude-code/skills/project-cleaner/index.py
   ```

2. **查看报告**
   - 检查是否有重复的 venv 目录
   - 查找重复的配置文件
   - 发现无用的临时文件

3. **根据需要调整配置**
   - 添加股票数据文件到排除列表
   - 配置归档规则适应你的项目结构

4. **定期维护**
   - 每次重大更新后运行
   - 每周定期清理

---

## 💡 特别说明

这个 Skill 是为你的 StockTracker 项目量身定制的，但也具有通用性，可以用于任何项目。核心特点：

- ✅ **智能化** - 自动检测问题，无需手动配置
- ✅ **安全性** - 干运行模式，永不意外删除
- ✅ **可配置** - 灵活的规则系统
- ✅ **可扩展** - 易于添加新功能
- ✅ **文档完善** - 详细的使用说明

祝你使用愉快！🎉
