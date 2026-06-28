"""
fetch_articles.py ― まほろば！攻略情報 自動収集スクリプト
===========================================================
GitHub Actions から build.py の前に実行されます。
Reddit公式API → articles.json を生成します。
失敗時も空JSONを生成してデプロイを止めません。
===========================================================
"""

import json, time, requests
from datetime import datetime, timezone, timedelta

UA      = "Mozilla/5.0 (compatible; MahorobaGuild/1.0)"
HEADERS = {"User-Agent": UA}
TIMEOUT = 15
JST     = timezone(timedelta(hours=9))

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
# リトライ付きGET（429・タイムアウト対策）
# ============================================================
def safe_get(url, retries=3, wait=5):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 429:
                print(f"  [429] レート制限 → {wait}秒待機してリトライ ({i+1}/{retries})")
                time.sleep(wait)
                wait *= 2  # 指数バックオフ
                continue
            return r
        except requests.exceptions.Timeout:
            print(f"  [Timeout] {wait}秒待機してリトライ ({i+1}/{retries})")
            time.sleep(wait)
        except Exception as e:
            print(f"  [Error] {e}")
            break
    return None

# ============================================================
# Reddit公式API
# ============================================================
def fetch_reddit():
    print("[fetch] Reddit から情報収集中...")
    articles = []

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
        r = safe_get(url)
        if r is None or r.status_code != 200:
            print(f"  [{query}] 取得失敗 → スキップ")
            continue

        try:
            posts = r.json().get("data", {}).get("children", [])
        except Exception:
            print(f"  [{query}] JSONパース失敗 → スキップ")
            continue

        print(f"  [{query}] {len(posts)}件取得")

        for post in posts:
            d     = post.get("data", {})
            title = d.get("title", "").strip()
            if not title or not is_relevant(title):
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

        time.sleep(2)  # レート制限対策（1→2秒に強化）

    # 重複除去
    seen, unique = set(), []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    unique.sort(key=lambda x: -x.get("score", 0))
    print(f"[fetch] Reddit: {len(unique)}件（重複除去後）")
    return unique

# ============================================================
# メイン（失敗時も空JSONを必ず生成）
# ============================================================
def main():
    print("=" * 50)
    print(f"[fetch] 攻略情報収集開始: {now_jst()}")
    print("=" * 50)

    try:
        articles = fetch_reddit()
    except Exception as e:
        print(f"[fetch] ❌ 予期せぬエラー: {e}")
        articles = []

    output = {
        "generated_at": now_jst(),
        "total":        len(articles),
        "articles":     articles,
    }

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    if articles:
        print(f"[fetch] ✅ articles.json 生成完了（{len(articles)}件）")
    else:
        # ★ 失敗時も空JSONを生成してデプロイを止めない
        print("[fetch] ⚠️ 記事0件。空のarticles.jsonを生成しました（デプロイは続行）")

if __name__ == "__main__":
    main()
