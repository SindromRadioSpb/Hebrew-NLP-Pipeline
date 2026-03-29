# 8.2. Release Checklist — KADIMA v1.0

## Pre-release
- [ ] All tests pass (unit, integration, system)
- [ ] All 26 gold corpora → PASS
- [ ] Code review complete
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version number bumped

## Build
- [ ] `pip install -e .` works clean
- [ ] `kadima --version` shows correct version
- [ ] `kadima gui` launches without errors
- [ ] All modules load correctly

## Validation
- [ ] Import 26 gold corpora → success
- [ ] Run pipeline on all → PASS
- [ ] Export all → correct format
- [ ] Review sheets generated → correct

## Distribution
- [ ] PyPI package built
- [ ] GitHub release created
- [ ] Documentation site updated
- [ ] Announcement prepared

## Post-release
- [ ] Monitor error reports
- [ ] Collect user feedback
- [ ] Plan v1.1 patches
