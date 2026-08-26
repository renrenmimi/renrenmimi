#!/usr/bin/env python3
"""Generate the animated workbench strip from real public GitHub commits."""
from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import pathlib
import subprocess
import urllib.parse
from dataclasses import dataclass
from zoneinfo import ZoneInfo


ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
USER = os.environ.get("GITHUB_USER", "renrenmimi")
PACIFIC = ZoneInfo("America/Los_Angeles")

# Deliberately public portfolio projects only. Classroom, empty, client-internal,
# and miscellaneous repositories never enter the generated profile strip.
PROJECTS = (
    "RepoTimeMachine",
    "BugMuseum",
    "DrillLab",
    "greenlane",
    "PetNote",
    "ToneDown",
    "DataData",
    "AlgoAlgo",
    "apier",
    "tser",
    "RedisVisual",
    "AgentLab",
    "SwiftLab",
    "iCanDoIt",
    "renren-across-tabs",
    "avatar-dash",
)

THEMES = {
    "light": {
        "bg": "#171431",
        "card": "#211D43",
        "card2": "#1B2543",
        "ink": "#F7F4FF",
        "sub": "#BDB8DA",
        "faint": "#7772A3",
        "line": "#37315F",
        "teal": "#4FD6C0",
        "yellow": "#FFD75E",
        "purple": "#8F7CF6",
    },
    "dark": {
        "bg": "#0D0B20",
        "card": "#171431",
        "card2": "#121A31",
        "ink": "#F7F4FF",
        "sub": "#B8B3D4",
        "faint": "#6E6997",
        "line": "#2B2851",
        "teal": "#4FD6C0",
        "yellow": "#FFD75E",
        "purple": "#8F7CF6",
    },
}


@dataclass(frozen=True)
class Commit:
    repo: str
    sha: str
    subject: str
    authored_at: dt.datetime


@dataclass(frozen=True)
class Snapshot:
    latest: Commit
    previous_project: Commit
    recent_commits: tuple[Commit, ...]
    seven_day_commits: int
    seven_day_projects: int
    fetched_at: dt.datetime


def github_token() -> str:
    if token := os.environ.get("GITHUB_TOKEN"):
        return token
    # Local previews can reuse gh's credential without ever writing it to an asset.
    result = subprocess.run(
        ["gh", "auth", "token"], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def fetch_commits(repo: str, token: str, since: dt.datetime) -> list[Commit]:
    query = urllib.parse.urlencode(
        {
            "author": USER,
            "per_page": 100,
            "since": since.isoformat().replace("+00:00", "Z"),
        }
    )
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{USER}/{repo}/commits?{query}",
            "--paginate",
            "--slurp",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    pages = json.loads(result.stdout)
    payload = [item for page in pages for item in page]

    commits = []
    for item in payload:
        commit = item["commit"]
        raw_date = commit["author"]["date"]
        commits.append(
            Commit(
                repo=repo,
                sha=item["sha"][:7],
                subject=commit["message"].splitlines()[0].strip(),
                authored_at=dt.datetime.fromisoformat(raw_date.replace("Z", "+00:00")),
            )
        )
    return commits


def fetch_snapshot() -> Snapshot:
    token = github_token()
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=7)
    commits = [
        commit
        for repo in PROJECTS
        for commit in fetch_commits(repo, token, cutoff)
    ]
    commits.sort(key=lambda commit: commit.authored_at, reverse=True)
    if not commits:
        raise RuntimeError("No public portfolio commits returned by GitHub")

    latest = commits[0]
    previous_project = next(commit for commit in commits if commit.repo != latest.repo)
    recent = [commit for commit in commits if commit.authored_at >= cutoff]
    return Snapshot(
        latest=latest,
        previous_project=previous_project,
        recent_commits=tuple(recent),
        seven_day_commits=len(recent),
        seven_day_projects=len({commit.repo for commit in recent}),
        fetched_at=now,
    )


def short_subject(subject: str, limit: int = 29) -> str:
    subject = subject.removesuffix(".")
    if len(subject) <= limit:
        return subject
    return subject[: limit - 1].rstrip(" -:([") + "…"


def display_date(value: dt.datetime) -> str:
    return value.astimezone(PACIFIC).strftime("%b %-d · %-I:%M %p PT")


def xml(value: object) -> str:
    return html.escape(str(value), quote=True)


def font_faces() -> str:
    rules = []
    for family, filename, weight in (
        ("Manrope", "Manrope-500.woff2", 500),
        ("Manrope", "Manrope-700.woff2", 700),
        ("Space Grotesk", "SpaceGrotesk-500.woff2", 500),
        ("Space Grotesk", "SpaceGrotesk-700.woff2", 700),
    ):
        encoded = base64.b64encode((ASSETS / filename).read_bytes()).decode()
        rules.append(
            f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{encoded}) format('woff2')}}"
        )
    return "\n      ".join(rules)


def build(c: dict[str, str], theme: str, snapshot: Snapshot) -> str:
    latest = snapshot.latest
    previous = snapshot.previous_project
    fetched = display_date(snapshot.fetched_at).upper()
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 224" width="1200" height="224" role="img"
  aria-label="Live from the workbench. Latest public commit: {xml(latest.repo)}, {xml(latest.subject)}. {snapshot.seven_day_commits} public commits across {snapshot.seven_day_projects} portfolio projects in the last seven days.">
  <title>Live from Weiren's workbench</title>
  <desc>Automatically generated from an allowlist of public portfolio repositories.</desc>
  <defs>
    <linearGradient id="edge-{theme}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['teal']}"/>
      <stop offset=".48" stop-color="{c['purple']}"/>
      <stop offset="1" stop-color="{c['yellow']}"/>
    </linearGradient>
    <linearGradient id="signal-{theme}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['teal']}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{c['teal']}"/>
      <stop offset="1" stop-color="{c['teal']}" stop-opacity="0"/>
    </linearGradient>
    <filter id="glow-{theme}" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan-{theme}" width="6" height="6" patternUnits="userSpaceOnUse">
      <rect width="6" height="1" fill="{c['ink']}" opacity=".018"/>
    </pattern>
    <style>
      {font_faces()}
      .eyebrow{{font:700 13px 'Space Grotesk',sans-serif;letter-spacing:2.2px}}
      .label{{font:700 11px 'Space Grotesk',sans-serif;letter-spacing:1.8px}}
      .title{{font:700 18px 'Manrope',sans-serif}}
      .meta{{font:500 13px 'Manrope',sans-serif}}
      .number{{font:700 30px 'Space Grotesk',sans-serif}}
      .statlabel{{font:500 11px 'Space Grotesk',sans-serif;letter-spacing:1.25px}}
    </style>
  </defs>

  <rect width="1200" height="224" rx="18" fill="{c['bg']}"/>
  <rect width="1200" height="224" rx="18" fill="url(#scan-{theme})"/>
  <rect x="1" y="1" width="1198" height="222" rx="17" fill="none" stroke="{c['line']}" stroke-width="2"/>
  <rect x="26" y="0" width="1148" height="3" rx="1.5" fill="url(#edge-{theme})"/>

  <g transform="translate(48 34)">
    <circle cx="7" cy="7" r="5" fill="{c['teal']}" filter="url(#glow-{theme})">
      <animate attributeName="r" values="4.5;6;4.5" dur="2.2s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values=".72;1;.72" dur="2.2s" repeatCount="indefinite"/>
    </circle>
    <text x="24" y="12" class="eyebrow" fill="{c['teal']}">LIVE FROM THE WORKBENCH</text>
  </g>
  <text x="1152" y="46" text-anchor="end" class="label" fill="{c['faint']}">FETCHED {xml(fetched)}</text>

  <g transform="translate(48 70)">
    <rect width="342" height="112" rx="13" fill="{c['card']}" stroke="{c['line']}"/>
    <rect x="0" y="18" width="3" height="76" rx="1.5" fill="{c['teal']}"/>
    <text x="24" y="30" class="label" fill="{c['teal']}">LATEST COMMIT</text>
    <text x="24" y="62" class="title" fill="{c['ink']}">{xml(short_subject(latest.subject))}</text>
    <text x="24" y="89" class="meta" fill="{c['sub']}">{xml(latest.repo)} · {xml(latest.sha)} · {xml(display_date(latest.authored_at))}</text>
  </g>

  <g transform="translate(408 70)">
    <rect width="342" height="112" rx="13" fill="{c['card']}" stroke="{c['line']}"/>
    <rect x="0" y="18" width="3" height="76" rx="1.5" fill="{c['yellow']}"/>
    <text x="24" y="30" class="label" fill="{c['yellow']}">PREVIOUS PROJECT</text>
    <text x="24" y="62" class="title" fill="{c['ink']}">{xml(short_subject(previous.subject))}</text>
    <text x="24" y="89" class="meta" fill="{c['sub']}">{xml(previous.repo)} · {xml(previous.sha)} · {xml(display_date(previous.authored_at))}</text>
  </g>

  <g transform="translate(768 70)">
    <rect width="384" height="112" rx="13" fill="{c['card2']}" stroke="{c['line']}"/>
    <circle cx="28" cy="27" r="4" fill="{c['purple']}">
      <animate attributeName="opacity" values=".45;1;.45" dur="2.4s" repeatCount="indefinite"/>
    </circle>
    <text x="42" y="32" class="label" fill="{c['purple']}">PUBLIC PULSE · LAST 7 DAYS</text>
    <text x="24" y="72" class="number" fill="{c['ink']}">{snapshot.seven_day_commits}</text>
    <text x="24" y="92" class="statlabel" fill="{c['sub']}">COMMITS</text>
    <line x1="132" y1="48" x2="132" y2="93" stroke="{c['line']}"/>
    <text x="158" y="72" class="number" fill="{c['ink']}">{snapshot.seven_day_projects}</text>
    <text x="158" y="92" class="statlabel" fill="{c['sub']}">ACTIVE PROJECTS</text>
    <rect x="24" y="104" width="330" height="1" fill="{c['line']}"/>
    <rect x="24" y="104" width="92" height="1" fill="url(#signal-{theme})">
      <animate attributeName="x" values="-68;330" dur="3.2s" repeatCount="indefinite"/>
    </rect>
  </g>

  <g transform="translate(48 202)">
    <circle cx="0" cy="0" r="3" fill="{c['teal']}"/>
    <rect x="12" y="-1" width="1092" height="2" rx="1" fill="{c['line']}"/>
    <rect x="12" y="-1" width="170" height="2" rx="1" fill="url(#edge-{theme})">
      <animate attributeName="x" values="12;934;12" dur="8s" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .2 1;.4 0 .2 1"/>
    </rect>
    <circle cx="1104" cy="0" r="3" fill="{c['yellow']}"/>
  </g>
</svg>'''


def main() -> None:
    snapshot = fetch_snapshot()
    for theme, colors in THEMES.items():
        (ASSETS / f"workbench-{theme}.svg").write_text(
            build(colors, theme, snapshot), encoding="utf-8"
        )
    print(
        f"Fetched {snapshot.seven_day_commits} commits across "
        f"{snapshot.seven_day_projects} projects; latest is "
        f"{snapshot.latest.repo}@{snapshot.latest.sha}."
    )


if __name__ == "__main__":
    main()

