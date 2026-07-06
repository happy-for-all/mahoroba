// ============================================================
// まほろば！ Cloudflare Worker
// 役割：① 通常アクセス→静的サイト配信　② /api/chat→AI BOTへ中継
// ============================================================

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // ------------------------------------------------------------
    // ① チャットBOT中継エンドポイント（/api/chat への POST のみ処理）
    // ------------------------------------------------------------
    if (url.pathname === '/api/chat' && request.method === 'POST') {
      try {
        const userBody = await request.json();

        // 🔴【要調整】知人のBOTの「入力形式」に合わせて、ここを調整してください
        const webhookPayload = {
          message: userBody.message ?? ''
        };

        const botResponse = await fetch(env.BOT_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(webhookPayload)
        });

        if (!botResponse.ok) {
          throw new Error(`BOT応答エラー: HTTP ${botResponse.status}`);
        }

        const data = await botResponse.json();

        // 🔴【要調整】知人のBOTの「出力形式」に合わせて、ここを調整してください
        const replyText =
          data.reply ?? data.answer ?? data.text ?? data.output ?? data.message
          ?? JSON.stringify(data);

        return new Response(JSON.stringify({ reply: replyText }), {
          headers: { 'Content-Type': 'application/json' }
        });

      } catch (err) {
        console.error('[chat relay error]', err);
        return new Response(
          JSON.stringify({ reply: '申し訳ございません、只今BOTに接続できませんでした。' }),
          { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // ------------------------------------------------------------
    // ② それ以外は通常どおり静的ファイルを配信
    // ------------------------------------------------------------
    return env.ASSETS.fetch(request);
  }
};
