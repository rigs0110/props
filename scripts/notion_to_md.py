import os, requests, datetime, pathlib, re

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB_ID")
OUT_DIR = "content"
pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

def slugify(s):
    return re.sub(r'[^a-z0-9-]+', '-', s.lower()).strip('-')

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{DB_ID}/query"
data = requests.post(url, headers=headers).json()
today = datetime.date.today().isoformat()

for row in data.get("results", []):
    props = row["properties"]
    firm = props["Firm Name"]["title"][0]["plain_text"] if props["Firm Name"]["title"] else "Unknown"
    code = props["Affiliate Code"]["rich_text"][0]["plain_text"] if props["Affiliate Code"]["rich_text"] else ""
    site = props["Landing URL"]["url"] if props["Landing URL"]["url"] else "#"
    benefit = props["Short Benefit"]["rich_text"][0]["plain_text"] if props["Short Benefit"]["rich_text"] else "Discount available"
    fee = props["Fee"]["rich_text"][0]["plain_text"] if props["Fee"]["rich_text"] else "n/a"
    requirements = props["Requirements"]["rich_text"][0]["plain_text"] if props["Requirements"]["rich_text"] else "n/a"
    best_for = props["Best For"]["rich_text"][0]["plain_text"] if props["Best For"]["rich_text"] else "Traders"
    notes = props["Notes"]["rich_text"][0]["plain_text"] if props["Notes"]["rich_text"] else ""
    slug = props["Slug"]["rich_text"][0]["plain_text"] if props["Slug"]["rich_text"] else slugify(firm)

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
- Requirements: {requirements}
- Best for: {best_for}

## How to apply the code
1. Go to the site above.
2. Pick your challenge/account.
3. Paste code `{code}` at checkout.

{notes}
"""
    with open(f"{OUT_DIR}/{slug}.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ Wrote {OUT_DIR}/{slug}.md")
