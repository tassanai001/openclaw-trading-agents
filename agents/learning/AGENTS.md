# Learning Agent

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Performance tracking and daily report generation. Records P&L, win rate, drawdown, and trade counts.

## STRUCTURE

```
agents/learning/
├── learning.py   # Main implementation
├── config.py     # LearningConfig dataclass
└── __init__.py   # Exports LearningAgent class
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Record metrics | `learning.py:record_performance()` | Append to history |
| Generate report | `learning.py:generate_daily_report()` | Markdown format |
| Save report | `learning.py:save_daily_report()` | writes to `reports/` |
| Summary stats | `learning.py:get_performance_summary()` | Aggregate metrics |

## CONVENTIONS

- **Report format**: Markdown with tables
- **Storage**: `reports/learning/` directory
- **History**: Last 1000 records kept in memory

## ANTI-PATTERNS

- **Never** overwrite existing reports — use date-stamped filenames
- **Never** export raw data without filtering by date
