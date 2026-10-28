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
// ---- Wechselbare App-Icons: je Variante ein activity-alias, umgeschaltet vom Plugin „AppIcon“ ----
const ICONS = fs.readdirSync(path.join(root, "app-icons")).filter(f => f.endsWith(".svg")).map(f => f.slice(0, -4)).sort();
const any26 = path.join(res, "mipmap-anydpi-v26");
for (const v of ICONS) {
  const svg = fs.readFileSync(path.join(root, "app-icons", v + ".svg"), "utf8");
  // vollflächige Fassung mit Rand, damit die runde/eckige Maske des Launchers nichts Wichtiges abschneidet
  const bleed = svg.replace('viewBox="0 0 512 512" width="512" height="512"', 'viewBox="-80 -80 672 672" width="672" height="672"')
                   .replace('<rect width="512" height="512" rx="112"', '<rect x="-80" y="-80" width="672" height="672"');
  for (const [d, f] of Object.entries(D)) {
    const dir = path.join(res, `mipmap-${d}`);
    await sharp(Buffer.from(svg)).resize(Math.round(48 * f), Math.round(48 * f)).png().toFile(path.join(dir, `ic_icon_${v}.png`));
    await sharp(Buffer.from(bleed)).resize(Math.round(108 * f), Math.round(108 * f)).png().toFile(path.join(dir, `ic_icon_${v}_fg.png`));
  }
  fs.writeFileSync(path.join(any26, `ic_icon_${v}.xml`), `<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n    <background android:drawable="@android:color/black"/>\n    <foreground android:drawable="@mipmap/ic_icon_${v}_fg"/>\n</adaptive-icon>\n`);
}
const cap = s => s[0].toUpperCase() + s.slice(1);
const launcher = `<intent-filter>\n                <action android:name="android.intent.action.MAIN" />\n                <category android:name="android.intent.category.LAUNCHER" />\n            </intent-filter>`;
let man = fs.readFileSync(mf, "utf8");
if (!man.includes(launcher)) throw new Error("Launcher-Intent-Filter nicht gefunden");
man = man.replace(launcher, "");
const alias = (name, icon, round, on) => `
        <activity-alias android:name=".Icon${name}" android:targetActivity=".MainActivity" android:enabled="${on}" android:exported="true"
            android:label="@string/app_name" android:icon="${icon}" android:roundIcon="${round}">
            ${launcher}
        </activity-alias>`;
const aliases = alias("Klassisch", "@mipmap/ic_launcher", "@mipmap/ic_launcher_round", true) + ICONS.map(v => alias(cap(v), `@mipmap/ic_icon_${v}`, `@mipmap/ic_icon_${v}`, false)).join("");
man = man.replace(/(<\/activity>)/, `$1${aliases}`);
fs.writeFileSync(mf, man);
// Plugin + Registrierung in der MainActivity
const pkgDir = path.join(app, "src/main/java/de/sparxfuna/raupenbuch");
const names = ["Klassisch", ...ICONS.map(cap)];
fs.writeFileSync(path.join(pkgDir, "AppIconPlugin.java"), `package de.sparxfuna.raupenbuch;

import android.content.ComponentName;
import android.content.pm.PackageManager;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/** Wechselt das App-Icon, indem genau einer der activity-alias-Einträge aktiv ist. */
@CapacitorPlugin(name = "AppIcon")
public class AppIconPlugin extends Plugin {
    static final String[] ICONS = {${names.map(n => `"${n}"`).join(", ")}};

    private ComponentName cn(String n) { return new ComponentName(getContext().getPackageName(), "de.sparxfuna.raupenbuch.Icon" + n); }

    private String current() {
        PackageManager pm = getContext().getPackageManager();
        for (String n : ICONS) if (pm.getComponentEnabledSetting(cn(n)) == PackageManager.COMPONENT_ENABLED_STATE_ENABLED) return n;
        return "Klassisch";
    }

    @PluginMethod
    public void get(PluginCall call) {
        JSObject r = new JSObject(); JSArray a = new JSArray();
        for (String n : ICONS) a.put(n);
        r.put("current", current()); r.put("icons", a);
        call.resolve(r);
    }

    @PluginMethod
    public void set(PluginCall call) {
        String name = call.getString("name", "Klassisch");
        boolean known = false; for (String n : ICONS) if (n.equals(name)) known = true;
        if (!known) { call.reject("Unbekanntes Icon: " + name); return; }
        PackageManager pm = getContext().getPackageManager();
        pm.setComponentEnabledSetting(cn(name), PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
        for (String n : ICONS) if (!n.equals(name))
            pm.setComponentEnabledSetting(cn(n), PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
        JSObject r = new JSObject(); r.put("current", name); call.resolve(r);
    }
}
`);
fs.writeFileSync(path.join(pkgDir, "MainActivity.java"), `package de.sparxfuna.raupenbuch;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(AppIconPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
`);
console.log(`Raupenbuch ${ver} (versionCode ${code}), Icon-Hintergrund ${hex}, App-Icons: ${names.join(", ")}`);
