# AGENTS.md

本專案的 AI 規則都寫在 [CLAUDE.md](CLAUDE.md)，請先完整閱讀後再修改任何檔案。

重點摘要：
- 內容只能來自 `source/*.txt`（院內核准衛教單張的原文），不可改寫或補充醫療內容。
- 新增單張：建立 `source/NN_頁面代號.txt` → `python scripts/build.py` → `python scripts/validate.py`（必須全部通過）。
- 不要手動修改 `leaflets/` 與 `data/`，它們由 `build.py` 產生。
