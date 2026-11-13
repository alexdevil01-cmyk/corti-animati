// Render delle assonometrie (three.js) e conversione SVG -> PNG / PDF con Playwright.
// Uso: node render.js <cartella con node_modules/three>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const TAV = path.join(ROOT, 'tavole');
const THREE_DIR = path.join(process.argv[2] || '.', 'node_modules', 'three');

const ISO_HTML = (boxes, mode) => `<!doctype html><html><body style="margin:0;background:#173d6e">
<script type="importmap">{"imports":{"three":"http://local/three/build/three.module.js"}}</script>
<script type="module">
import * as THREE from 'three';
const boxes = ${JSON.stringify(boxes)};
const mode = '${mode}';
const W = 1040, H = 1120;
const r = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
r.setSize(W, H); r.setClearColor(0x173d6e); document.body.appendChild(r.domElement);
const scene = new THREE.Scene();
const fill = {muro:0x2a5a98, solaio:0x3b6fb0, gradino:0x5a8fd0, pianerottolo:0x5a8fd0, ringhiera:0x9cc0ea,
  'scala-pioli':0xffd36b, marcapiano:0x2f63a5, cornicione:0x2f63a5, 'portone-chiuso':0x1d4478,
  'portone-aperto':0x1d4478, persiana:0x244f8a};
const front = new Set(['marcapiano','cornicione','persiana','portone-chiuso']);
for (const b of boxes) {
  if (mode === 'spaccato') {
    if (front.has(b.tag)) continue;
    if (b.name === 'facciata') continue;
    if (b.tag === 'solaio' && b.z0 > 14) continue;      // copertura rimossa
    if (b.name === 'comune-dx') continue;
    // taglio assonometrico a metà profondità: via muri e solai davanti a y = CUT
    const CUT = 4.6;
    if ((b.tag === 'muro' || b.tag === 'solaio') && b.z1 > 0.001) {
      if (b.y1 <= CUT) continue;
      if (b.y0 < CUT) b.y0 = CUT;
    }
    if (b.tag === 'portone-aperto') continue;
  }
  const g = new THREE.BoxGeometry(b.x1-b.x0, b.z1-b.z0, b.y1-b.y0);
  const m = new THREE.MeshBasicMaterial({color: fill[b.tag] ?? 0x3b6fb0, polygonOffset:true,
    polygonOffsetFactor:1, polygonOffsetUnits:1});
  const mesh = new THREE.Mesh(g, m);
  mesh.position.set((b.x0+b.x1)/2, (b.z0+b.z1)/2, -(b.y0+b.y1)/2);
  scene.add(mesh);
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(g),
    new THREE.LineBasicMaterial({color: b.tag==='scala-pioli' ? 0xffd36b : 0xeaf3ff}));
  e.position.copy(mesh.position); scene.add(e);
}
const s = 11.2;
const cam = new THREE.OrthographicCamera(-s*W/H, s*W/H, s, -s, -100, 200);
const target = new THREE.Vector3(6, 7.4, -5);
const dir = mode === 'spaccato' ? new THREE.Vector3(0.5, 0.42, 1) : new THREE.Vector3(0.62, 0.38, 1);
cam.position.copy(target).add(dir.normalize().multiplyScalar(60));
cam.lookAt(target);
r.render(scene, cam);
window.__done = true;
</script></body></html>`;

(async () => {
  const boxes = JSON.parse(fs.readFileSync(path.join(ROOT, 'modello', 'edificio.json'), 'utf8'));
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const mode = process.argv[3] || 'all';
  if (mode === 'all' || mode === 'iso') {
    const page = await browser.newPage({ viewport: { width: 1040, height: 1120 } });
    await page.route('http://local/**', (route) => {
      const rel = route.request().url().replace('http://local/three/', '');
      route.fulfill({ path: path.join(THREE_DIR, rel), contentType: 'application/javascript' });
    });
    for (const m of ['esterno', 'spaccato']) {
      await page.route('http://local/page.html', (route) =>
        route.fulfill({ body: ISO_HTML(boxes, m), contentType: 'text/html' }));
      await page.goto('http://local/page.html');
      await page.waitForFunction(() => window.__done === true, null, { timeout: 30000 });
      await page.locator('canvas').screenshot({ path: path.join(TAV, `_iso_${m}.png`) });
      await page.unroute('http://local/page.html');
      console.log('iso', m);
    }
    await page.close();
  }
  if (mode === 'all' || mode === 'sheets') {
    const svgs = fs.readdirSync(TAV).filter((f) => f.startsWith('tav') && f.endsWith('.svg')).sort();
    const page = await browser.newPage({ viewport: { width: 1680, height: 1188 }, deviceScaleFactor: 2 });
    for (const f of svgs) {
      await page.goto('file://' + path.join(TAV, f));
      await page.screenshot({ path: path.join(TAV, f.replace('.svg', '.png')) });
      console.log('png', f);
    }
    // PDF unico A3 orizzontale
    const imgs = svgs.map((f) => `<div class="p"><img src="file://${path.join(TAV, f)}"></div>`).join('');
    const html = `<!doctype html><html><head><style>@page{size:420mm 297mm;margin:0}
      body{margin:0}.p{width:420mm;height:297mm;page-break-after:always;overflow:hidden}
      .p img{width:100%;height:100%;display:block}</style></head><body>${imgs}</body></html>`;
    const tmp = path.join(TAV, '_pdf.html');
    fs.writeFileSync(tmp, html);
    await page.goto('file://' + tmp);
    await page.waitForTimeout(500);
    await page.pdf({ path: path.join(ROOT, 'blueprint_edificio_tre_portoni.pdf'), width: '420mm', height: '297mm',
      printBackground: true });
    fs.unlinkSync(tmp);
    console.log('pdf ok');
  }
  await browser.close();
})();
