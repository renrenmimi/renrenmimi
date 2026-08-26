#!/usr/bin/env python3
"""Generate three compact, independently clickable profile link buttons."""
from __future__ import annotations

from gen_workbench import ASSETS, font_faces


BG = "#0D0B20"
PANEL = "#171431"
INK = "#F7F4FF"
TEAL = "#4FD6C0"
BLUE = "#6EA8FF"
YELLOW = "#FFD75E"


def shell(label: str, width: int, background: str, button: str = "") -> str:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 78" width="{width}" height="78" role="img" aria-label="{label}">
      <title>{label}</title>
      <defs>
        <pattern id="scan" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="1" fill="{INK}" opacity=".018"/></pattern>
        <style>
          {font_faces()}
          .button{{font:700 17px 'Space Grotesk',sans-serif;letter-spacing:2.1px}}
        </style>
      </defs>
      {background}
      <rect width="{width}" height="78" fill="url(#scan)"/>
      {button}
    </svg>'''
    return "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"


def portfolio() -> str:
    background = ""
    button = f'''
      <rect x="2" y="2" width="368" height="64" rx="22" fill="{PANEL}" stroke="{TEAL}" stroke-width="1.5"/>
      <path d="M64 24h22a3 3 0 0 1 3 3v13a3 3 0 0 1-3 3H64a3 3 0 0 1-3-3V27a3 3 0 0 1 3-3z" fill="{TEAL}"/>
      <path d="M69 24v-4h12v4M61 32h28M73 31v3h4v-3" fill="none" stroke="{BG}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="190" y="40" text-anchor="middle" class="button" fill="{INK}">PORTFOLIO</text>
      <path d="M302 34h18m-8-8 8 8-8 8" fill="none" stroke="{TEAL}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'''
    return shell("Open portfolio", 372, background, button)


def linkedin() -> str:
    background = ""
    button = f'''
      <rect x="2" y="2" width="368" height="64" rx="22" fill="{PANEL}" stroke="{BLUE}" stroke-width="1.5"/>
      <rect x="65" y="24" width="19" height="19" rx="4" fill="{BLUE}"/>
      <text x="74.5" y="38.5" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" font-weight="700" fill="{BG}">in</text>
      <text x="190" y="40" text-anchor="middle" class="button" fill="{INK}">LINKEDIN</text>
      <path d="M302 34h18m-8-8 8 8-8 8" fill="none" stroke="{BLUE}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'''
    return shell("Open LinkedIn", 372, background, button)


def email() -> str:
    background = ""
    button = f'''
      <rect x="2" y="2" width="368" height="64" rx="22" fill="{PANEL}" stroke="{YELLOW}" stroke-width="1.5"/>
      <rect x="61" y="24" width="24" height="18" rx="2" fill="none" stroke="{YELLOW}" stroke-width="2"/>
      <path d="m63 26 10 8 10-8" fill="none" stroke="{YELLOW}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="187" y="40" text-anchor="middle" class="button" fill="{INK}">EMAIL</text>
      <path d="M302 34h18m-8-8 8 8-8 8" fill="none" stroke="{YELLOW}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'''
    return shell("Send email", 372, background, button)


def main() -> None:
    for name, content in {
        "dock-portfolio.svg": portfolio(),
        "dock-linkedin.svg": linkedin(),
        "dock-email.svg": email(),
    }.items():
        (ASSETS / name).write_text(content, encoding="utf-8")
    print("Generated three independently clickable profile link buttons.")


if __name__ == "__main__":
    main()
