import os, requests, datetime, pathlib, re, sys

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "content"
pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# Preferred property names — falls back automatically
PREF = {
    "firm": ["Firm Name", "Name", "Title"],
    "code": ["Affiliate Code", "Code", "Discount Code"],
    "url": ["Landing URL", "URL", "Link"],
    "benefit": ["Short Benefit", "Benefit"],
    "fee": ["Fee", "Price"],
    "req": ["Requirements", "Rules"],
    "best_for": ["Best For", "Audience"],
    "notes": ["Notes", "Extra"],
    "slug": ["Slug", "Handle"],
}

def slugify(s: str) -> str:
    return re.sub(r'[^a-z0-9-]+', '-', (s or "").lower()).strip('-') or "firm"

def get_first_of_type(props, ptype):
    for k, v in props.items():
        if v.get("type") == ptype:
            return k
    return None

def pick_property(props, candidates, expect_type=None):
    for name in candidates:
        if name in props and (expect_type is None or props[name].get("type") == expect_type):
            return name
    if expect_type:
        t = get_first_of_type(props, expect_type)
        if t:
            return t
    lower = {k.lower(): k for k in props.keys()}
    for name in candidates:
        if name.lower() in lower:
            return lower[name.lower()]
    return None

def read_value(props, key, expect_type):
    if not key or key not in props:
        return ""
    p = props[key]
    t = p.get("type")
    try:
        if expect_type == "title" and t == "title":
            arr = p["title"]
            return arr[0]["plain_text"].strip() if arr else ""
        if expect_type == "url" and t == "url":
            return (p["url"] or "").strip()
        if t == "rich_text":
            arr = p["rich_text"]
            return arr[0]["plain_text"].strip() if arr else ""
        if t == "select":
            return (p["select"]["name"] or "").strip() if p.get("select") else ""
        if t == "multi_select":
            return ", ".join(x["name"] for x in p.get("multi_select", []))
        if t == "number":
            return str(p.get("number") or "")
        if t == "checkbox":
            return "yes" if p.get("checkbox") else "no"
    except Exception:
        return ""
    return ""

def fetch_all_rows(db_id):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload = {}
    while True:
        r = requests.post(url, headers=HEADERS, json=payload)
        if r.status_code != 200:
            raise SystemExit(f"❌ Notion API error {r.status_code}: {r.text}")
        data = r.json()
        for row in data.get("results", []):
            yield row
        if not data.get("has_more"):
            break
        payload = {"start_cursor": data.get("next_cursor")}

def main():
    if not NOTION_TOKEN or not DB_ID:
        raise SystemExit("❌ NOTION_TOKEN or NOTION_DB_ID missing.")

    today = datetime.date.today().isoformat()
    count = 0

    for row in fetch_all_rows(DB_ID):
        props = row["properties"]

        firm_key = pick_property(props, PREF["firm"], "title")
        url_key  = pick_property(props, PREF["url"],  "url")
        code_key = pick_property(props, PREF["code"])
        ben_key  = pick_property(props, PREF["benefit"])
        fee_key  = pick_property(props, PREF["fee"])
        req_key  = pick_property(props, PREF["req"])
        bf_key   = pick_property(props, PREF["best_for"])
        notes_key= pick_property(props, PREF["notes"])
        slug_key = pick_property(props, PREF["slug"])

        firm = read_value(props, firm_key, "title") or "Unknown Firm"
        site = read_value(props, url_key,  "url")   or "#"
        code = read_value(props, code_key, None)
        benefit = read_value(props, ben_key, None) or "Discount available"
        fee = read_value(props, fee_key, None) or "n/a"
        req = read_value(props, req_key, None) or "n/a"
        best_for = read_value(props, bf_key, None) or "Traders"
        notes = read_value(props, notes_key, None)
        slug = read_value(props, slug_key, None) or slugify(firm)

        md = f"""---
title: "{firm} Discount Code — Save on {firm}"
description: "Active {firm} discount code and how to use it."
last_updated: {today}
permalink: /{slug}/
---

# {firm} — Active Discount Code

**Affiliate code:** `{code}`  
[Go to {firm}]({site}){{:target="_blank" rel="noopener"}}

## Quick facts
- Benefit: {benefit}
- Fee: {fee}
- Requirements: {req}
- Best for: {best_for}

## How to apply the code
1. Go to the site above.
2. Pick your challenge/account.
3. Paste code `{code}` at checkout.

{notes}
"""
        path = pathlib.Path(OUT_DIR) / f"{slug}.md"
        path.write_text(md, encoding="utf-8")
        print(f"✅ Wrote {path}")
        count += 1

    if count == 0:
        print("⚠️ No rows found. Add rows in Notion and re-run.")

if __name__ == "__main__":
    main()
