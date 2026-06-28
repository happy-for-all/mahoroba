"""
fetch_articles.py ― まほろば！攻略情報 自動収集スクリプト v4.0
===========================================================
情報源：
  ① せにろぐ（senilog.com）カテゴリ別RSS
     ダダサバイバー攻略記事を日本語で安定取得
失敗時も空JSONを生成してデプロイを止めません。
===========================================================
"""

import json, time, re, requests
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree
from email.utils import parsedate_to_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ja,en;q=0.9",
}
TIMEOUT = 20
JST = timezone(timedelta(hours=9))

# ============================================================
# 取得対象 RSS フィード一覧
# senilog.com は WordPress → カテゴリURL末尾に /feed/ をつけるだけ
# ============================================================
RSS_SOURCES = [
    {
        "name":   "せにろぐ｜ダダサバイバー攻略",
        "url":    "https://www.senilog.com/category/%E3%82%B2%E3%83%BC%E3%83%A0/%E3%83%80%E3%83%80%E3%82%B5%E3%83%90%E3%82%A4%E3%83%90%E3%83%BC/feed/",
        "source": "せにろぐ",
        "lang":   "JP",
    },
    {
        "name":   "せにろぐ｜アップデート情報",
        "url":    "https://www.senilog.com/category/%E3%82%B2%E3%83%BC%E3%83%A0/%E3%83%80%E3%83%80%E3%82%B5%E3%83%90%E3%82%A4%E3%83%90%E3%83%BC/%E3%82%A2%E3%83%83%E3%83%97%E3%83%87%E3%83%BC%E3%83%88%E6%83%85%E5%A0%B1%E3%80%90%E3%83%80%E3%83%80%E3%82%B5%E3%83%90%E3%82%A4%E3%83%90%E3%83%BC%E3%80%91/feed/",
        "source": "せにろぐ",
        "lang":   "JP",
    },
    {
        "name":   "せにろぐ｜初心者向け",
        "url":    "https://www.senilog.com/category/%E3%82%B2%E3%83%BC%E3%83%A0/%E3%83%80%E3%83%80%E3%82%B5%E3%83%90%E3%82%A4%E3%83%90%E3%83%BC/%E5%88%9D%E5%BF%83%E8%80%85%E5%90%91%E3%81%91%E3%80%90%E3%83%80%E3%83%80%E3%82%B5%E3%83%90%E3%82%A4%E3%83%90%E3%83%BC%E3%80%91/feed/",
        "source": "せにろぐ",
        "lang":   "JP",
    },
    {
        "name":   "せにろぐ｜イベント攻略",
        "url":    "https://www.senilog.com/category/%E3%82%B2%E3%83%BC%E3%83%A0/%E3%83%80%E3%83%80%E3%82%B5%E3%83%90%E3%82%A4%E3%83%90%E3%83%BC/%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88%E6%94%BB%E7%95%A5%E3%80%90%E3%83%80%E3%83%80%E3%82%B5%E3%83%90%E3%82%A4%E3%83%90%E3%83%BC%E3%80%91/feed/",
        "source": "せにろぐ",
        "lang":   "JP",
    },
]

def now_jst():
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M')

def parse_date(text):
    """RFC2822 / ISO8601 両対応の日付パーサー"""
    if not text:
        return now_jst()[:10]
    text = text.strip()
    # RFC2822（WordPress標準）
    try:
        dt = parsedate_to_datetime(text)
        return dt.astimezone(JST).strftime('%Y-%m-%d')
    except Exception:
        pass
    # ISO8601
    try:
        dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
        return dt.astimezone(JST).strftime('%Y-%m-%d')
    except Exception:
        pass
    return now_jst()[:10]

def strip_html(text):
    """HTMLタグとエンティティを除去して読みやすいプレーンテキストに"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&quot;', '"').replace('&#039;', "'").replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ============================================================
# リトライ付きGET
# ============================================================
def safe_get(url, retries=2, wait=5):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            print(f"    HTTP {r.status_code} ← {url[:70]}")
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                print(f"    [429] レート制限 → {wait}秒待機 ({i+1}/{retries})")
                time.sleep(wait)
                wait *= 2
                continue
            print(f"    HTTP {r.status_code} → スキップ")
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
# RSS 2.0 パーサー（WordPressの標準形式）
# ============================================================
def parse_rss2(content_bytes, source_name, lang):
    """RSS 2.0 形式のXMLをパースして記事リストを返す"""
    articles = []
    try:
        root = ElementTree.fromstring(content_bytes)
    except ElementTree.ParseError as e:
        print(f"    XML解析エラー: {e}")
        return articles

    for item in root.findall('.//item'):
        # タイトル
        title_el = item.find('title')
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        # URL
        link_el = item.find('link')
        url = link_el.text.strip() if link_el is not None and link_el.text else ""

        # 日付
        date_el = item.find('pubDate')
        date = parse_date(date_el.text if date_el is not None else "")

        # 概要（description から HTMLタグ除去）
        desc_el = item.find('description')
        summary = ""
        if desc_el is not None and desc_el.text:
            summary = strip_html(desc_el.text)[:120].strip()
            if len(strip_html(desc_el.text)) > 120:
                summary += "…"

        if title and url:
            articles.append({
                "source":  source_name,
                "lang":    lang,
                "title":   title,
                "url":     url,
                "date":    date,
                "summary": summary,
                "score":   0,
            })

    return articles

# ============================================================
# メイン
# ============================================================
def main():
    print("=" * 50)
    print(f"[fetch] 攻略情報収集開始: {now_jst()}")
    print("=" * 50)

    all_articles = []

    for src in RSS_SOURCES:
        print(f"\n[fetch] 取得中: {src['name']}")
        try:
            r = safe_get(src["url"])
            if r is None:
                print(f"    → スキップ")
                continue

            articles = parse_rss2(r.content, src["source"], src["lang"])
            print(f"    → {len(articles)}件パース成功")
            all_articles += articles

        except Exception as e:
            print(f"    → 予期せぬエラー: {e}")

        time.sleep(2)  # サーバー負荷軽減

    # 重複除去（URLで判定）
    seen, unique = set(), []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    # 日付降順ソート（新しい記事が上）
    unique.sort(key=lambda x: x.get("date", ""), reverse=True)

    output = {
        "generated_at": now_jst(),
        "total":        len(unique),
        "articles":     unique,
    }

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    if unique:
        print(f"\n[fetch] ✅ articles.json 生成完了（{len(unique)}件）")
        print("\n[fetch] 取得記事プレビュー（上位5件）:")
        for a in unique[:5]:
            print(f"  [{a['source']}] {a['date']} | {a['title'][:50]}")
    else:
        print("\n[fetch] ⚠️ 全ソース取得失敗。空のarticles.jsonを生成（デプロイは続行）")

if __name__ == "__main__":
    main()
