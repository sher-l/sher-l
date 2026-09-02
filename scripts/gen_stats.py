#!/usr/bin/env python3
"""从 GitHub GraphQL API 拉取数据，自渲染 profile 用的 stats.svg 与 graph.svg。

不依赖 github-readme-stats.vercel.app 等第三方共享实例（经常 503/限流导致 README 图裂开）。
配色与 bio-dev / 博客主题一致：纸色底 + 墨绿 + 金。
"""
import json
import os
import sys
import urllib.request

LOGIN = "sher-l"
TOKEN = os.environ.get("GH_TOKEN")
if not TOKEN:
    sys.exit("GH_TOKEN is required")

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount }
    }
    followers { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

PAPER = "#FDFBF7"
INK = "#12362C"
TEXT = "#1C2420"
MUTED = "#5A6B62"
BORDER = "#E5E1D6"
GOLD = "#C8963E"
LEVELS = ["#EDEBE2", "#DCEFE6", "#6FC7A4", "#3C9373", "#12362C"]


def level_color(count):
    if count <= 0:
        return LEVELS[0]
    if count <= 3:
        return LEVELS[1]
    if count <= 7:
        return LEVELS[2]
    if count <= 12:
        return LEVELS[3]
    return LEVELS[4]


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        sys.exit(f"GraphQL errors: {data['errors']}")
    return data["data"]["user"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_stats(user):
    repos = user["repositories"]["totalCount"]
    stars = sum(n["stargazerCount"] for n in user["repositories"]["nodes"])
    followers = user["followers"]["totalCount"]
    contribs = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    def cell(x, y, value, label, color):
        return (
            f'<text x="{x}" y="{y}" font-family="Courier New, monospace" font-size="24" '
            f'font-weight="bold" fill="{color}">{esc(value)}</text>'
            f'<text x="{x}" y="{y + 22}" font-family="Helvetica, Arial, sans-serif" '
            f'font-size="11" fill="{MUTED}">{esc(label)}</text>'
        )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="195" viewBox="0 0 500 195">',
        f'<rect x="0.5" y="0.5" width="499" height="194" rx="18" fill="{PAPER}" stroke="{BORDER}"/>',
        f'<text x="26" y="42" font-family="Georgia, serif" font-size="21" font-weight="bold" fill="{INK}">{LOGIN}</text>',
        f'<text x="{26 + len(LOGIN) * 12 + 14}" y="42" font-family="Helvetica, Arial, sans-serif" font-size="13" fill="{MUTED}">GitHub Stats</text>',
        f'<line x1="26" y1="58" x2="474" y2="58" stroke="{BORDER}"/>',
        cell(26, 96, str(stars), "Total Stars", GOLD),
        cell(262, 96, str(repos), "Total Repos", TEXT),
        cell(26, 152, str(followers), "Followers", TEXT),
        cell(262, 152, f"{contribs}", "Contributions (1y)", TEXT),
        "</svg>",
    ]
    return "\n".join(parts)


def render_graph(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    cell, gap = 11, 3
    x0, y0 = 26, 48
    w = x0 * 2 + len(weeks) * (cell + gap)
    h = 118
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{PAPER}" stroke="{BORDER}"/>',
        f'<text x="{x0}" y="30" font-family="Georgia, serif" font-size="16" font-weight="bold" fill="{INK}">Contributions in the last year</text>',
        f'<text x="{w - x0}" y="30" text-anchor="end" font-family="Courier New, monospace" font-size="14" font-weight="bold" fill="{GOLD}">{total}</text>',
    ]
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            parts.append(
                f'<rect x="{x0 + wi * (cell + gap)}" y="{y0 + di * (cell + gap)}" '
                f'width="{cell}" height="{cell}" rx="2.5" fill="{level_color(day["contributionCount"])}">'
                f"<title>{day['date']}: {day['contributionCount']}</title></rect>"
            )
    lx = w - x0 - 5 * (cell + gap) - 84
    parts.append(f'<text x="{lx}" y="{h - 12}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{MUTED}">Less</text>')
    for i in range(5):
        parts.append(
            f'<rect x="{lx + 34 + i * (cell + gap)}" y="{h - 21}" width="{cell}" height="{cell}" rx="2" fill="{LEVELS[i]}"/>'
        )
    parts.append(
        f'<text x="{lx + 34 + 5 * (cell + gap) + 6}" y="{h - 12}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{MUTED}">More</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    user = fetch()
    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(render_stats(user))
    with open("graph.svg", "w", encoding="utf-8") as f:
        f.write(render_graph(user))
    print("stats.svg / graph.svg generated")


if __name__ == "__main__":
    main()
