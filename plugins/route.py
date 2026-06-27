#(c) CodeXBotz / Advanced File Share Bot

from aiohttp import web

from config import AMAZON_LINK, VERIFY_MIN_SECONDS
from database.database import save_verification_click, save_verification_return
from helper_func import verify_verification_token

routes = web.RouteTableDef()


VERIFY_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Verification</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; background: #101820; color: #f7f7f7; }
    main { min-height: 100vh; display: grid; place-items: center; padding: 24px; box-sizing: border-box; }
    section { width: min(460px, 100%); }
    h1 { font-size: 28px; margin: 0 0 10px; }
    p { color: #c8d0d8; line-height: 1.55; }
    button, a { width: 100%; border: 0; border-radius: 8px; padding: 14px 16px; font-weight: 700; font-size: 16px; cursor: pointer; box-sizing: border-box; }
    a { display: block; text-align: center; text-decoration: none; background: #ffb703; color: #141414; margin: 18px 0 12px; }
    button { background: #2dd4bf; color: #082f2c; }
    .status { min-height: 28px; margin-top: 14px; color: #dbeafe; }
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Verify Access</h1>
      <p>Open the sponsor link once, return here, and verification will complete automatically after a short check.</p>
      <a id="amazon" href="__AMAZON_LINK__" target="_blank" rel="noopener">Open Amazon Link</a>
      <button id="check">I Returned, Verify Now</button>
      <p class="status" id="status"></p>
    </section>
  </main>
  <script>
    const params = new URLSearchParams(location.search);
    const user = params.get("user");
    const payload = params.get("payload") || "";
    const token = params.get("token");
    const statusEl = document.getElementById("status");
    const tg = window.Telegram && window.Telegram.WebApp;
    if (tg) tg.ready();

    async function api(path) {
      const res = await fetch(path, {method: "POST"});
      return await res.json();
    }
    async function markClick() {
      statusEl.textContent = "Link opened. Come back here to finish verification.";
      await api(`/api/verify-click?user=${encodeURIComponent(user)}&payload=${encodeURIComponent(payload)}&token=${encodeURIComponent(token)}`);
    }
    async function verify() {
      statusEl.textContent = "Checking verification...";
      const data = await api(`/api/verify-return?user=${encodeURIComponent(user)}&payload=${encodeURIComponent(payload)}&token=${encodeURIComponent(token)}`);
      if (data.verified) {
        statusEl.textContent = "Verified. Return to Telegram and tap the file link again.";
        if (tg) setTimeout(() => tg.close(), 1200);
      } else {
        statusEl.textContent = `Please keep the link open for at least __MIN_SECONDS__ seconds.`;
      }
    }
    document.getElementById("amazon").addEventListener("click", markClick);
    document.getElementById("check").addEventListener("click", verify);
    window.addEventListener("focus", () => setTimeout(verify, 3500));
  </script>
</body>
</html>"""


@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"status": "ok", "service": "advanced-file-share-bot"})


@routes.get("/health", allow_head=True)
async def health(request):
    return web.json_response({"status": "ok"})


@routes.get("/verify", allow_head=True)
async def verify_page(request):
    user_id = request.query.get("user", "")
    payload = request.query.get("payload", "")
    token = request.query.get("token", "")
    if not user_id.isdigit() or not verify_verification_token(int(user_id), payload, token):
        return web.Response(text="Invalid verification link", status=403)
    html = VERIFY_HTML.replace("__AMAZON_LINK__", AMAZON_LINK).replace("__MIN_SECONDS__", str(VERIFY_MIN_SECONDS))
    return web.Response(text=html, content_type="text/html")


@routes.post("/api/verify-click")
async def verify_click(request):
    user_id = request.query.get("user", "")
    payload = request.query.get("payload", "")
    token = request.query.get("token", "")
    if not user_id.isdigit() or not verify_verification_token(int(user_id), payload, token):
        return web.json_response({"ok": False}, status=403)
    await save_verification_click(int(user_id), token, request.remote)
    return web.json_response({"ok": True})


@routes.post("/api/verify-return")
async def verify_return(request):
    user_id = request.query.get("user", "")
    payload = request.query.get("payload", "")
    token = request.query.get("token", "")
    if not user_id.isdigit() or not verify_verification_token(int(user_id), payload, token):
        return web.json_response({"ok": False}, status=403)
    verified, spent = await save_verification_return(int(user_id), token, VERIFY_MIN_SECONDS)
    return web.json_response({"ok": True, "verified": verified, "time_spent": spent})
