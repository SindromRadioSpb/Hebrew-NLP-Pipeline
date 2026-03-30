# 7.1. Test Strategy — KADIMA

## Уровни тестирования

### Unit Tests
- Каждый модуль M1–M13: ≥ 90% coverage
- Gold corpus tests: 26 корпусов × all checks
- Edge cases: empty, single-token, noise, degenerate

### Integration Tests
- Pipeline M1→M2→M3→M8: end-to-end on gold corpora
- Validation: gold → pipeline → comparison → report
- Import/export round-trip

### System Tests
- Full workflow: import → run → validate → export
- UI interactions (pytest-qt)
- API endpoints (pytest + httpx)

### Acceptance Tests (UAT)
- All 26 gold corpora → PASS
- 3 profiles produce expected differentiation
- Review sheets are correctly generated

## Test Data
- 26 gold corpora from Hebrew-NLP-Pipeline repo
- Edge case corpora (empty, noise, degenerate)
- Custom synthetic corpora for regression

## CI/CD
- GitHub Actions
- Run all tests on every push
- Coverage report: ≥ 85%
