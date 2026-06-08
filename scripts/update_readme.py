#!/usr/bin/env python3
"""Auto-generate Lobe-style GitHub stats section for profile README."""
from __future__ import annotations

import collections
import json
import os
import urllib.request
from typing import Dict, List

USERNAME = os.getenv("GITHUB_USERNAME", "TonyBlur")
README_PATH = "README.md"
START = "<!-- AUTO-REPO-STATS:START -->"
END = "<!-- AUTO-REPO-STATS:END -->"
MAX_REPOS_TO_SHOW = 8

RAINBOW = "![](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)"


def fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-profile-readme-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_repos(username: str) -> List[Dict]:
    repos: List[Dict] = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}&sort=updated"
        chunk = fetch_json(url)
        if not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return repos


def iso_to_date(iso: str) -> str:
    return iso[:10]


def _badge(label: str, value: str, color: str, logo: str = "") -> str:
    """Generate a shields.io flat-square badge markdown."""
    logo_part = f"&logo={logo}&logoColor=white" if logo else ""
    return (
        f"![{label}](https://img.shields.io/badge/{label}-{value}-{color}"
        f"?style=flat-square&labelColor=black{logo_part})"
    )


def build_auto_section(username: str, repos: List[Dict]) -> str:
    total = len(repos)
    forks = sum(1 for r in repos if r.get("fork"))
    source = total - forks

    lang_counter = collections.Counter(r.get("language") for r in repos if r.get("language"))
    top_lang = ", ".join(f"**{lang}** ({cnt})" for lang, cnt in lang_counter.most_common(6)) or "N/A"
    repos_sorted = sorted(
        repos,
        key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at", "")),
        reverse=True,
    )

    lines: List[str] = []

    # ── GitHub Stats Section ──
    lines.append('## 📊 GitHub Stats')
    lines.append("")
    lines.append('<div align="center">')
    lines.append("")
    # Profile details card
    lines.append(
        f'  <img src="https://github-profile-summary-cards.vercel.app/api/cards/profile-details'
        f'?username={username}&theme=github_dark" width="100%" />'
    )
    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append(RAINBOW)
    lines.append("")

    # Stats + Top Languages side by side
    lines.append('<div align="center">')
    lines.append(
        f'  <img height="170" src="https://github-profile-summary-cards.vercel.app/api/cards/stats'
        f'?username={username}&theme=github_dark" />'
    )
    lines.append(
        f'  <img height="170" src="https://github-readme-stats.vercel.app/api/top-langs/'
        f'?username={username}&layout=compact&theme=github_dark&hide_border=true" />'
    )
    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append(RAINBOW)
    lines.append("")

    # Activity graph
    lines.append('<div align="center">')
    lines.append(
        f'  <img src="https://github-readme-activity-graph.vercel.app/graph'
        f'?username={username}&theme=github-compact&hide_border=true" width="100%" />'
    )
    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append(RAINBOW)
    lines.append("")

    # ── Repository Overview Section ──
    lines.append("## 📦 Repository Overview")
    lines.append("")
    lines.append('<div align="center">')
    lines.append("")
    lines.append(f'{_badge("🌐 Repos", str(total), "8ae8ff")}')
    lines.append(f'{_badge("🧩 Source", str(source), "c4f042")}')
    lines.append(f'{_badge("🍴 Forks", str(forks), "ff80eb")}')
    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append(f"- 🛠️ Top languages: {top_lang}")
    lines.append("")

    # Repo table
    lines.append("| Repo | Type | ⭐ | Last Push | Language | Activity |")
    lines.append("|:---|:---:|---:|:---:|:---:|:---|")

    for r in repos_sorted[:MAX_REPOS_TO_SHOW]:
        name = r["name"]
        repo_url = r["html_url"]
        kind = "Fork" if r.get("fork") else "Source"
        stars = r.get("stargazers_count", 0)
        pushed = iso_to_date(r.get("pushed_at", "")) if r.get("pushed_at") else "N/A"
        lang = r.get("language") or "N/A"
        activity_badge = (
            f"![activity](https://img.shields.io/github/commit-activity/y/{username}/{name}"
            f"?style=flat-square) "
            f"![last](https://img.shields.io/github/last-commit/{username}/{name}"
            f"?style=flat-square)"
        )
        lines.append(f"| [{name}]({repo_url}) | {kind} | {stars} | {pushed} | {lang} | {activity_badge} |")

    lines.append("")

    return "\n".join(lines)


def update_readme(section: str) -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if START not in content or END not in content:
        raise RuntimeError(f"README markers not found: {START} / {END}")

    before = content.split(START)[0]
    after = content.split(END)[1]
    new_content = before + START + "\n\n" + section + "\n\n" + END + after

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main() -> None:
    repos = fetch_all_repos(USERNAME)
    section = build_auto_section(USERNAME, repos)
    update_readme(section)


if __name__ == "__main__":
    main()
