"""
build.py ― まほろば！（ダダサバイバー ギルド紹介サイト）ビルドスクリプト
===========================================================================
処理フロー：
  1. dist/ ディレクトリを初期化
  2. index.html を dist/ にコピー
  3. MD5ハッシュを生成して _cache_bust.txt に記録
  4. ビルド完了サマリーを表示
===========================================================================
"""

import os
import shutil
import hashlib
from datetime import datetime, timezone, timedelta

# ============================================================
# 定数
# ============================================================
DIST_DIR   = 'dist'
INDEX_HTML = 'index.html'
JST        = timezone(timedelta(hours=9))

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

    # --- index.html の存在確認 ---
    if not os.path.exists(INDEX_HTML):
        print(f'[build] ❌ エラー: {INDEX_HTML} が見つかりません')
        raise FileNotFoundError(f'{INDEX_HTML} not found')

    # --- index.html を dist/ にコピー ---
    # --- ファイル群を dist/ にコピー ---
    # ★ ここに css と js を追加します（デグレ防止アドオン）
    files_to_copy = [INDEX_HTML, 'style.css', 'script.js']
    
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            dest = os.path.join(DIST_DIR, file_name)
            shutil.copy2(file_name, dest)
            print(f'[build] {file_name} → {DIST_DIR}/ にコピー完了')
        else:
            print(f'[build] ⚠️ 警告: {file_name} が見つからないためスキップしました')

    # --- MD5ハッシュ生成（CDNキャッシュ破棄用）---
    file_hash = md5_file(dest)
    cache_bust_path = os.path.join(DIST_DIR, '_cache_bust.txt')
    with open(cache_bust_path, 'w', encoding='utf-8') as f:
        f.write(file_hash)
    print(f'[build] キャッシュバスト用ハッシュ: {file_hash}')

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
