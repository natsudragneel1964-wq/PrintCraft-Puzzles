// Genera branding/avatar.png (800x800) y branding/banner.png (2560x1440)
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const css = `*{margin:0;box-sizing:border-box}body{font-family:"Inter Display","Inter",sans-serif;font-weight:900;color:#fff;overflow:hidden;
background:linear-gradient(180deg,#0a0520 0%,#3b0f63 42%,#c2267a 72%,#ff8a3c 100%)}
.sun{position:absolute;border-radius:50%;background:linear-gradient(180deg,#fff27a,#ffb23f 40%,#ff3d9a);
-webkit-mask:repeating-linear-gradient(180deg,#000 0 9%,transparent 9% 12%)}
.t{position:absolute;left:0;right:0;text-align:center;font-style:italic;text-shadow:0 0 40px #ff3d9a,0 8px 0 rgba(0,0,0,.5)}
.tag{position:absolute;left:50%;transform:translateX(-50%) skewX(-8deg);background:#ffb23f;color:#0b0618;white-space:nowrap}`;
const avatar = `<style>${css}body{width:800px;height:800px}</style>
<div class="sun" style="left:150px;top:230px;width:500px;height:500px"></div>
<div class="t" style="top:150px;font-size:210px;letter-spacing:-8px;line-height:.9">RADIO</div>
<div class="tag" style="top:390px;font-size:92px;padding:6px 30px;border-radius:14px;letter-spacing:2px">LEONIDA</div>
<div class="t" style="top:560px;font-size:64px;letter-spacing:10px;font-style:normal">GTA 6</div>`;
const banner = `<style>${css}body{width:2560px;height:1440px}</style>
<div class="sun" style="left:880px;top:420px;width:800px;height:800px;opacity:.55"></div>
<div class="t" style="top:520px;font-size:230px;letter-spacing:-6px;line-height:1">RADIO LEONIDA</div>
<div class="tag" style="top:790px;font-size:64px;padding:12px 40px;border-radius:14px;letter-spacing:6px">TODO SOBRE GTA 6 · CADA DÍA</div>
<div class="t" style="top:905px;font-size:30px;font-style:normal;font-weight:600;text-shadow:none;opacity:.8">Canal de fans · No afiliado a Rockstar Games</div>`;
(async () => {
  const out = path.join(__dirname, '..', 'branding'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  for (const [name, html, w, h] of [['avatar', avatar, 800, 800], ['banner', banner, 2560, 1440]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.setContent(html); await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(out, name + '.png') });
  }
  await b.close();
})();
