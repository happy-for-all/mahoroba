"""
fetch_articles.py ― まほろば！攻略情報 自動収集スクリプト v3.0
===========================================================
情報源：
  ① Reddit RSS（キーワードフィルタ廃止・検索結果をそのまま取得）
  ② はてなブックマーク RSS（日本語・安定・公開API）
失敗時も空JSONを生成してデプロイを止めません。
===========================================================
"""

import json, time, requests
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {
    "User-Agent": UA,
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
TIMEOUT = 20
JST = timezone(timedelta(hours=9))

def now_jst():
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M')

def parse_date(text):
    """日付文字列をYYYY-MM-DD形式に変換"""
    if not text:
        return now_jst()[:10]
    text = text.strip()
    # ISO8601形式（RedditのAtom）
    for fmt in [
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S+00:00',
    ]:
        try:
            dt = datetime.strptime(text[:25], fmt[:len(fmt)])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(JST).strftime('%Y-%m-%d')
        except Exception:
            pass
    # RFC2822形式（はてなのRSS 2.0）
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(text)
        return dt.astimezone(JST).strftime('%Y-%m-%d')
    except Exception:
        pass
    return now_jst()[:10]

# ============================================================
# リトライ付きGET
# ============================================================
def safe_get(url, retries=2, wait=6):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            print(f"    HTTP {r.status_code} ← {url[:70]}")
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
# XML/RSSパーサー共通関数
# ============================================================
def parse_rss_entries(content_bytes):
    """
    AtomとRSS2.0の両形式に対応した汎用パーサー。
    [{title, url, date, summary}] を返す。
    """
    items = []
    try:
        root = ElementTree.fromstring(content_bytes)
    except ElementTree.ParseError as e:
        print(f"    XML解析エラー: {e}")
        return items

    ns_atom = 'http://www.w3.org/2005/Atom'

    # --- Atom形式（Reddit） ---
    entries = root.findall(f'.//{{{ns_atom}}}entry')
    if entries:
        for entry in entries:
            title_el = entry.find(f'{{{ns_atom}}}title')
            title    = title_el.text.strip() if title_el is not None and title_el.text else ""

            link_el  = entry.find(f'{{{ns_atom}}}link')
            url      = link_el.get('href', '') if link_el is not None else ""

            date_el  = (entry.find(f'{{{ns_atom}}}updated') or
                        entry.find(f'{{{ns_atom}}}published'))
            date     = parse_date(date_el.text if date_el is not None else "")

            summary_el = entry.find(f'{{{ns_atom}}}summary')
            summary    = ""
            if summary_el is not None and summary_el.text:
                # HTMLタグを除去
                import re
                summary = re.sub(r'<[^>]+>', '', summary_el.text).strip()[:150]

            if title and url:
                items.append({
                    "title": title, "url": url,
                    "date": date, "summary": summary,
                })
        return items

    # --- RSS 2.0形式（はてな等） ---
    for item in root.findall('.//item'):
        title_el = item.find('title')
        title    = title_el.text.strip() if title_el is not None and title_el.text else ""

        link_el  = item.find('link')
        url      = link_el.text.strip() if link_el is not None and link_el.text else ""

        date_el  = item.find('pubDate')
        date     = parse_date(date_el.text if date_el is not None else "")

        desc_el  = item.find('description')
        summary  = ""
        if desc_el is not None and desc_el.text:
            import re
            summary = re.sub(r'<[^>]+>', '', desc_el.text).strip()[:150]

        if title and url:
            items.append({
                "title": title, "url": url,
                "date": date, "summary": summary,
            })

    return items

# ============================================================
# ① Reddit RSS
# 検索クエリで既に絞り込み済みのため is_relevant() フィルタ不要
# ============================================================
def fetch_reddit_rss():
    print("\n[fetch] ① Reddit RSS から情報収集中...")
    articles = []

    queries = [
        ("Dada+Survivor",          "EN"),
        ("Dada+Survivor+guide",    "EN"),
        ("Dada+Survivor+tier",     "EN"),
    ]

    for query, lang in queries:
        url = f"https://www.reddit.com/search.rss?q={query}&sort=new&limit=8"
        r   = safe_get(url)
        if r is None:
            continue

        entries = parse_rss_entries(r.content)
        print(f"    「{query}」: {len(entries)}件パース成功")

        for e in entries:
            articles.append({
                "source":  "Reddit",
                "lang":    lang,
                "title":   e["title"],
                "url":     e["url"],
                "date":    e["date"],
                "summary": e["summary"],
                "score":   0,
            })

        time.sleep(3)  # 429対策：間隔を3秒に延長

    # 重複除去
    seen, unique = set(), []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    print(f"[fetch] Reddit RSS: {len(unique)}件（重複除去後）")
    return unique

# ============================================================
# ② はてなブックマーク RSS
# 公開RSS・CI環境でのブロックなし・日本語情報に強い
# ============================================================
def fetch_hatena():
    print("\n[fetch] ② はてなブックマーク RSS から情報収集中...")
    articles = []

    # 検索キーワード一覧（日本語）
    queries = [
        "ダダサバイバー",
        "ダダサバ 攻略",
        "ダダサバ ギルド",
    ]

    for query in queries:
        url = (
            "https://b.hatena.ne.jp/search/text"
            f"?q={requests.utils.quote(query)}&mode=rss&sort=recent"
        )
        r = safe_get(url)
        if r is None:
            continue

        entries = parse_rss_entries(r.content)
        print(f"    「{query}」: {len(entries)}件パース成功")

        for e in entries:
            articles.append({
                "source":  "はてなブックマーク",
                "lang":    "JP",
                "title":   e["title"],
                "url":     e["url"],
                "date":    e["date"],
                "summary": e["summary"],
                "score":   0,
            })

        time.sleep(2)

    # 重複除去
    seen, unique = set(), []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    print(f"[fetch] はてな: {len(unique)}件（重複除去後）")
    return unique

# ============================================================
# メイン
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
        articles += fetch_hatena()
    except Exception as e:
        print(f"[fetch] はてな 予期せぬエラー: {e}")

    # 日付降順ソート（新しい記事が上に来る）
    articles.sort(key=lambda x: x.get("date", ""), reverse=True)

    output = {
        "generated_at": now_jst(),
        "total":        len(articles),
        "articles":     articles,
    }

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    if articles:
        print(f"\n[fetch] ✅ articles.json 生成完了（{len(articles)}件）")
        print("\n[fetch] 取得記事プレビュー（上位5件）:")
        for a in articles[:5]:
            print(f"  [{a['source']}][{a['lang']}] {a['title'][:55]}")
    else:
        print("\n[fetch] ⚠️ 全ソース取得失敗。空のarticles.jsonを生成（デプロイは続行）")

if __name__ == "__main__":
    main()
