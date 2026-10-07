#!/usr/bin/env python3

import html
import json
import os
import urllib.request
from pathlib import Path

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "kudokudo1")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
PROFILE_REPO = f"{OWNER}/{OWNER}"
OUT = Path("assets/public-language-stats.svg")


def github_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "post-apollo-profile-language-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def fetch_public_nonfork_repos():
    repos = []
    page = 1

    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&per_page=100&page={page}&sort=full_name"
        )
        batch = github_json(url)
        if not batch:
            break

        for repo in batch:
            if repo.get("private"):
                continue
            if repo.get("fork"):
                continue
            if repo.get("full_name") == PROFILE_REPO:
                continue
            repos.append(repo)

        if len(batch) < 100:
            break
        page += 1

    return repos


def aggregate_languages(repos):
    totals = {}

    for repo in repos:
        langs = github_json(repo["languages_url"])
        for language, byte_count in langs.items():
            totals[language] = totals.get(language, 0) + int(byte_count)

    return totals


def build_rows(totals):
    total_bytes = sum(totals.values())
    if total_bytes == 0:
        return [("No detected languages", 0.0)], 0

    ordered = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    top = ordered[:4]
    remainder = sum(value for _, value in ordered[4:])

    rows = [(name, value / total_bytes * 100.0) for name, value in top]
    if remainder:
        rows.append(("Other", remainder / total_bytes * 100.0))

    return rows, len(ordered)


def render_svg(rows, language_count, repo_count):
    width = 520
    height = 235
    bar_x = 22
    bar_width = 476
    row_start = 73
    row_gap = 31
    bar_height = 7

    palette = ["#55CFCA", "#F2BE4E", "#C74EC7", "#5B5FD4", "#D16041"]

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="235" viewBox="0 0 520 235">',
        '  <rect width="520" height="235" rx="8" fill="#1B0623"/>',
        '  <rect x="0.5" y="0.5" width="519" height="234" rx="8" fill="none" stroke="#55CFCA" stroke-opacity="0.85"/>',
        "",
        "  <style>",
        '    .title { font: 600 18px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #55CFCA; }',
        '    .label { font: 600 12px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #DCF3FA; }',
        '    .value { font: 700 12px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #DCF3FA; }',
        '    .small { font: 600 9px ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; fill: #C74EC7; letter-spacing: 1px; }',
        "  </style>",
        "",
        '  <text x="22" y="31" class="title">PUBLIC REPO LANGUAGES</text>',
        '  <text x="22" y="50" class="small">AUTO // PUBLIC NON-FORKED SNAPSHOT</text>',
        "",
    ]

    for index, (name, percentage) in enumerate(rows):
        y = row_start + index * row_gap
        bar_y = y + 8
        fill_width = max(0.0, min(bar_width, bar_width * percentage / 100.0))
        color = palette[index % len(palette)]
        safe_name = html.escape(name)

        parts.extend([
            f'  <text x="22" y="{y}" class="label">{safe_name}</text>',
            f'  <text x="498" y="{y}" text-anchor="end" class="value">{percentage:.2f}%</text>',
            f'  <rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" rx="3.5" fill="#3E174A"/>',
            f'  <rect x="{bar_x}" y="{bar_y}" width="{fill_width:.2f}" height="{bar_height}" rx="3.5" fill="{color}"/>',
            "",
        ])

    footer = f"{repo_count} REPOS // {language_count} LANGUAGES"
    parts.append(f'  <text x="498" y="224" text-anchor="end" class="small">{footer}</text>')
    parts.append("</svg>")
    parts.append("")

    return "\n".join(parts)


def main():
    repos = fetch_public_nonfork_repos()
    totals = aggregate_languages(repos)
    rows, language_count = build_rows(totals)
    svg = render_svg(rows, language_count, len(repos))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")

    print(f"Updated {OUT}")
    print(f"Counted {len(repos)} public non-forked repositories")
    for name, percentage in rows:
        print(f"{name}: {percentage:.2f}%")


if __name__ == "__main__":
    main()
