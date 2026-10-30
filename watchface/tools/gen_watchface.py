#!/usr/bin/env python3
"""Erzeugt watchface.xml (Raupi-Zifferblatt) und die Schriften in res/font.
Wird beim Bauen (GitHub Actions) automatisch aufgerufen:  python3 watchface/tools/gen_watchface.py"""
import math, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
RES = os.path.join(HERE, "../src/main/res")

# ---- Schriften: aus den Web-Schriften der App (woff2) werden TTF-Dateien für die Uhr ----
FONTS = [  # id, Anzeigename (String-Ressource), Familie, Datei im Repo, Gewicht für die Uhr
    ("0", "font_system", "SYNC_TO_DEVICE", None, "BOLD"),
    ("1", "font_plex", "raupi_plex", "ibm-plex-sans-latin-600-normal.woff2", "NORMAL"),
    ("2", "font_mono", "raupi_mono", "ibm-plex-mono-latin-500-normal.woff2", "NORMAL"),
    ("3", "font_serif", "raupi_serif", "spectral-latin-600-normal.woff2", "NORMAL"),
    ("4", "font_italic", "raupi_italic", "spectral-latin-600-italic.woff2", "NORMAL"),
]
def make_fonts():
    from fontTools.ttLib import TTFont
    os.makedirs(os.path.join(RES, "font"), exist_ok=True)
    for _, _, fam, src, _ in FONTS:
        if src:
            f = TTFont(os.path.join(ROOT, src)); f.flavor = None
            f.save(os.path.join(RES, "font", fam + ".ttf"))

# ---- Lage der Uhrzeit ----
LAYOUTS = [  # id, Name, y Uhrzeit, Größe, y Datum
    ("0", "pos_top", 70, 92, 182),
    ("1", "pos_low", 112, 86, 216),
    ("2", "pos_big", 62, 104, 192),
]
DARK, DATE_C = "#ff1f3d2d", "#ff2f5a43"

def vis(active):  # sichtbar nur im normalen Modus bzw. nur im Always-on
    return ('alpha="255"', '<Variant mode="AMBIENT" target="alpha" value="0"/>') if active else ('alpha="0"', '<Variant mode="AMBIENT" target="alpha" value="255"/>')

def clock(fam, weight, y, size, dy):
    out = []
    for active in (True, False):
        a, v = vis(active)
        w = weight if active else ("THIN" if fam == "SYNC_TO_DEVICE" else weight)
        col = DARK if active else "#ffffffff"
        out.append(f'''          <DigitalClock x="0" y="0" width="450" height="450" {a}>{v}
            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="0" y="{y}" width="450" height="{int(size*1.22)}">
              <Font family="{fam}" size="{size}" weight="{w}" color="{col}"/>
            </TimeText>
          </DigitalClock>
          <PartText x="0" y="{dy}" width="450" height="40" {a}>{v}
            <Text align="CENTER">
              <Font family="{fam}" size="28" color="{DATE_C if active else '#ffaaaaaa'}">
                <Template>%s, %s. %s<Parameter expression="[DAY_OF_WEEK_S]"/><Parameter expression="[DAY]"/><Parameter expression="[MONTH_S]"/></Template>
              </Font>
            </Text>
          </PartText>''')
    return "\n".join(out)

def clock_block():
    s = '    <ListConfiguration id="font">\n'
    for fid, _, fam, _, weight in FONTS:
        s += f'      <ListOption id="{fid}">\n        <Group x="0" y="0" width="450" height="450" name="font{fid}">\n          <ListConfiguration id="layout">\n'
        for lid, _, y, size, dy in LAYOUTS:
            s += f'          <ListOption id="{lid}">\n            <Group x="0" y="0" width="450" height="450" name="f{fid}l{lid}">\n{clock(fam, weight, y, size, dy)}\n            </Group>\n          </ListOption>\n'
        s += '          </ListConfiguration>\n        </Group>\n      </ListOption>\n'
    return s + '    </ListConfiguration>\n'

# ---- Komplikationen als Bögen am Rand; im Always-on ausgeblendet ----
C, R, TH = 225, 205, 12
TRACK = "#4d1f3d2d"
SLOTS = [  # id, Start-, Endwinkel (0° = oben, im Uhrzeigersinn), Name, Standard
    (0, 282, 348, "slot_tl", "STEP_COUNT", "SHORT_TEXT"),
    (1,  12,  78, "slot_tr", "WATCH_BATTERY", "RANGED_VALUE"),
    (2, 102, 168, "slot_br", "SUNRISE_SUNSET", "SHORT_TEXT"),
    (3, 192, 258, "slot_bl", "EMPTY", "EMPTY"),
]
HIDE = '<Variant mode="AMBIENT" target="alpha" value="0"/>'
FRAC = "(clamp([COMPLICATION.RANGED_VALUE_VALUE], [COMPLICATION.RANGED_VALUE_MIN], [COMPLICATION.RANGED_VALUE_MAX]) - [COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN])"
def arc(a0, a1, color, extra=""):
    return f'<Arc centerX="{C}" centerY="{C}" width="{2*R}" height="{2*R}" startAngle="{a0}" endAngle="{a1}"><Stroke thickness="{TH}" color="{color}" cap="ROUND"/>{extra}</Arc>'
def track(a0, a1):
    return f'\n        <PartDraw x="0" y="0" width="450" height="450">{HIDE}{arc(a0, a1, TRACK)}</PartDraw>'
def progress(a0, a1):
    t = f"{a0} + {FRAC} * {a1-a0}"
    return f'''
        <PartDraw x="0" y="0" width="450" height="450">{HIDE}{arc(a0, a1, DARK, f'<Transform target="endAngle" value="{t}"/>')}</PartDraw>
        <PartDraw x="0" y="0" width="450" height="450">{HIDE}
          <Ellipse x="{C-8}" y="{C-R-8}" width="16" height="16"><Fill color="#ffffffff"/><Stroke thickness="2" color="{DARK}"/></Ellipse>
          <Transform target="angle" value="{t}"/>
        </PartDraw>'''
def icon(a0, size=26, r=190):  # etwas nach innen, damit der Rand nichts abschneidet
    a = math.radians(a0 - 10); x = C + r*math.sin(a) - size/2; y = C - r*math.cos(a) - size/2
    return f'''
        <PartImage x="{x:.0f}" y="{y:.0f}" width="{size}" height="{size}" tintColor="{DARK}">{HIDE}
          <Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/>
        </PartImage>'''
def text(a0, a1):
    if 90 < (a0 + a1)/2 < 270: d, s, e, dia = "COUNTER_CLOCKWISE", a0 + 44, a0 + 4, 2*192
    else:                      d, s, e, dia = "CLOCKWISE", a0 + 4, a0 + 44, 2*176
    return f'''
        <PartText x="0" y="0" width="450" height="450">{HIDE}
          <TextCircular centerX="{C}" centerY="{C}" width="{dia}" height="{dia}" startAngle="{s}" endAngle="{e}" direction="{d}" align="CENTER" ellipsis="TRUE">
            <Font family="SYNC_TO_DEVICE" size="26" weight="BOLD" color="{DARK}"><Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template></Font>
          </TextCircular>
        </PartText>'''
def slot(sid, a0, a1, name, prov, ptype):
    return f'''
    <ComplicationSlot x="0" y="0" width="450" height="450" slotId="{sid}" displayName="{name}" supportedTypes="RANGED_VALUE SHORT_TEXT MONOCHROMATIC_IMAGE EMPTY">
      <DefaultProviderPolicy defaultSystemProvider="{prov}" defaultSystemProviderType="{ptype}"/>
      <BoundingArc centerX="{C}" centerY="{C}" width="{2*R}" height="{2*R}" thickness="44" startAngle="{a0-18}" endAngle="{a1}"/>
      <Complication type="RANGED_VALUE">{track(a0, a1)}{progress(a0, a1)}{icon(a0)}{text(a0, a1)}
      </Complication>
      <Complication type="SHORT_TEXT">{track(a0, a1)}{icon(a0)}{text(a0, a1)}
      </Complication>
      <Complication type="MONOCHROMATIC_IMAGE">{track(a0, a1)}{icon(a0, 30)}
      </Complication>
    </ComplicationSlot>'''

def watchface():
    opts = lambda items: "".join(f'\n      <ListOption id="{i}" displayName="{n}"/>' for i, n, *_ in items)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Raupi-Zifferblatt (Watch Face Format 1). ERZEUGT von watchface/tools/gen_watchface.py – dort ändern. -->
<WatchFace width="450" height="450">
  <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
  <Metadata key="PREVIEW_TIME" value="10:08:32"/>
  <UserConfigurations>
    <ListConfiguration id="font" displayName="cfg_font" defaultValue="0">{opts(FONTS)}
    </ListConfiguration>
    <ListConfiguration id="layout" displayName="cfg_layout" defaultValue="0">{opts(LAYOUTS)}
    </ListConfiguration>
  </UserConfigurations>
  <Scene backgroundColor="#ff000000">
    <PartImage x="0" y="0" width="450" height="450" name="bg">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Image resource="raupi_bg"/>
    </PartImage>

    <!-- Raupis Tag: wandern, tanzen, Ball spielen (Endlosschleife) -->
    <PartAnimatedImage x="45" y="238" width="360" height="149" name="raupi">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <AnimationController play="ON_VISIBLE" repeat="TRUE" resumePlayBack="TRUE" beforePlaying="FIRST_FRAME" afterPlaying="FIRST_FRAME"/>
      <AnimatedImage resource="raupi_day" format="WEBP" thumbnail="raupi_thumb"/>
    </PartAnimatedImage>
    <!-- Antippen: Herzchen -->
    <PartAnimatedImage x="45" y="238" width="360" height="149" name="hearts">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <AnimationController play="TAP" beforePlaying="HIDE" afterPlaying="HIDE"/>
      <AnimatedImage resource="raupi_hearts" format="WEBP" thumbnail="raupi_hearts_thumb"/>
    </PartAnimatedImage>
    <!-- Always-on: ruhende Raupi, gedimmt -->
    <PartImage x="45" y="238" width="360" height="149" name="raupi_ambient" alpha="0">
      <Variant mode="AMBIENT" target="alpha" value="255"/>
      <Image resource="raupi_ambient"/>
    </PartImage>

    <!-- Uhrzeit und Datum: Schriftart × Lage, auf der Uhr unter „Anpassen“ wählbar -->
{clock_block()}{"".join(slot(*x) for x in SLOTS)}
  </Scene>
</WatchFace>
'''

STRINGS = {"watch_face_name": "Raupi", "slot_tl": "Oben links", "slot_tr": "Oben rechts", "slot_br": "Unten rechts", "slot_bl": "Unten links",
           "cfg_font": "Schrift", "font_system": "Uhr-Standard", "font_plex": "Plex", "font_mono": "Plex Mono", "font_serif": "Spectral", "font_italic": "Spectral kursiv",
           "cfg_layout": "Uhrzeit", "pos_top": "Oben", "pos_low": "Etwas tiefer", "pos_big": "Groß"}

if __name__ == "__main__":
    open(os.path.join(RES, "raw/watchface.xml"), "w").write(watchface())
    open(os.path.join(RES, "values/strings.xml"), "w").write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n' + "".join(f'  <string name="{k}">{v}</string>\n' for k, v in STRINGS.items()) + "</resources>\n")
    try: make_fonts()
    except ImportError: print("fontTools fehlt – Schriften nicht erzeugt (pip install fonttools brotli)")
    print("watchface.xml erzeugt")
