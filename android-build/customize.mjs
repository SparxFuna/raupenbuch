// Passt das von „npx cap add android“ erzeugte Projekt an: Version, Icons, Startbild, Kamera, Signatur.
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const root = path.resolve("..");                  // Repo-Hauptordner (Web-App)
const app = path.resolve("android/app");
const res = path.join(app, "src/main/res");

// Version aus der Web-App: 5.32.0 -> versionName 5.32.0, versionCode 503200
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const ver = (html.match(/const APP_VERSION = "(\d+\.\d+\.\d+)"/) || [])[1];
if (!ver) throw new Error("APP_VERSION nicht gefunden");
const [a, b, c] = ver.split(".").map(Number);
const code = a * 100000 + b * 100 + c;
let gradle = fs.readFileSync(path.join(app, "build.gradle"), "utf8");
gradle = gradle.replace(/versionCode \d+/, `versionCode ${code}`).replace(/versionName "[^"]*"/, `versionName "${ver}"`);
// Signatur mit festem Schlüssel (aus GitHub-Secret), damit Updates über die alte App installiert werden können
gradle += `
android {
    signingConfigs {
        release {
            if (file('release.p12').exists()) {
                storeFile file('release.p12')
                storeType 'pkcs12'
                storePassword System.getenv('RB_KS_PASS')
                keyAlias 'raupenbuch'
                keyPassword System.getenv('RB_KS_PASS')
            }
        }
    }
    buildTypes { release { if (file('release.p12').exists()) { signingConfig signingConfigs.release } } }
}
`;
fs.writeFileSync(path.join(app, "build.gradle"), gradle);

// Berechtigungen: Kamera (QR-Scanner, Eier-Foto)
const mf = path.join(app, "src/main/AndroidManifest.xml");
let m = fs.readFileSync(mf, "utf8");
if (!m.includes("android.permission.CAMERA")) m = m.replace('<uses-permission android:name="android.permission.INTERNET" />', '<uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="android.permission.CAMERA" />');
fs.writeFileSync(mf, m);

// Icons aus den Web-App-Icons
const maskable = path.join(root, "icon-maskable.png"), plain = path.join(root, "icon-512.png");
const bg = [...(await sharp(maskable).extract({ left: 2, top: 2, width: 1, height: 1 }).removeAlpha().raw().toBuffer())];
const hex = "#" + bg.slice(0, 3).map(x => x.toString(16).padStart(2, "0")).join("");
fs.writeFileSync(path.join(res, "values/ic_launcher_background.xml"), `<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">${hex}</color>\n</resources>\n`);
const D = { mdpi: 1, hdpi: 1.5, xhdpi: 2, xxhdpi: 3, xxxhdpi: 4 };
for (const [d, f] of Object.entries(D)) {
  const dir = path.join(res, `mipmap-${d}`); fs.mkdirSync(dir, { recursive: true });
  const leg = Math.round(48 * f), fg = Math.round(108 * f);
  await sharp(plain).resize(leg, leg).png().toFile(path.join(dir, "ic_launcher.png"));
  const circle = Buffer.from(`<svg width="${leg}" height="${leg}"><circle cx="${leg / 2}" cy="${leg / 2}" r="${leg / 2}"/></svg>`);
  await sharp(maskable).resize(leg, leg).composite([{ input: circle, blend: "dest-in" }]).png().toFile(path.join(dir, "ic_launcher_round.png"));
  await sharp(maskable).resize(fg, fg).png().toFile(path.join(dir, "ic_launcher_foreground.png"));
}
// Startbild: Icon mittig auf dunklem Grund (ersetzt das Capacitor-Logo)
for (const dir of fs.readdirSync(res).filter(x => x.startsWith("drawable"))) {
  const f = path.join(res, dir, "splash.png"); if (!fs.existsSync(f)) continue;
  const { width, height } = await sharp(f).metadata();
  const s = Math.round(Math.min(width, height) * 0.28);
  const icon = await sharp(plain).resize(s, s).png().toBuffer();
  await sharp({ create: { width, height, channels: 4, background: "#121411" } }).composite([{ input: icon, gravity: "centre" }]).png().toFile(f + ".tmp");
  fs.renameSync(f + ".tmp", f);
}
console.log(`Raupenbuch ${ver} (versionCode ${code}), Icon-Hintergrund ${hex}`);
