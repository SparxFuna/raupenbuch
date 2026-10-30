#!/usr/bin/env python3
"""Erzeugt die Rand-Komplikationen (Bögen wie bei Samsung-Zifferblättern) und setzt sie in watchface.xml ein.
Aufruf: python3 watchface/tools/complications.py"""
import math, os, re
XML = os.path.join(os.path.dirname(__file__), "../src/main/res/raw/watchface.xml")
C, R, TH = 225, 205, 12                     # Mitte, Radius der Bogenmitte, Strichstärke
DARK, TRACK = "#ff1f3d2d", "#4d1f3d2d"      # aktiv: dunkelgrün auf hellem Grund
AMB, AMBTR = "#ffffffff", "#55ffffff"       # Always-on: weiß auf schwarz
SLOTS = [  # id, Start-, Endwinkel (0° = oben, im Uhrzeigersinn), Name, Standard
    (0, 282, 348, "slot_tl", "STEP_COUNT", "SHORT_TEXT"),
    (1,  12,  78, "slot_tr", "WATCH_BATTERY", "RANGED_VALUE"),
    (2, 102, 168, "slot_br", "SUNRISE_SUNSET", "SHORT_TEXT"),
    (3, 192, 258, "slot_bl", "EMPTY", "EMPTY"),
]
FRAC = "(clamp([COMPLICATION.RANGED_VALUE_VALUE], [COMPLICATION.RANGED_VALUE_MIN], [COMPLICATION.RANGED_VALUE_MAX]) - [COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN])"

def both(fn):  # normal + Always-on-Kopie
    return fn(DARK, TRACK, 255, 0) + fn(AMB, AMBTR, 0, 255)

def arc(a0, a1, color, extra=""):
    return f'<Arc centerX="{C}" centerY="{C}" width="{2*R}" height="{2*R}" startAngle="{a0}" endAngle="{a1}"><Stroke thickness="{TH}" color="{color}" cap="ROUND"/>{extra}</Arc>'

def track(a0, a1):
    return both(lambda fg, tr, al, va: f'''
        <PartDraw x="0" y="0" width="450" height="450" alpha="{al}"><Variant mode="AMBIENT" target="alpha" value="{va}"/>{arc(a0, a1, tr)}</PartDraw>''')

def progress(a0, a1):
    end = f'<Transform target="endAngle" value="{a0} + {FRAC} * {a1-a0}"/>'
    return both(lambda fg, tr, al, va: f'''
        <PartDraw x="0" y="0" width="450" height="450" alpha="{al}"><Variant mode="AMBIENT" target="alpha" value="{va}"/>{arc(a0, a1, fg, end)}</PartDraw>
        <PartDraw x="0" y="0" width="450" height="450" alpha="{al}"><Variant mode="AMBIENT" target="alpha" value="{va}"/>
          <Ellipse x="{C-8}" y="{C-R-8}" width="16" height="16"><Fill color="#ffffffff"/><Stroke thickness="2" color="{fg}"/></Ellipse>
          <Transform target="angle" value="{a0} + {FRAC} * {a1-a0}"/>
        </PartDraw>''')

def icon(a0, size=30):
    a = math.radians(a0 - 10); x = C + R*math.sin(a) - size/2; y = C - R*math.cos(a) - size/2
    return both(lambda fg, tr, al, va: f'''
        <PartImage x="{x:.0f}" y="{y:.0f}" width="{size}" height="{size}" tintColor="{fg}" alpha="{al}"><Variant mode="AMBIENT" target="alpha" value="{va}"/>
          <Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/>
        </PartImage>''')

def text(a0, a1):
    bottom = 90 < (a0 + a1)/2 < 270
    if bottom:  # unten gegen den Uhrzeigersinn, damit die Schrift lesbar bleibt
        d, s, e, dia = "COUNTER_CLOCKWISE", a0 + 44, a0 + 4, 2*192
    else:
        d, s, e, dia = "CLOCKWISE", a0 + 4, a0 + 44, 2*176
    return both(lambda fg, tr, al, va: f'''
        <PartText x="0" y="0" width="450" height="450" alpha="{al}"><Variant mode="AMBIENT" target="alpha" value="{va}"/>
          <TextCircular centerX="{C}" centerY="{C}" width="{dia}" height="{dia}" startAngle="{s}" endAngle="{e}" direction="{d}" align="CENTER" ellipsis="TRUE">
            <Font family="SYNC_TO_DEVICE" size="26" weight="BOLD" color="{fg}"><Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template></Font>
          </TextCircular>
        </PartText>''')

def slot(sid, a0, a1, name, prov, ptype):
    return f'''
    <ComplicationSlot x="0" y="0" width="450" height="450" slotId="{sid}" displayName="{name}" supportedTypes="RANGED_VALUE SHORT_TEXT MONOCHROMATIC_IMAGE EMPTY">
      <DefaultProviderPolicy defaultSystemProvider="{prov}" defaultSystemProviderType="{ptype}"/>
      <BoundingArc centerX="{C}" centerY="{C}" width="{2*R}" height="{2*R}" thickness="44" startAngle="{a0-18}" endAngle="{a1}"/>
      <Complication type="RANGED_VALUE">{track(a0, a1)}{progress(a0, a1)}{icon(a0)}{text(a0, a1)}
      </Complication>
      <Complication type="SHORT_TEXT">{track(a0, a1)}{icon(a0)}{text(a0, a1)}
      </Complication>
      <Complication type="MONOCHROMATIC_IMAGE">{track(a0, a1)}{icon(a0, 34)}
      </Complication>
    </ComplicationSlot>'''

s = open(XML).read()
block = "\n    <!-- KOMPLIKATIONEN (erzeugt von tools/complications.py) -->" + "".join(slot(*x) for x in SLOTS) + "\n    <!-- /KOMPLIKATIONEN -->\n"
if "<!-- KOMPLIKATIONEN" in s:
    s = re.sub(r"\n    <!-- KOMPLIKATIONEN.*?<!-- /KOMPLIKATIONEN -->\n", lambda m: block, s, flags=re.S)
else:
    s = re.sub(r"\n    <!-- Komplikationen:.*?(?=  </Scene>)", "", s, flags=re.S)
    s = s.replace("  </Scene>", block + "  </Scene>")
open(XML, "w").write(s)
print("ok", len(s))
