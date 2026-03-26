#!/usr/bin/env python3
from __future__ import annotations

import collections
import datetime as dt
import json
import os
import urllib.request
from typing import Dict, List

USERNAME = os.getenv("GITHUB_USERNAME", "TonyBlur")
README_PATH = "README.md"
START = "<!-- AUTO-REPO-STATS:START -->"
END = "<!-- AUTO-REPO-STATS:END -->"
MAX_REPOS_TO_SHOW = 8


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
        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?per_page=100&page={page}&sort=updated"
        )
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


def build_auto_section(username: str, repos: List[Dict]) -> str:
    total = len(repos)
    forks = sum(1 for r in repos if r.get("fork"))
    source = total - forks

    lang_counter = collections.Counter(r.get("language") for r in repos if r.get("language"))
    top_lang = ", ".join(f"{lang} ({cnt})" for lang, cnt in lang_counter.most_common(6)) or "N/A"

    repos_sorted = sorted(repos, key=lambda r: r.get("pushed_at", ""), reverse=True)

    lines: List[str] = []
    lines.append("## Auto-updated Repository Stats (All Repos)")
    lines.append("")
    lines.append(f"- Total public repositories: **{total}**")
    lines.append(f"- Source repositories: **{source}**")
    lines.append(f"- Fork repositories: **{forks}**")
    lines.append(f"- Top languages by repository count: **{top_lang}**")
    lines.append("")
    lines.append(f"_Last updated (UTC): {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append("")

    lines.append("### Repository Maintenance Board")
    lines.append("")
    lines.append("| Repo | Type | Stars | Last Push | Main Language | Activity |")
    lines.append("|---|---:|---:|---:|---|---|")
    for r in repos_sorted[:MAX_REPOS_TO_SHOW]:
        name = r["name"]
        repo_url = r["html_url"]
        kind = "Fork" if r.get("fork") else "Source"
        stars = r.get("stargazers_count", 0)
        pushed = iso_to_date(r.get("pushed_at", "")) if r.get("pushed_at") else "N/A"
        lang = r.get("language") or "N/A"
        activity_badge = (
            f"![activity](https://img.shields.io/github/commit-activity/y/{username}/{name}?style=flat-square) "
            f"![last](https://img.shields.io/github/last-commit/{username}/{name}?style=flat-square)"
        )
        lines.append(f"| [{name}]({repo_url}) | {kind} | {stars} | {pushed} | {lang} | {activity_badge} |")

    lines.append("")

    lines.append("")
    lines.append(f"_Showing the latest **{min(total, MAX_REPOS_TO_SHOW)}** repositories by push time (out of {total} total)._")

    lines.append("### Live Dynamic Visuals")
    lines.append("")
    lines.append('<div align="center">')
    lines.append(
        f'  <img src="https://github-profile-summary-cards.vercel.app/api/cards/profile-details?username={username}&theme=github_dark" width="100%" />'
    )
    lines.append("</div>")
    lines.append("")
    lines.append('<div align="center">')
    lines.append(
        f'  <img src="https://github-readme-activity-graph.vercel.app/graph?username={username}&theme=github-compact&hide_border=true" width="100%" />'
    )
    lines.append("</div>")
    lines.append("")
    lines.append('<div align="center">')
    lines.append(
        f'  <img height="170" src="https://github-readme-stats.vercel.app/api?username={username}&show_icons=true&theme=github_dark&hide_border=true&include_all_commits=true" />'
    )
    lines.append(
        f'  <img height="170" src="https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact&theme=github_dark&hide_border=true" />'
    )
    lines.append("</div>")

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
