"""
fetch_articles.py ― まほろば！攻略情報 自動収集スクリプト
===========================================================
GitHub Actions から build.py の前に実行されます。
Reddit公式API → articles.json を生成します。
===========================================================
"""

import json, time, requests
from datetime import datetime, timezone, timedelta

UA      = "Mozilla/5.0 (compatible; MahorobaGuild/1.0)"
HEADERS = {"User-Agent": UA}
TIMEOUT = 15
JST     = timezone(timedelta(hours=9))

# ============================================================
# キーワード（日英両対応）
# ============================================================
KEYWORDS = [
    # 日本語
    "ダダサバイバー", "ダダサバ", "攻略", "最強", "Tier",
    "アップデート", "初心者", "ペット", "装備", "ギルド",
    # 英語
    "Dada Survivor", "DadaSurvivor",
    "tier list", "best build", "patch notes",
    "beginner", "guide", "guild", "update",
]

def now_jst():
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M')

def is_relevant(text):
    t = text.lower()
    return any(kw.lower() in t for kw in KEYWORDS)

# ============================================================
# Reddit公式API（認証不要・安定動作）
# ============================================================
def fetch_reddit():
    print("[fetch] Reddit から情報収集中...")
    articles = []

    # 検索クエリ一覧
    queries = [
        "Dada Survivor",
        "DadaSurvivor tier list",
        "Dada Survivor guide",
        "Dada Survivor update",
    ]

    for query in queries:
        url = (
            "https://www.reddit.com/search.json"
            f"?q={requests.utils.quote(query)}&sort=new&limit=8"
        )
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code != 200:
                print(f"  [{query}] HTTP {r.status_code} → スキップ")
                continue

            posts = r.json().get("data", {}).get("children", [])
            print(f"  [{query}] {len(posts)}件取得")

            for post in posts:
                d     = post.get("data", {})
                title = d.get("title", "")
                if not is_relevant(title):
                    continue

                articles.append({
                    "source":  "Reddit",
                    "lang":    "EN",
                    "title":   title,
                    "url":     "https://www.reddit.com" + d.get("permalink", ""),
                    "date":    datetime.fromtimestamp(
                                   d.get("created_utc", 0), tz=timezone.utc
                               ).astimezone(JST).strftime('%Y-%m-%d'),
                    "summary": d.get("selftext", "")[:150].strip(),
                    "score":   d.get("score", 0),
                })

            time.sleep(1)  # サーバー負荷軽減

        except Exception as e:
            print(f"  [{query}] エラー: {e}")

    # 重複除去（URLで判定）
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    unique.sort(key=lambda x: -x.get("score", 0))
    print(f"[fetch] Reddit: {len(unique)}件（重複除去後）")
    return unique

# ============================================================
# メイン
# ============================================================
def main():
    print("=" * 50)
    print(f"[fetch] 攻略情報収集開始: {now_jst()}")
    print("=" * 50)

    articles = fetch_reddit()

    output = {
        "generated_at": now_jst(),
        "total":        len(articles),
        "articles":     articles,
    }

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[fetch] ✅ articles.json 生成完了（{len(articles)}件）")

if __name__ == "__main__":
    main()
