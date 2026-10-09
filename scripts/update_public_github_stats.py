#!/usr/bin/env python3

import html
import json
import os
import urllib.request
from pathlib import Path

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "kudokudo1")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
PROFILE_REPO = f"{OWNER}/{OWNER}"
OUT = Path("assets/public-github-stats.svg")


def github_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "post-apollo-profile-stats-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def fetch_owned_public_repos():
    repos = []
    page = 1

    while True:
        batch = github_json(
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&per_page=100&page={page}&sort=full_name"
        )
        if not batch:
            break

        repos.extend(repo for repo in batch if not repo.get("private"))

        if len(batch) < 100:
            break
        page += 1

    return repos


def render_svg(public_repos):
    family = [
        repo for repo in public_repos
        if repo.get("full_name") != PROFILE_REPO
    ]
    originals = [repo for repo in family if not repo.get("fork")]
    forks = [repo for repo in family if repo.get("fork")]
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in public_repos)

    rows = [
        ("◈  PUBLIC REPOSITORIES", len(public_repos)),
        ("★  FAMILY PROJECTS", len(family)),
        ("◆  ORIGINAL PROJECTS", len(originals)),
        ("⑂  INHERITED FORKS", len(forks)),
        ("✦  STARS EARNED", stars),
    ]

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="235" viewBox="0 0 520 235">',
        '  <rect width="520" height="235" rx="8" fill="#1B0623"/>',
        '  <rect x="0.5" y="0.5" width="519" height="234" rx="8" fill="none" stroke="#55CFCA" stroke-opacity="0.85"/>',
        "",
        "  <style>",
        '    .title { font: 600 18px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #55CFCA; }',
        '    .label { font: 600 13px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #DCF3FA; }',
        '    .value { font: 700 14px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #F2BE4E; }',
        '    .small { font: 600 9px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #C74EC7; letter-spacing: 1px; }',
        '    .big { font: 700 32px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #DCF3FA; }',
        "  </style>",
        "",
        '  <text x="22" y="31" class="title">KUDO // PUBLIC GITHUB</text>',
        '  <text x="22" y="50" class="small">AUTO // CURRENT ACCOUNT SNAPSHOT</text>',
        "",
        '  <g transform="translate(22,0)">',
    ]

    y = 82
    for label, value in rows:
        parts.append(f'    <text x="0" y="{y}" class="label">{html.escape(str(label))}</text>')
        parts.append(f'    <text x="300" y="{y}" text-anchor="end" class="value">{value}</text>')
        parts.append("")
        y += 26

    parts.extend([
        "  </g>",
        "",
        '  <circle cx="435" cy="118" r="45" fill="none" stroke="#3E174A" stroke-width="8"/>',
        '  <circle cx="435" cy="118" r="45" fill="none" stroke="#C74EC7" stroke-width="8"',
        '          stroke-linecap="round" stroke-dasharray="210 73" transform="rotate(-90 435 118)"/>',
        f'  <text x="435" y="128" text-anchor="middle" class="big">{len(public_repos)}</text>',
        '  <text x="435" y="204" text-anchor="middle" class="small">PUBLIC REPOS</text>',
        "</svg>",
        "",
    ])

    return "\n".join(parts)


def main():
    repos = fetch_owned_public_repos()
    svg = render_svg(repos)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")

    family = [repo for repo in repos if repo.get("full_name") != PROFILE_REPO]
    originals = [repo for repo in family if not repo.get("fork")]
    forks = [repo for repo in family if repo.get("fork")]
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in repos)

    print(f"Updated {OUT}")
    print(f"PUBLIC REPOSITORIES // {len(repos)}")
    print(f"FAMILY PROJECTS // {len(family)}")
    print(f"ORIGINAL PROJECTS // {len(originals)}")
    print(f"INHERITED FORKS // {len(forks)}")
    print(f"STARS EARNED // {stars}")


if __name__ == "__main__":
    main()
