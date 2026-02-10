# AI Benchmark Infrastructure

## Overview

This directory contains benchmark test sets and runners for evaluating the quality of AI/Agent features in StockTracker.

## Components

### 1. Test Sets

#### Agent Prompt Test Set (`agent_prompt_test_set.py`)
- **Purpose**: Evaluate Agent's ability to generate logically valid strategies from natural language prompts
- **Coverage**: 20 test cases covering:
  - Basic MA strategies with specific parameters
  - Conservative vs aggressive variants
  - Long-term vs short-term strategies
  - Edge cases and ambiguous prompts
  - Multi-parameter combinations
  - Boundary conditions
  - Negative/invalid cases (auto-correction testing)

#### KB Q&A Test Set (`kb_qa_test_set.py`)
- **Purpose**: Evaluate KB's retrieval recall and ranking quality
- **Coverage**: 50 test cases across categories:
  - Risk management (drawdown, stop-loss, position sizing)
  - Performance metrics (Sharpe ratio, win rate, max drawdown)
  - Strategy development (optimization, backtesting pitfalls)
  - Market microstructure (spread, impact cost)
  - Chinese market specifics (T+1, circuit breakers)
  - Technical indicators (RSI, Bollinger Bands, MACD)
  - Portfolio management (diversification, rebalancing)

### 2. Benchmark Runners

#### Agent Benchmark Runner (`run_agent_benchmark.py`)
- **Status**: ✅ Implemented and tested
- **Features**:
  - Evaluates generated strategy type, parameters, and logical constraints
  - Supports subset testing (`--subset N`)
  - Category filtering (`--category moving_average`)
  - JSON output with detailed results
  - Pass/fail reporting with quality thresholds

**Usage**:
```bash
# Run all cases
python -m benchmarks.run_agent_benchmark

# Run subset
python -m benchmarks.run_agent_benchmark --subset 5

# Filter by category
python -m benchmarks.run_agent_benchmark --category moving_average

# Specify output
python -m benchmarks.run_agent_benchmark --output results/my_run.json
```

**Example Output**:
```
Running Agent Benchmark (20 cases)...

[1/20] AG-001: 生成均线策略，短期5天长期20天...
  [PASS] (10 checks)
[2/20] AG-002: 创建一个快速均线策略，3天短线和10天长线...
  [PASS] (9 checks)
...

============================================================
BENCHMARK SUMMARY
============================================================
Total cases: 20
Passed: 18 (90.0%)
Failed: 2
Errors: 0
============================================================
```

#### KB Benchmark Runner (`run_kb_benchmark.py`)
- **Status**: 🚧 Planned (framework ready, implementation pending)
- **Planned Features**:
  - Evaluate recall@k (top-1, top-3, top-5)
  - Measure ranking quality (NDCG, MRR)
  - Confidence score accuracy
  - Source type filtering effectiveness

### 3. Quality Standards

#### Agent Generation Quality
- ✅ **Type correctness**: Generated strategy type matches expected
- ✅ **Parameter presence**: All required parameters exist
- ✅ **Parameter values**: Match prompt requirements (with tolerance)
- ✅ **Logical constraints**: Parameters satisfy business logic (e.g., short < long)
- ✅ **Boundary compliance**: Values within reasonable min/max bounds

#### KB Retrieval Quality (Planned)
- 🚧 **Recall@3**: At least 67% of relevant docs in top-3
- 🚧 **Top-1 relevance**: Highest-ranked result is "high" or "medium" relevance
- 🚧 **Ranking quality**: Highly relevant docs rank higher than partially relevant
- 🚧 **Confidence accuracy**: High-confidence results are actually relevant

### 4. Quality Thresholds

| Metric | Current | Target |
|--------|---------|--------|
| Agent prompt accuracy | 100% (3/3 tested) | ≥ 90% |
| Agent parameter logic | 100% (3/3 tested) | ≥ 95% |
| KB recall@3 | TBD | ≥ 80% |
| KB top-1 relevance | TBD | ≥ 85% |

## Integration

### CI/CD Pipeline (Recommended)
```yaml
# Example GitHub Actions workflow
- name: Run Agent Benchmark
  run: python -m benchmarks.run_agent_benchmark

- name: Check pass rate
  run: |
    PASS_RATE=$(jq '.summary.pass_rate' < .runtime/benchmarks/latest.json)
    if (( $(echo "$PASS_RATE < 0.9" | bc -l) )); then
      echo "Agent benchmark pass rate below 90%: $PASS_RATE"
      exit 1
    fi
```

### Pre-release Testing
Before each release, run full benchmarks and verify:
1. Agent prompt accuracy ≥ 90%
2. No regressions from previous run
3. New test cases added for new features

## Next Steps

### Short-term (P1)
- [ ] Implement KB benchmark runner
- [ ] Run baseline benchmarks and record results
- [ ] Set quality thresholds based on baseline

### Medium-term (P2)
- [ ] Add Agent benchmark for strategy tuning quality
- [ ] Expand test sets to cover more strategy types (RSI, Bollinger Bands)
- [ ] Implement automated regression detection

### Long-term (P3)
- [ ] Build end-to-end scenario benchmarks
- [ ] Add user feedback collection mechanism
- [ ] Implement A/B testing framework for prompt templates

## History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-10 | v0.1 | Initial benchmark infrastructure created |

## Related Documentation

- [AI Quality Overview](../../docs/QA/AI_Quality_Overview_2026-02-10.md)
- [Agent LLM Readiness Checklist](../../docs/QA/Agent_LLM_Readiness_Checklist_2026-02-10.md)
- [Test AI Quality](../tests/test_ai_quality.py)
