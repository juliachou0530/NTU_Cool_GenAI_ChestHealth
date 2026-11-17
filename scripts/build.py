"""把 source/*.txt 轉成 leaflets/<頁面代號>.json 與 data/catalog.json。

用法（在專案根目錄）：python scripts/build.py
這是唯一產生 JSON 的方式；不要手動修改 leaflets/ 與 data/ 內的檔案。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "source"
LEAFLET_DIR = ROOT / "leaflets"
CATALOG = ROOT / "data" / "catalog.json"

FIELDS = {  # TXT 欄位名稱 → JSON 鍵
    "標題": "title", "頁面代號": "id", "分類": "category", "資料類型": "document_type",
    "單張編號": "code", "制訂單位": "unit", "制修訂日期": "revised_date",
    "諮詢電話": "contact", "教材整理日期": "prepared_date",
}
SECTION_RE = re.compile(r"^【([^】\n]+)】[ \t]*$", re.MULTILINE)
FILENAME_RE = re.compile(r"^(\d{2})_([a-z0-9]+(?:-[a-z0-9]+)*)\.txt$")


def parse_header(text):
    header = SECTION_RE.split(text, maxsplit=1)[0]
    meta = {}
    for line in header.splitlines():
        m = re.match(r"^([^：:]+)[：:][ \t]*(.*)$", line.strip())
        if m and m.group(1) in FIELDS:
            meta[FIELDS[m.group(1)]] = m.group(2).strip()
    return meta


def split_sections(text):
    parts = SECTION_RE.split(text)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def parse_content(body):
    """【內容】：空行分段；每段第一行是小標，「・」開頭為條列，其餘為段落。"""
    blocks = []
    for chunk in re.split(r"\n\s*\n", body.strip()):
        lines = [l.strip() for l in chunk.splitlines() if l.strip()]
        if not lines:
            continue
        heading, rest = lines[0], lines[1:]
        items = []
        for line in rest:
            if line.startswith("・"):
                items.append({"type": "bullet", "text": line[1:].strip()})
            else:
                items.append({"type": "paragraph", "text": line})
        blocks.append({
            "heading": heading,
            "alert": any(k in heading for k in ("緊急", "就醫")),
            "items": items,
        })
    return blocks


def parse_quiz(body):
    questions, answer_lines = [], []
    for line in (l.strip() for l in body.splitlines()):
        if re.match(r"^問題\s*\d+\s*[：:]", line) and "正確答案" not in line and "(" in line:
            questions.append(re.sub(r"^問題\s*\d+\s*[：:]\s*", "", line))
        elif line:
            answer_lines.append(line)
    return {"questions": questions, "answers": " ".join(answer_lines).replace("正確答案", "").lstrip("：: ")}


def build_one(path):
    m = FILENAME_RE.match(path.name)
    if not m:
        raise SystemExit(f"檔名不符規則（NN_頁面代號.txt）：{path.name}")
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    meta = parse_header(text)
    sections = split_sections(text)
    if meta.get("id") != m.group(2):
        raise SystemExit(f"{path.name}：檔名代號 {m.group(2)} 與「頁面代號」{meta.get('id')} 不一致")
    if "內容" not in sections:
        raise SystemExit(f"{path.name}：缺少【內容】區段")
    content = parse_content(sections["內容"])
    return {
        **meta,
        "order": int(m.group(1)),
        "source_file": f"source/{path.name}",
        "summary": next((it["text"] for b in content for it in b["items"]), ""),
        "content": content,
        "quiz": parse_quiz(sections.get("複習問題", "")),
        "references": [l.strip() for l in sections.get("參考資料", "").splitlines() if l.strip()],
        "notice": sections.get("提醒", "").strip(),
    }


def main():
    LEAFLET_DIR.mkdir(exist_ok=True)
    CATALOG.parent.mkdir(exist_ok=True)
    leaflets = [build_one(p) for p in sorted(SOURCE_DIR.glob("*.txt"))]
    expected = {f"{d['id']}.json" for d in leaflets}
    for old in LEAFLET_DIR.glob("*.json"):  # 移除已不存在於 source/ 的單張
        if old.name not in expected:
            old.unlink()
    for d in leaflets:
        (LEAFLET_DIR / f"{d['id']}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog = [{k: d[k] for k in ("id", "order", "title", "category", "code", "unit", "revised_date", "summary")}
               | {"sections": len(d["content"])} for d in leaflets]
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已產生 {len(leaflets)} 份單張：", "、".join(d["title"] for d in leaflets))


if __name__ == "__main__":
    main()
