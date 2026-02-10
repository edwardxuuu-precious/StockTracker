"""
AI Benchmark Test Set - Agent Strategy Generation

Purpose: Evaluate Agent's ability to generate logically valid strategies from natural language prompts.

Format:
- prompt: User's natural language request
- expected_type: Expected strategy type
- expected_params: Expected parameter names and constraints
- quality_checks: Assertions to validate the generated strategy
"""

AGENT_PROMPT_TEST_SET = [
    # Basic Moving Average Strategies
    {
        "id": "AG-001",
        "category": "moving_average",
        "prompt": "生成均线策略，短期5天长期20天",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 5, "constraint": "< long_window"},
            "long_window": {"value": 20, "constraint": "> short_window"},
        },
        "quality_checks": [
            "short_window < long_window",
            "short_window >= 1",
            "long_window >= 2",
        ],
    },
    {
        "id": "AG-002",
        "category": "moving_average",
        "prompt": "创建一个快速均线策略，3天短线和10天长线",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 3, "constraint": "< long_window"},
            "long_window": {"value": 10, "constraint": "> short_window"},
        },
        "quality_checks": [
            "short_window < long_window",
            "short_window >= 1",
        ],
    },
    {
        "id": "AG-003",
        "category": "moving_average",
        "prompt": "Build a moving average crossover strategy with short=8 and long=21",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 8, "tolerance": 2},
            "long_window": {"value": 21, "tolerance": 5},
        },
        "quality_checks": [
            "short_window < long_window",
        ],
    },
    # Conservative vs Aggressive Variants
    {
        "id": "AG-004",
        "category": "moving_average",
        "prompt": "生成保守的均线策略，仓位控制在10%",
        "expected_type": "moving_average",
        "expected_params": {
            "allocation_per_trade": {"max": 0.15},
        },
        "quality_checks": [
            "allocation_per_trade <= 0.15",
            "allocation_per_trade > 0",
        ],
    },
    {
        "id": "AG-005",
        "category": "moving_average",
        "prompt": "创建激进的趋势跟踪策略，每次交易30%仓位",
        "expected_type": "moving_average",
        "expected_params": {
            "allocation_per_trade": {"min": 0.25, "max": 0.35},
        },
        "quality_checks": [
            "allocation_per_trade >= 0.25",
            "allocation_per_trade <= 0.5",
        ],
    },
    # Long-term vs Short-term
    {
        "id": "AG-006",
        "category": "moving_average",
        "prompt": "生成长期持有策略，使用50天和200天均线",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 50, "tolerance": 10},
            "long_window": {"value": 200, "tolerance": 20},
        },
        "quality_checks": [
            "short_window >= 30",
            "long_window >= 100",
            "short_window < long_window",
        ],
    },
    {
        "id": "AG-007",
        "category": "moving_average",
        "prompt": "创建短线交易策略，2天和5天均线",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 2, "tolerance": 1},
            "long_window": {"value": 5, "tolerance": 2},
        },
        "quality_checks": [
            "short_window <= 5",
            "long_window <= 10",
        ],
    },
    # Edge Cases & Ambiguous Prompts
    {
        "id": "AG-008",
        "category": "moving_average",
        "prompt": "帮我做一个趋势策略",
        "expected_type": "moving_average",
        "expected_params": {},  # No specific values expected
        "quality_checks": [
            "short_window < long_window",
            "allocation_per_trade > 0",
            "allocation_per_trade <= 1",
        ],
    },
    {
        "id": "AG-009",
        "category": "moving_average",
        "prompt": "Generate a simple MA strategy",
        "expected_type": "moving_average",
        "expected_params": {},
        "quality_checks": [
            "short_window < long_window",
        ],
    },
    {
        "id": "AG-010",
        "category": "moving_average",
        "prompt": "均线金叉死叉策略，参数自己定",
        "expected_type": "moving_average",
        "expected_params": {},
        "quality_checks": [
            "short_window < long_window",
            "short_window >= 2",
            "long_window >= 5",
        ],
    },
    # Multi-parameter Combinations
    {
        "id": "AG-011",
        "category": "moving_average",
        "prompt": "生成均线策略：短期5天、长期15天、每次20%仓位",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 5, "tolerance": 1},
            "long_window": {"value": 15, "tolerance": 2},
            "allocation_per_trade": {"value": 0.2, "tolerance": 0.05},
        },
        "quality_checks": [
            "short_window < long_window",
            "allocation_per_trade >= 0.15",
            "allocation_per_trade <= 0.25",
        ],
    },
    {
        "id": "AG-012",
        "category": "moving_average",
        "prompt": "创建稳健策略：10日和30日均线，单笔仓位不超过15%",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 10, "tolerance": 2},
            "long_window": {"value": 30, "tolerance": 5},
            "allocation_per_trade": {"max": 0.15},
        },
        "quality_checks": [
            "short_window < long_window",
            "allocation_per_trade <= 0.15",
        ],
    },
    # Boundary Conditions
    {
        "id": "AG-013",
        "category": "moving_average",
        "prompt": "生成最小窗口的均线策略，1天和2天",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 1, "tolerance": 1},
            "long_window": {"value": 2, "tolerance": 1},
        },
        "quality_checks": [
            "short_window >= 1",
            "long_window >= 2",
            "short_window < long_window",
        ],
    },
    {
        "id": "AG-014",
        "category": "moving_average",
        "prompt": "创建极保守策略，每次只用5%资金",
        "expected_type": "moving_average",
        "expected_params": {
            "allocation_per_trade": {"max": 0.1},
        },
        "quality_checks": [
            "allocation_per_trade <= 0.1",
            "allocation_per_trade > 0",
        ],
    },
    # Chinese & English Mixed
    {
        "id": "AG-015",
        "category": "moving_average",
        "prompt": "Create MA strategy with short=7, long=21, allocation=25%",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 7, "tolerance": 2},
            "long_window": {"value": 21, "tolerance": 5},
            "allocation_per_trade": {"value": 0.25, "tolerance": 0.05},
        },
        "quality_checks": [
            "short_window < long_window",
            "allocation_per_trade >= 0.2",
            "allocation_per_trade <= 0.3",
        ],
    },
    # Complex Requirements
    {
        "id": "AG-016",
        "category": "moving_average",
        "prompt": "生成中期趋势策略，适合波段操作，窗口15和45天",
        "expected_type": "moving_average",
        "expected_params": {
            "short_window": {"value": 15, "tolerance": 5},
            "long_window": {"value": 45, "tolerance": 10},
        },
        "quality_checks": [
            "short_window >= 10",
            "short_window <= 20",
            "long_window >= 35",
            "long_window <= 60",
        ],
    },
    {
        "id": "AG-017",
        "category": "moving_average",
        "prompt": "适合A股的均线策略，考虑T+1限制",
        "expected_type": "moving_average",
        "expected_params": {},
        "quality_checks": [
            "short_window < long_window",
            "short_window >= 2",  # T+1 means at least 2 days
        ],
    },
    # Negative/Invalid Cases (should handle gracefully)
    {
        "id": "AG-018",
        "category": "moving_average",
        "prompt": "生成均线策略，短线比长线长",  # Contradictory requirement
        "expected_type": "moving_average",
        "expected_params": {},
        "quality_checks": [
            "short_window < long_window",  # Should auto-correct
        ],
        "notes": "Agent should auto-correct contradictory requirements",
    },
    {
        "id": "AG-019",
        "category": "moving_average",
        "prompt": "均线策略，200%仓位",  # Invalid allocation
        "expected_type": "moving_average",
        "expected_params": {},
        "quality_checks": [
            "allocation_per_trade <= 1",  # Should cap at 100%
            "allocation_per_trade > 0",
        ],
        "notes": "Agent should cap allocation at reasonable levels",
    },
    {
        "id": "AG-020",
        "category": "moving_average",
        "prompt": "Generate a strategy that always wins",  # Unrealistic expectation
        "expected_type": "moving_average",
        "expected_params": {},
        "quality_checks": [
            "short_window < long_window",
        ],
        "notes": "Agent should generate reasonable strategy despite unrealistic prompt",
    },
]
