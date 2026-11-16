// Uso: node render.js <id> [--still t1,t2,...]   Renderiza work/<id>.json(+wav) -> videos/<id>.mp4 y covers/<id>.jpg
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const FPS = 30, root = path.join(__dirname, '..');

(async () => {
  const id = process.argv[2];
  const si = process.argv.indexOf('--still');
  const tl = JSON.parse(fs.readFileSync(path.join(root, 'work', id + '.json'), 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'template.html'));
  await page.evaluate(t => window.init(t), tl);
  if (si > 0) {
    for (const t of process.argv[si + 1].split(',')) {
      await page.evaluate(x => window.render(x), +t);
      await page.screenshot({ path: path.join(root, 'work', `${id}_${t}.jpg`), type: 'jpeg', quality: 80 });
    }
    await browser.close(); return;
  }
  for (const d of ['videos', 'covers']) fs.mkdirSync(path.join(root, d), { recursive: true });
  await page.evaluate(x => window.render(x), Math.min(tl.scenes[0].end - 0.4, 1.6));
  await page.screenshot({ path: path.join(root, 'covers', id + '.jpg'), type: 'jpeg', quality: 92 });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', path.join(root, 'work', id + '.wav'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-r', String(FPS), '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-shortest', '-movflags', '+faststart',
    path.join(root, 'videos', id + '.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.floor(tl.dur * FPS);
  for (let f = 0; f < n; f++) {
    await page.evaluate(x => window.render(x), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('ok', id, tl.dur + 's');
})();
