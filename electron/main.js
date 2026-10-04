'use strict';
const { app, BrowserWindow, shell, session } = require('electron');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

const DIST = path.join(process.resourcesPath, 'dist');
const BUNDLED = path.join(process.resourcesPath, 'bundled-data');
const TITLE = 'WARDOGS Offline Calculator';
const PREFERRED_PORT = 47821; // fixed so saved targets/settings (localStorage) persist between launches

// archive file -> sub-folder of map-data it unpacks into (each tar holds one <map> folder)
const ARCHIVES = [
  ['tiles-zestafona.tar', 'maps/tiles'], ['tiles-bakurani.tar', 'maps/tiles'], ['tiles-ozeti.tar', 'maps/tiles'],
  ['tiles-color-zestafona.tar', 'maps/tiles-color'], ['tiles-color-bakurani.tar', 'maps/tiles-color'], ['tiles-color-ozeti.tar', 'maps/tiles-color']
];

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.webp': 'image/webp',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml',
  '.webmanifest': 'application/manifest+json', '.bin': 'application/octet-stream'
};

let mapData; // set after app ready
let splash = null;

function tarExe() {
  const sys = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tar.exe');
  return fs.existsSync(sys) ? sys : 'tar';
}
function run(cmd, args) {
  return new Promise((resolve, reject) => execFile(cmd, args, { windowsHide: true, maxBuffer: 1 << 24 }, (e) => (e ? reject(e) : resolve())));
}
function showSplash(text) {
  if (!splash) {
    splash = new BrowserWindow({ width: 440, height: 150, frame: false, resizable: false, alwaysOnTop: true, show: true,
      backgroundColor: '#0b0f14', webPreferences: { contextIsolation: true } });
  }
  const html = `<body style="margin:0;background:#0b0f14;color:#e6e6e6;font-family:Segoe UI,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh"><div style="font-size:16px">Setting up map data...</div><div style="margin-top:10px;font-size:13px;opacity:.75">${text}</div><div style="margin-top:10px;font-size:11px;opacity:.5">One-time setup, this can take a few minutes</div></body>`;
  splash.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html));
}
async function ensureMapData() {
  const pending = ARCHIVES.filter(([f, sub]) => {
    const marker = path.join(mapData, '.done-' + f);
    return !fs.existsSync(marker) && fs.existsSync(path.join(BUNDLED, f));
  });
  let i = 0;
  for (const [f, sub] of pending) {
    i++;
    showSplash(`Unpacking ${i} of ${pending.length}: ${f}`);
    const dest = path.join(mapData, sub);
    fs.mkdirSync(dest, { recursive: true });
    await run(tarExe(), ['-xf', path.join(BUNDLED, f), '-C', dest]);
    fs.writeFileSync(path.join(mapData, '.done-' + f), new Date().toISOString());
    try { fs.unlinkSync(path.join(BUNDLED, f)); } catch (_) { /* keep archive if it cannot be removed */ }
  }
  if (splash) { splash.close(); splash = null; }
}

function resolveFile(urlPath) {
  let p;
  try { p = decodeURIComponent(urlPath.split('?')[0].split('#')[0]); } catch (_) { return null; }
  p = path.posix.normalize('/' + p);
  const root = (p.startsWith('/maps/tiles/') || p.startsWith('/maps/tiles-color/')) ? mapData : DIST;
  let full = path.join(root, p);
  if (!full.startsWith(root)) return null;
  try {
    const st = fs.statSync(full);
    if (st.isDirectory()) full = path.join(full, 'index.html');
  } catch (_) { return null; }
  return fs.existsSync(full) ? full : null;
}

function startServer() {
  const server = http.createServer((req, res) => {
    const file = resolveFile(req.url || '/');
    if (!file) { res.writeHead(404, { 'Content-Type': 'text/plain' }); return res.end('Not found'); }
    const ext = path.extname(file).toLowerCase();
    const isTile = /[\\/]maps[\\/]tiles(-color)?[\\/]/.test(file);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream', 'Cache-Control': isTile ? 'public, max-age=31536000, immutable' : 'no-cache' });
    fs.createReadStream(file).on('error', () => res.destroy()).pipe(res);
  });
  return new Promise((resolve) => {
    server.once('error', () => server.listen(0, '127.0.0.1', () => resolve(server.address().port)));
    server.listen(PREFERRED_PORT, '127.0.0.1', () => resolve(server.address().port));
  });
}

function isLocal(url) {
  return /^(http:\/\/(127\.0\.0\.1|localhost)[:/]|data:|blob:|devtools:|file:|chrome-extension:)/i.test(url);
}

async function main() {
  mapData = path.join(app.getPath('userData'), 'map-data');
  fs.mkdirSync(mapData, { recursive: true });

  // Offline guarantee: the app never contacts anything outside this computer.
  session.defaultSession.webRequest.onBeforeRequest((details, cb) => cb({ cancel: !isLocal(details.url) }));

  await ensureMapData();
  const port = await startServer();

  const win = new BrowserWindow({
    width: 1440, height: 900, minWidth: 900, minHeight: 600, autoHideMenuBar: true, backgroundColor: '#0b0f14',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true, preload: path.join(__dirname, 'preload.js') }
  });
  win.setMenuBarVisibility(false);
  win.setTitle(TITLE);
  win.webContents.on('page-title-updated', (e) => e.preventDefault()); // keep our window title
  const external = (url) => { if (/^https?:\/\//i.test(url) && !isLocal(url)) shell.openExternal(url); };
  win.webContents.setWindowOpenHandler(({ url }) => { external(url); return { action: 'deny' }; });
  win.webContents.on('will-navigate', (e, url) => { if (!isLocal(url)) { e.preventDefault(); external(url); } });
  await win.loadURL(`http://127.0.0.1:${port}/`);
}

if (!app.requestSingleInstanceLock()) { app.quit(); }
else {
  app.whenReady().then(main).catch((err) => { console.error(err); app.quit(); });
  app.on('window-all-closed', () => app.quit());
}
