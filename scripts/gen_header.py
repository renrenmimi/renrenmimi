#!/usr/bin/env python3
"""
Regenerate the profile header SVGs from live GitHub data.

Draws the last 26 weeks of contributions as a ridge of weekly bars, with the dog
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
# 4 shipped web apps (incl. kovaflooring.com) + 7 course sites + 18 toys + this portfolio.
LIVE_SITES = 30

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
    recent_weeks = weeks[-26:]
    return recent_weeks, sum(recent_weeks), user["repositories"]["totalCount"]


# ── palette ────────────────────────────────────────────────────────────────
# Achievement Arcade: deep violet cabinet, score-yellow highlights, teal active
# platforms, and muted purple platforms waiting for the dog to reach them.
THEMES = {
    "light": dict(bg="#171431", ink="#F5F3FF", sub="#C9C6E4", faint="#A9AFE6",
                  accent="#4FD6C0", accent2="#FFD75E", hair="#FFD75E",
                  bar="#454074", barhi="#43CDB7", base="#625DC2", grid="#8B86DD",
                  shadow="#070614", halo="#FFD75E", name_shadow="#5D3F8F"),
    "dark":  dict(bg="#0D0B20", ink="#F5F3FF", sub="#C5C1E0", faint="#969DCE",
                  accent="#4FD6C0", accent2="#FFD75E", hair="#FFD75E",
                  bar="#2B2851", barhi="#43CDB7", base="#5752AD", grid="#7772CE",
                  shadow="#030208", halo="#FFD75E", name_shadow="#4A3278"),
}

LINES = ["frontend / full-stack engineer",
         "I turn what I just learned into something you can click",
         "open to new-grad through mid-level roles \u00b7 Bay Area or Irvine"]
DUR, TCYC = 4.4, 13.2

# ── geometry ───────────────────────────────────────────────────────────────
X0, PITCH, BW = 72.0, 39.5, 28.0
BASE_Y, MAXH, STUB = 336.0, 116.0, 5.0
RUN, LOOP = 9.6, 13.6          # dog crosses in RUN, whole cycle is LOOP
DOG_R, LIFT = 30.0, 31.0
K_HOLD, K_OFF = 0.815, 0.885   # ridge stays lit until, then goes dark


def bar_h(v, peak):
    # One unusually busy week should read as a finale, not flatten the rest of
    # the level. Values above the 90th-percentile scale still reach the same
    # honest maximum height; the raw contribution total remains in the stats.
    return STUB + min(v / peak, 1.0) * (MAXH - STUB) if v else STUB


def visual_peak(series):
    active = sorted(v for v in series if v > 0)
    if not active:
        return 1
    return active[round((len(active) - 1) * .9)]


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
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{BW}" height="{h:.1f}" rx="5" fill="{c["bar"]}">'
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
            f'      <text x="0" y="0" class="sub-{tn}" opacity="{1 if i == 0 else 0}">{text}\n'
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
            f'  <g opacity="1">\n'
            f'    <animate attributeName="opacity" values="0;1" dur=".8s" '
            f'begin="{1.15 + k*0.15:.2f}s" fill="freeze"/>\n'
            f'    <text class="num-{tn}"  x="{x}" y="102">{num}</text>\n'
            f'    <text class="nlab-{tn}" x="{x}" y="122">{label}</text>\n'
            f'  </g>')
    return "\n".join(out)


def font_face():
    """Manrope, inlined as base64.
    A webfont fetched over the network would be blocked — SVGs loaded through <img>
    run in secure animated processing mode, which forbids external references, and
    the text would silently fall back to a system font."""
    out = []
    for w in (500, 700):
        b64 = base64.b64encode((ASSETS / f"Manrope-{w}.woff2").read_bytes()).decode()
        out.append(
            f"      @font-face {{ font-family:'Manrope'; font-style:normal; font-weight:{w}; "
            f"src:url(data:font/woff2;base64,{b64}) format('woff2'); }}")
    return "\n".join(out)


def build(c, tn, series, total, repos, dog_b64):
    peak = visual_peak(series)
    n = len(series)
    dv, dk = dog_track(series, peak)
    dog_x0, dog_y0 = dv.split(';')[0].split()
    hop = "; ".join("0 " + ("-5" if i % 2 else "0") for i in range(23))
    stats = [(str(repos), "PUBLIC REPOS", 800),
             (str(LIVE_SITES), "LIVE SITES", 925),
             (str(total), "CONTRIBUTIONS", 1020)]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 1200 360" width="1200" height="360" role="img"
     aria-label="Weiren Feng, frontend and full-stack engineer. Open to new-grad through mid-level roles in the SF Bay Area or Irvine, California. {total} contributions in the last 26 weeks.">
  <title>Weiren Feng — frontend / full-stack engineer</title>
  <desc>My dog running across my real GitHub contribution history, one week per step.</desc>
  <defs>
    <clipPath id="dogClip-{tn}"><circle cx="0" cy="0" r="{DOG_R-1}"/></clipPath>
    <linearGradient id="rule-{tn}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{c['accent2']}" stop-opacity=".95"/>
      <stop offset="45%"  stop-color="{c['accent']}" stop-opacity=".55"/>
      <stop offset="100%" stop-color="{c['accent']}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="scan-{tn}" width="6" height="6" patternUnits="userSpaceOnUse">
      <rect width="6" height="1" fill="{c['ink']}" opacity=".025"/>
    </pattern>
    <style>
{font_face()}
      .name-{tn} {{ font:700 56px 'Manrope',system-ui,-apple-system,'Segoe UI',sans-serif; fill:{c['ink']}; letter-spacing:-1.8px; filter:drop-shadow(4px 4px 0 {c['name_shadow']}); }}
      .sub-{tn}  {{ font:500 18px 'Manrope',system-ui,-apple-system,'Segoe UI',sans-serif; fill:{c['sub']}; }}
      .meta-{tn} {{ font:700 12.5px 'Manrope',system-ui,-apple-system,sans-serif; fill:{c['accent']}; letter-spacing:1.5px; }}
      .num-{tn}  {{ font:700 30px 'Manrope',system-ui,-apple-system,sans-serif; fill:{c['accent2']}; letter-spacing:-0.7px; }}
      .nlab-{tn} {{ font:500 10.5px 'Manrope',system-ui,-apple-system,sans-serif; fill:{c['faint']}; letter-spacing:1.2px; }}
      .axis-{tn} {{ font:500 10px 'Manrope',system-ui,-apple-system,sans-serif; fill:{c['faint']}; letter-spacing:1px; }}
    </style>
  </defs>

  <rect width="1200" height="360" fill="{c['bg']}"/>
  <rect width="1200" height="360" fill="url(#scan-{tn})"/>

  <g transform="translate(72,0)">
    <text class="meta-{tn}" x="0" y="48" opacity="1">SF BAY AREA / IRVINE, CA &#183; OPEN TO WORK
      <animate attributeName="opacity" values="0;1" dur=".7s" begin=".1s" fill="freeze"/>
    </text>
    <text class="name-{tn}" x="0" y="104" opacity="1">Weiren Feng
      <animate attributeName="opacity" values="0;1" dur=".9s" begin=".3s" fill="freeze"/>
      <animateTransform attributeName="transform" type="translate" values="0 12;0 0" dur=".9s" begin=".3s" fill="freeze"/>
    </text>
    <rect x="0" y="126" width="420" height="2" rx="1" fill="url(#rule-{tn})">
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
      <path d="M {X0} {BASE_Y-38} H {X0+(n-1)*PITCH+BW:.1f} M {X0} {BASE_Y-76} H {X0+(n-1)*PITCH+BW:.1f} M {X0} {BASE_Y-114} H {X0+(n-1)*PITCH+BW:.1f}"
            fill="none" stroke="{c['grid']}" stroke-width="1" stroke-dasharray="3 9" opacity=".18"/>
      {bars(c, series, peak)}
  </g>
  <rect x="{X0}" y="{BASE_Y}" width="{(n-1)*PITCH+BW:.0f}" height="1.4" fill="{c['base']}"/>
  <text class="axis-{tn}" x="{X0}" y="{BASE_Y+18:.0f}">LEVEL &#183; LAST 26 WEEKS</text>
  <text class="axis-{tn}" x="{X0+(n-1)*PITCH+BW:.0f}" y="{BASE_Y+18:.0f}" text-anchor="end">TODAY &#183; CONTRIBUTION RUN</text>

  <g opacity="1" transform="translate({dog_x0},{dog_y0})">
    <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.05;.755;.815;1" dur="{LOOP}s" repeatCount="indefinite"/>
    <animateTransform attributeName="transform" type="translate" values="{dv}" keyTimes="{dk}"
                      dur="{LOOP}s" repeatCount="indefinite"/>
    <g>
      <animateTransform attributeName="transform" type="translate" values="{hop}" dur="{RUN}s"
                        repeatCount="indefinite" calcMode="spline" keySplines="{';'.join(['.35 0 .45 1']*22)}"/>
      <ellipse cx="0" cy="{LIFT-2:.0f}" rx="15" ry="3" fill="{c['shadow']}" opacity=".4"/>
      <circle cx="0" cy="0" r="{DOG_R+6:.1f}" fill="{c['halo']}" opacity=".22"/>
      <circle cx="{-DOG_R-10:.0f}" cy="3" r="3" fill="{c['accent2']}" opacity="0">
        <animate attributeName="opacity" values="0;.9;0" dur=".7s" repeatCount="indefinite"/>
        <animate attributeName="r" values="1;4;1" dur=".7s" repeatCount="indefinite"/>
      </circle>
      <circle cx="{-DOG_R-4:.0f}" cy="14" r="2" fill="{c['accent']}" opacity="0">
        <animate attributeName="opacity" values=".8;0;.8" dur=".9s" repeatCount="indefinite"/>
      </circle>
      <circle cx="0" cy="0" r="{DOG_R+1:.1f}" fill="none" stroke="{c['hair']}" stroke-width="2"/>
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
