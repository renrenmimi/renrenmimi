#!/usr/bin/env python3
"""
Regenerate the profile header SVGs from live GitHub data.

Draws the last 12 months of contributions as a ridge of weekly bars, with the dog
running across it — each bar lights up as she steps on it and stays lit, so the whole
ridge is glowing by the time she reaches the far end.

Two files are written, one per colour scheme; README picks between them with <picture>.
The dog is inlined as base64 so the SVG has no external references at all — SVGs loaded
through <img> run in "secure animated processing mode", which allows declarative
animation (SMIL and CSS) but forbids external resources.

Run:  GITHUB_TOKEN=... python3 scripts/gen_header.py
"""
from __future__ import annotations

import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

USER = os.environ.get("GITHUB_USER", "renrenmimi")
ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Counted by hand, so they need a nudge when the picture changes:
# 3 shipped web apps + 7 course sites + 18 toys + the portfolio itself.
LIVE_SITES = 29

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount weekday } }
      }
    }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC) {
      totalCount
    }
  }
}
"""


def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER}-profile-header",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(f"GraphQL error: {payload['errors']}")
    user = payload["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]
    return weeks, cal["totalContributions"], user["repositories"]["totalCount"]


# ── palette ────────────────────────────────────────────────────────────────
# Sampled off the dog: cream coat, warm charcoal, caramel nose.
THEMES = {
    "light": dict(ink="#2B2420", sub="#6F6458", faint="#9C9184", accent="#B07F52",
                  hair="#E2D4C0", bar="#DCC7A8", barhi="#A56D3B", base="#E3D8C7",
                  shadow="#CDBFA9"),
    "dark":  dict(ink="#EDE4D8", sub="#9C9184", faint="#6E6459", accent="#DFB684",
                  hair="#4A3F33", bar="#463829", barhi="#F0C68E", base="#2A231B",
                  shadow="#0A0806"),
}

LINES = ["frontend / full-stack engineer",
         "I turn what I just learned into something you can click",
         "open to new-grad and full-stack roles, SF Bay Area"]
DUR, TCYC = 4.4, 13.2

# ── geometry ───────────────────────────────────────────────────────────────
X0, PITCH, BW = 72.0, 19.5, 13.0
BASE_Y, MAXH, STUB = 336.0, 100.0, 3.0
RUN, LOOP = 9.6, 13.6          # dog crosses in RUN, whole cycle is LOOP
DOG_R, LIFT = 22.0, 22.0
K_HOLD, K_OFF = 0.815, 0.885   # ridge stays lit until, then goes dark


def bar_h(v, peak):
    return STUB + (v / peak) * (MAXH - STUB) if v else STUB


def bars(c, series, peak):
    n = len(series)
    out = []
    for i, v in enumerate(series):
        x, h = X0 + i * PITCH, bar_h(v, peak)
        y = BASE_Y - h
        t = (i / (n - 1)) * RUN
        # Every pulse rides the LOOP timeline. Giving each bar its own short dur with
        # repeatCount="indefinite" instead would make them blink on their own schedule,
        # completely decoupled from where the dog actually is.
        k_on = t / LOOP
        k_peak = min((t + 0.14) / LOOP, K_HOLD - 0.002)
        k_dn = min((t + 0.95) / LOOP, 0.998)
        kt_c = f"0;{k_on:.4f};{k_peak:.4f};{K_HOLD};{K_OFF};1"
        kt_p = f"0;{k_on:.4f};{k_peak:.4f};{k_dn:.4f};1"
        pop = 8.0
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{BW}" height="{h:.1f}" rx="3" fill="{c["bar"]}">'
            f'<animate attributeName="fill" '
            f'values="{c["bar"]};{c["bar"]};{c["barhi"]};{c["barhi"]};{c["bar"]};{c["bar"]}" '
            f'keyTimes="{kt_c}" dur="{LOOP}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{y:.1f};{y:.1f};{y-pop:.1f};{y:.1f};{y:.1f}" '
            f'keyTimes="{kt_p}" dur="{LOOP}s" repeatCount="indefinite" calcMode="spline" '
            f'keySplines=".2 0 .3 1;.3 0 .5 1;0 0 1 1;0 0 1 1"/>'
            f'<animate attributeName="height" values="{h:.1f};{h:.1f};{h+pop:.1f};{h:.1f};{h:.1f}" '
            f'keyTimes="{kt_p}" dur="{LOOP}s" repeatCount="indefinite" calcMode="spline" '
            f'keySplines=".2 0 .3 1;.3 0 .5 1;0 0 1 1;0 0 1 1"/>'
            f'</rect>')
    return "\n      ".join(out)


def dog_track(series, peak):
    n = len(series)
    pts, kts = [], []
    for i, v in enumerate(series):
        pts.append(f"{X0 + i*PITCH + BW/2:.1f} {BASE_Y - bar_h(v, peak) - LIFT:.1f}")
        kts.append(f"{(i/(n-1))*(RUN/LOOP):.4f}")
    pts.append(pts[-1])          # wait at the far end until the cycle restarts
    kts.append("1")
    return ";".join(pts), ";".join(kts)


def subtitles(tn):
    out = []
    for i, text in enumerate(LINES):
        b = i * DUR
        # Each line must be held at 0 before its turn — without the leading hold the
        # value interpolates up from keyTime 0 and all three lines overlap.
        kt = ";".join(f"{v:.4f}" for v in
                      [0, b/TCYC, (b+.40)/TCYC, (b+DUR-.55)/TCYC, (b+DUR-.15)/TCYC, 1])
        out.append(
            f'      <text x="0" y="0" class="sub-{tn}" opacity="0">{text}\n'
            f'        <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" '
            f'dur="{TCYC}s" repeatCount="indefinite"/>\n'
            f'        <animate attributeName="x" values="7;7;0;0;0;0" keyTimes="{kt}" '
            f'dur="{TCYC}s" repeatCount="indefinite"/>\n'
            f'      </text>')
    return "\n".join(out)


def stats_block(tn, stats):
    out = []
    for k, (num, label, x) in enumerate(stats):
        out.append(
            f'  <g opacity="0">\n'
            f'    <animate attributeName="opacity" values="0;1" dur=".8s" '
            f'begin="{1.15 + k*0.15:.2f}s" fill="freeze"/>\n'
            f'    <text class="num-{tn}"  x="{x}" y="102">{num}</text>\n'
            f'    <text class="nlab-{tn}" x="{x}" y="122">{label}</text>\n'
            f'  </g>')
    return "\n".join(out)


def build(c, tn, series, total, repos, dog_b64):
    peak = max(series) or 1
    n = len(series)
    dv, dk = dog_track(series, peak)
    hop = "; ".join("0 " + ("-5" if i % 2 else "0") for i in range(23))
    stats = [(str(repos), "PUBLIC REPOS", 800),
             (str(LIVE_SITES), "LIVE SITES", 925),
             (str(total), "CONTRIBUTIONS", 1020)]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 1200 360" width="1200" height="360" role="img"
     aria-label="Weiren Feng, frontend and full-stack engineer in the SF Bay Area. {total} contributions in the last twelve months.">
  <title>Weiren Feng — frontend / full-stack engineer</title>
  <desc>My dog running across my real GitHub contribution history, one week per step.</desc>
  <defs>
    <clipPath id="dogClip-{tn}"><circle cx="0" cy="0" r="{DOG_R-1}"/></clipPath>
    <linearGradient id="rule-{tn}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{c['accent']}" stop-opacity=".9"/>
      <stop offset="45%"  stop-color="{c['accent']}" stop-opacity=".38"/>
      <stop offset="100%" stop-color="{c['accent']}" stop-opacity="0"/>
    </linearGradient>
    <style>
      .name-{tn} {{ font:700 58px Georgia,'Iowan Old Style','Times New Roman',serif; fill:{c['ink']}; letter-spacing:-1.1px; }}
      .sub-{tn}  {{ font:400 18.5px 'Segoe UI',-apple-system,Helvetica,Arial,sans-serif; fill:{c['sub']}; }}
      .meta-{tn} {{ font:600 12px ui-monospace,'SF Mono',Menlo,Consolas,monospace; fill:{c['accent']}; letter-spacing:2.7px; }}
      .num-{tn}  {{ font:700 30px Georgia,'Iowan Old Style',serif; fill:{c['ink']}; }}
      .nlab-{tn} {{ font:400 10.5px ui-monospace,'SF Mono',Menlo,Consolas,monospace; fill:{c['faint']}; letter-spacing:1.3px; }}
      .axis-{tn} {{ font:400 10px ui-monospace,'SF Mono',Menlo,Consolas,monospace; fill:{c['faint']}; letter-spacing:1px; }}
    </style>
  </defs>

  <g transform="translate(72,0)">
    <text class="meta-{tn}" x="0" y="48" opacity="0">SAN FRANCISCO BAY AREA &#183; OPEN TO WORK
      <animate attributeName="opacity" values="0;1" dur=".7s" begin=".1s" fill="freeze"/>
    </text>
    <text class="name-{tn}" x="0" y="104" opacity="0">Weiren Feng
      <animate attributeName="opacity" values="0;1" dur=".9s" begin=".3s" fill="freeze"/>
      <animateTransform attributeName="transform" type="translate" values="0 12;0 0" dur=".9s" begin=".3s" fill="freeze"/>
    </text>
    <rect x="0" y="126" width="0" height="2" rx="1" fill="url(#rule-{tn})">
      <animate attributeName="width" values="0;420" dur="1.1s" begin=".8s" fill="freeze"/>
    </rect>
    <g transform="translate(0,162)">
{subtitles(tn)}
      <rect x="-15" y="-13" width="2.4" height="16.5" rx="1.2" fill="{c['accent']}">
        <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.45;.5;.95;1" dur="1.1s" repeatCount="indefinite"/>
      </rect>
    </g>
  </g>

{stats_block(tn, stats)}

  <g>
      {bars(c, series, peak)}
  </g>
  <rect x="{X0}" y="{BASE_Y}" width="{(n-1)*PITCH+BW:.0f}" height="1.4" fill="{c['base']}"/>
  <text class="axis-{tn}" x="{X0}" y="{BASE_Y+18:.0f}">52 WEEKS AGO</text>
  <text class="axis-{tn}" x="{X0+(n-1)*PITCH+BW:.0f}" y="{BASE_Y+18:.0f}" text-anchor="end">TODAY &#183; weekly commits</text>

  <g opacity="0">
    <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.05;.755;.815;1" dur="{LOOP}s" repeatCount="indefinite"/>
    <animateTransform attributeName="transform" type="translate" values="{dv}" keyTimes="{dk}"
                      dur="{LOOP}s" repeatCount="indefinite"/>
    <g>
      <animateTransform attributeName="transform" type="translate" values="{hop}" dur="{RUN}s"
                        repeatCount="indefinite" calcMode="spline" keySplines="{';'.join(['.35 0 .45 1']*22)}"/>
      <ellipse cx="0" cy="{LIFT-2:.0f}" rx="15" ry="3" fill="{c['shadow']}" opacity=".4"/>
      <circle cx="0" cy="0" r="{DOG_R+1.6:.1f}" fill="none" stroke="{c['hair']}" stroke-width="2.4"/>
      <image xlink:href="data:image/jpeg;base64,{dog_b64}" x="{-DOG_R:.0f}" y="{-DOG_R:.0f}"
             width="{DOG_R*2:.0f}" height="{DOG_R*2:.0f}"
             clip-path="url(#dogClip-{tn})" preserveAspectRatio="xMidYMid slice"/>
    </g>
  </g>
</svg>
'''


def main():
    series, total, repos = fetch()
    dog_b64 = base64.b64encode((ASSETS / "dog.jpg").read_bytes()).decode()
    for tn, colors in THEMES.items():
        path = ASSETS / f"header-{tn}.svg"
        path.write_text(build(colors, tn, series, total, repos, dog_b64), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}  ({path.stat().st_size/1024:.1f} KB)")
    print(f"{total} contributions · {repos} public repos · peak week {max(series)}")


if __name__ == "__main__":
    main()
