# Raupenbuch

Zuchttagebuch für Raupen und Falter als offline-fähige Web-App (PWA).

**App:** https://sparxfuna.github.io/raupenbuch/

- Alle Daten liegen nur auf dem Gerät (IndexedDB, Fotos als Blobs). Backups als JSON-Datei mit Fotos unter *Mehr → Daten & Sicherung*.
- Bluetooth-Sensor Xiaomi LYWSD03MMC (Original-Firmware) im Tab *Klima* → Standort.
- Keine externen Abhängigkeiten: jsPDF 2.5.1, qrcode-generator 1.4.4, jsQR 1.4.0 und die Schriften (IBM Plex, Spectral; SIL OFL) liegen im Repo.

Bei Änderungen `VERSION` in `sw.js` erhöhen, damit installierte Apps das Update bekommen.
