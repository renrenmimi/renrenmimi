#!/usr/bin/env python3
"""Add a restrained animated neon frame and rounded corners to the profile header."""
from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

EXTRA_DEFS = '''
    <clipPath id="headerRound"><rect x="3" y="3" width="1194" height="354" rx="22"/></clipPath>
    <linearGradient id="headerNeon" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1200" y2="0" spreadMethod="pad">
      <stop offset="0" stop-color="#4FD6C0"/>
      <stop offset=".30" stop-color="#4FD6C0"/>
      <stop offset=".48" stop-color="#6EA8FF"/>
      <stop offset=".64" stop-color="#8F7CF6"/>
      <stop offset=".82" stop-color="#FFD75E"/>
      <stop offset="1" stop-color="#FFD75E"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-180 0;180 0;-180 0" dur="11.5s" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .2 1;.4 0 .2 1"/>
    </linearGradient>
    <filter id="headerGlow" x="-20%" y="-30%" width="140%" height="160%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
'''

FRAME = '''
  <rect x="3" y="3" width="1194" height="354" rx="22" fill="none" stroke="#34305E" stroke-width="4" opacity=".72"/>
  <rect x="3" y="3" width="1194" height="354" rx="22" fill="none" stroke="url(#headerNeon)" stroke-width="5" opacity=".3" filter="url(#headerGlow)">
    <animate attributeName="opacity" values=".24;.40;.24" dur="4.8s" repeatCount="indefinite"/>
  </rect>
  <rect x="3" y="3" width="1194" height="354" rx="22" fill="none" stroke="url(#headerNeon)" stroke-width="1.9"/>
'''


def transform(source: str) -> str:
    head, body = source.split("</defs>", 1)
    body = body.rsplit("</svg>", 1)[0]
    return f"{head}{EXTRA_DEFS}</defs>\n  <g clip-path=\"url(#headerRound)\">{body}</g>\n{FRAME}</svg>"


def main() -> None:
    for theme in ("light", "dark"):
        source = (ASSETS / f"header-{theme}.svg").read_text(encoding="utf-8")
        (ASSETS / f"header-neon-{theme}.svg").write_text(transform(source), encoding="utf-8")
    print("Generated rounded neon profile headers.")


if __name__ == "__main__":
    main()
