"""
build.py ― まほろば！（ダダサバイバー ギルド紹介サイト）ビルドスクリプト
===========================================================================
処理フロー：
  1. dist/ ディレクトリを初期化
  2. ファイル群を dist/ にコピー
  3. index.html の MD5ハッシュを生成して _cache_bust.txt に記録
  4. ビルド完了サマリーを表示
===========================================================================
"""

import os
import shutil
import hashlib
import sys
from datetime import datetime, timezone, timedelta

# ============================================================
# 定数
# ============================================================
DIST_DIR   = 'dist'
INDEX_HTML = 'index.html'
JST        = timezone(timedelta(hours=9))

# コピー対象ファイル一覧
FILES_TO_COPY = [INDEX_HTML, 'style.css', 'script.js', 'articles.json']

# ============================================================
# ユーティリティ
# ============================================================

def now_jst() -> str:
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M')

def md5_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# ============================================================
# メイン処理
# ============================================================

def build():
    print('=' * 60)
    print(f'[build] まほろば！ビルド開始: {now_jst()}')
    print('=' * 60)

    # --- dist/ 初期化 ---
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)
    print(f'[build] {DIST_DIR}/ を初期化しました')

    # --- index.html の存在確認（必須ファイル）---
    if not os.path.exists(INDEX_HTML):
        print(f'[build] ❌ エラー: {INDEX_HTML} が見つかりません')
        sys.exit(1)  # 明示的に終了（raiseより安全）

    # --- ファイル群を dist/ にコピー ---
   
    for file_name in FILES_TO_COPY:
        if os.path.exists(file_name):
            dest = os.path.join(DIST_DIR, file_name)
            shutil.copy2(file_name, dest)
            print(f'[build] {file_name} → {DIST_DIR}/ にコピー完了')
        else:
            print(f'[build] ⚠️ 警告: {file_name} が見つからないためスキップしました')

    # 👑 追加：images フォルダを丸ごとコピーする処理
    IMAGES_DIR = 'images'
    if os.path.exists(IMAGES_DIR):
        dest_images = os.path.join(DIST_DIR, IMAGES_DIR)
        shutil.copytree(IMAGES_DIR, dest_images)
        print(f'[build] 📁 {IMAGES_DIR}/ → {DIST_DIR}/ に丸ごとコピー完了')

    # --- MD5ハッシュ生成（index.html を基準に固定）---
    # ★ dest変数バグ修正：ループ変数に依存せず index.html のパスを直接指定
    index_dest = os.path.join(DIST_DIR, INDEX_HTML)
    file_hash = md5_file(index_dest)
    cache_bust_path = os.path.join(DIST_DIR, '_cache_bust.txt')
    with open(cache_bust_path, 'w', encoding='utf-8') as f:
        f.write(file_hash)
    print(f'[build] キャッシュバスト用ハッシュ: {file_hash}')

    # --- dist/ の中身を確認（デプロイ前の最終確認）---
    print(f'[build] dist/ の内容:')
    for f in sorted(os.listdir(DIST_DIR)):
        size = os.path.getsize(os.path.join(DIST_DIR, f))
        print(f'[build]   {f} ({size:,} bytes)')

    # --- 完了サマリー ---
    print('=' * 60)
    print(f'[build] ✅ ビルド完了: {now_jst()}')
    print(f'[build] 出力先: {DIST_DIR}/{INDEX_HTML}')
    print('=' * 60)

# ============================================================
# エントリーポイント
# ============================================================

if __name__ == '__main__':
    build()
