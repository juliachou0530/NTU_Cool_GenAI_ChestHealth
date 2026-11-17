# 胸腔衛教單張庫

把院內核准的胸腔護理衛教單張做成網頁，讓病人與家屬可以在手機上閱讀、放大字體、列印。

🌐 網站：https://juliachou0530.github.io/NTU_Cool_GenAI_ChestHealth/

## 特色
- 每份單張保留**原單張編號、制訂單位、制修訂日期**，內容與原單張一致
- 「緊急返院提醒」自動以紅色警示框顯示
- 字體可放大 1.25 倍，可直接列印
- 新增單張只要放一個 TXT、執行一個指令

## 新增單張
```bash
# 1. 在 source/ 新增 NN_頁面代號.txt（格式見 CLAUDE.md 第 4 節）
python scripts/build.py      # 2. 產生網頁用的 JSON
python scripts/validate.py   # 3. 檢查規則，必須全部通過
python -m http.server 8000   # 4. 本機預覽 http://localhost:8000
```

完整規則（給 AI 與開發者）請見 [CLAUDE.md](CLAUDE.md)。

## 聲明
本站內容僅供參考，實際治療以醫師診治為主；如有不適請立即就醫。
