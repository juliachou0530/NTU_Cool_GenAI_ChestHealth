"""檢查專案是否符合 CLAUDE.md 的規則。任何修改後都要跑一次，全部通過才能 commit。

用法（在專案根目錄）：python scripts/validate.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import CATALOG, LEAFLET_DIR, SOURCE_DIR, FILENAME_RE, build_one  # noqa: E402

REQUIRED = ("title", "id", "category", "code", "unit", "revised_date", "contact")
CATEGORIES = ("疾病照護", "照護技巧")
CODE_RE = re.compile(r"^PFS-\d{4}-\d{3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

errors, warnings = [], []
sources = sorted(SOURCE_DIR.glob("*.txt"))
ids, orders = {}, {}

for path in sources:
    if not FILENAME_RE.match(path.name):
        errors.append(f"{path.name}：檔名須為 NN_頁面代號.txt（小寫英文、數字、連字號）")
        continue
    try:
        expected = build_one(path)
    except SystemExit as exc:
        errors.append(str(exc))
        continue
    name = path.name
    for key in REQUIRED:
        if not expected.get(key):
            errors.append(f"{name}：缺少欄位 {key}")
    if expected.get("category") not in CATEGORIES:
        errors.append(f"{name}：分類必須是 {CATEGORIES} 之一，目前是 {expected.get('category')!r}")
    if expected.get("code") and not CODE_RE.match(expected["code"]):
        errors.append(f"{name}：單張編號格式應為 PFS-0000-000")
    if expected.get("revised_date") and not DATE_RE.match(expected["revised_date"]):
        errors.append(f"{name}：制修訂日期須以 YYYY-MM-DD 開頭")
    if expected["id"] in ids:
        errors.append(f"{name}：頁面代號與 {ids[expected['id']]} 重複")
    if expected["order"] in orders:
        errors.append(f"{name}：編號 NN 與 {orders[expected['order']]} 重複")
    ids[expected["id"]], orders[expected["order"]] = name, name

    json_path = LEAFLET_DIR / f"{expected['id']}.json"
    if not json_path.exists():
        errors.append(f"{name}：找不到 {json_path.name}，請執行 python scripts/build.py")
    elif json.loads(json_path.read_text(encoding="utf-8")) != expected:
        errors.append(f"{json_path.name}：與 source 不一致（可能被手動修改或忘了重新 build）")

    raw = path.read_text(encoding="utf-8-sig")
    for block in expected["content"]:  # 忠實度：每行內容都必須逐字出現在原始 TXT
        for item in [block["heading"]] + [it["text"] for it in block["items"]]:
            if item not in raw:
                errors.append(f"{name}：內容「{item[:20]}…」不在原始 TXT 中")
    if not any(b["alert"] for b in expected["content"]):
        warnings.append(f"{name}：沒有「緊急／就醫」段落（若原單張本來就沒有，可忽略）")

for path in LEAFLET_DIR.glob("*.json"):
    if path.stem not in ids:
        errors.append(f"leaflets/{path.name}：沒有對應的 source TXT")

catalog = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.exists() else []
if sorted(c["id"] for c in catalog) != sorted(ids):
    errors.append("data/catalog.json 與 source/ 不一致，請執行 python scripts/build.py")

for w in warnings:
    print("⚠️ ", w)
for e in errors:
    print("❌", e)
print(f"\n檢查 {len(sources)} 份單張：{'全部通過 ✅' if not errors else f'{len(errors)} 個錯誤'}")
sys.exit(1 if errors else 0)
