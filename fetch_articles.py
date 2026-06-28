"""
fetch_articles.py ― まほろば！攻略情報 自動収集スクリプト v2.0
===========================================================
情報源：
  ① Reddit RSS（JSON APIより制限が緩く、CI環境でも安定）
  ② Fandom Wiki API（Dada Survivor Wiki）
失敗時も空JSONを生成してデプロイを止めません。
===========================================================
"""

import json, time, re, requests
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree

UA      = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {
    "User-Agent": UA,
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
TIMEOUT = 20
JST     = timezone(timedelta(hours=9))

KEYWORDS = [
    "ダダサバイバー", "ダダサバ", "攻略", "最強", "Tier",
    "アップデート", "初心者", "ペット", "装備", "ギルド",
    "Dada Survivor", "DadaSurvivor",
    "tier list", "best build", "patch notes",
    "beginner", "guide", "guild", "update", "hero",
]

def now_jst():
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M')

def is_relevant(text):
    t = text.lower()
    return any(kw.lower() in t for kw in KEYWORDS)

# ============================================================
# リトライ付きGET（エラー詳細ログ付き）
# ============================================================
def safe_get(url, retries=3, wait=5, extra_headers=None):
    h = {**HEADERS, **(extra_headers or {})}
    for i in range(retries):
        try:
            r = requests.get(url, headers=h, timeout=TIMEOUT)
            print(f"    HTTP {r.status_code} ← {url[:80]}")
            if r.status_code == 429:
                print(f"    [429] レート制限 → {wait}秒待機 ({i+1}/{retries})")
                time.sleep(wait)
                wait *= 2
                continue
            if r.status_code == 200:
                return r
            return None
        except requests.exceptions.Timeout:
            print(f"    [Timeout] {wait}秒待機 ({i+1}/{retries})")
            time.sleep(wait)
        except requests.exceptions.ConnectionError as e:
            print(f"    [ConnectionError] {e}")
            time.sleep(wait)
        except Exception as e:
            print(f"    [Error] {type(e).__name__}: {e}")
            break
    return None

# ============================================================
# ① Reddit RSS（JSON APIより安定・CI環境でのブロックが少ない）
# ============================================================
def fetch_reddit_rss():
    print("\n[fetch] Reddit RSS から情報収集中...")
    articles = []

    # RSSフィードURL一覧（subreddit + 検索）
    rss_urls = [
        "https://www.reddit.com/search.rss?q=Dada+Survivor&sort=new&limit=10",
        "https://www.reddit.com/search.rss?q=DadaSurvivor&sort=new&limit=10",
        "https://www.reddit.com/r/dadasurvivor/.rss",  # 専用subredditがあれば
    ]

    for rss_url in rss_urls:
        r = safe_get(rss_url)
        if r is None:
            print(f"    スキップ: {rss_url[:60]}")
            continue

        try:
            root = ElementTree.fromstring(r.content)
            # RSSのnamespace対応
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'media': 'http://search.yahoo.com/mrss/',
            }

            # Atom形式（Redditの標準）
            entries = root.findall('.//atom:entry', ns)
            if not entries:
                # RSS 2.0形式のフォールバック
                entries = root.findall('.//item')

            print(f"    エントリー数: {len(entries)}件")

            for entry in entries:
                # タイトル取得（Atom / RSS両対応）
                title_el = (
                    entry.find('atom:title', ns) or
                    entry.find('title')
                )
                title = title_el.text.strip() if title_el is not None and title_el.text else ""

                # URL取得
                link_el = (
                    entry.find('atom:link', ns) or
                    entry.find('link')
                )
                if link_el is not None:
                    url = link_el.get('href') or link_el.text or ""
                else:
                    url = ""

                # 日付取得
                date_el = (
                    entry.find('atom:updated', ns) or
                    entry.find('atom:published', ns) or
                    entry.find('pubDate')
                )
                if date_el is not None and date_el.text:
                    try:
                        # ISO8601形式をパース
                        dt_str = date_el.text.strip()
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        date = dt.astimezone(JST).strftime('%Y-%m-%d')
                    except Exception:
                        date = now_jst()[:10]
                else:
                    date = now_jst()[:10]

                if not title or not url:
                    continue
                if not is_relevant(title):
                    continue

                articles.append({
                    "source":  "Reddit",
                    "lang":    "EN",
                    "title":   title,
                    "url":     url,
                    "date":    date,
                    "summary": "",
                    "score":   0,
                })

        except ElementTree.ParseError as e:
            print(f"    XML解析エラー: {e}")

        time.sleep(2)

    # 重複除去
    seen, unique = set(), []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    print(f"[fetch] Reddit RSS: {len(unique)}件取得")
    return unique

# ============================================================
# ② Fandom Wiki API（ゲーム攻略情報・安定動作）
# ============================================================
def fetch_fandom():
    print("\n[fetch] Fandom Wiki から情報収集中...")
    articles = []

    # ★ Dada Survivor の Fandom Wiki（存在しない場合は0件でスキップ）
    base = "https://dada-survivor.fandom.com"
    api  = f"{base}/api.php?action=query&list=allpages&aplimit=20&apnamespace=0&format=json"

    r = safe_get(api)
    if r is None:
        print("    Fandom Wiki: 取得失敗 → スキップ")
        return []

    try:
        data  = r.json()
        pages = data.get("query", {}).get("allpages", [])
        print(f"    Fandom Wiki: {len(pages)}ページ取得")

        for page in pages:
            title = page.get("title", "").strip()
            if not title:
                continue
            page_url = f"{base}/wiki/{requests.utils.quote(title.replace(' ', '_'))}"

            articles.append({
                "source":  "Fandom Wiki",
                "lang":    "EN",
                "title":   title,
                "url":     page_url,
                "date":    now_jst()[:10],
                "summary": "Dada Survivor Wiki の攻略ページ",
                "score":   0,
            })
            time.sleep(0.3)

    except Exception as e:
        print(f"    Fandom Wiki 解析エラー: {e}")

    print(f"[fetch] Fandom: {len(articles)}件取得")
    return articles

# ============================================================
# メイン（失敗時も空JSONを必ず生成）
# ============================================================
def main():
    print("=" * 50)
    print(f"[fetch] 攻略情報収集開始: {now_jst()}")
    print("=" * 50)

    articles = []

    try:
        articles += fetch_reddit_rss()
    except Exception as e:
        print(f"[fetch] Reddit RSS 予期せぬエラー: {e}")

    try:
        articles += fetch_fandom()
    except Exception as e:
        print(f"[fetch] Fandom 予期せぬエラー: {e}")

    # スコア降順ソート
    articles.sort(key=lambda x: -x.get("score", 0))

    output = {
        "generated_at": now_jst(),
        "total":        len(articles),
        "articles":     articles,
    }

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    if articles:
        print(f"\n[fetch] ✅ articles.json 生成完了（{len(articles)}件）")
        print("\n[fetch] 取得記事プレビュー（上位3件）:")
        for a in articles[:3]:
            print(f"  [{a['source']}] {a['title'][:60]}")
    else:
        print("\n[fetch] ⚠️ 全ソース取得失敗。空のarticles.jsonを生成（デプロイは続行）")

if __name__ == "__main__":
    main()
