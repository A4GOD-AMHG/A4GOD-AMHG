#!/usr/bin/env python3
"""Writes the profile cards, Spanish and English:

  stats.svg / stats.en.svg        contributions, repositories, pull requests,
                                  language mix (public + private work)
  calendar.svg / calendar.en.svg  last year's contribution graph

Only totals leave the token's scope: no repository name, link or content.
Needs GH_TOKEN with `repo` + `read:user` (a classic PAT of the profile owner).
"""
import datetime as dt
import html
import json
import os
import urllib.request

API = "https://api.github.com/graphql"
TOKEN = os.environ["GH_TOKEN"]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
AFFIL = "[OWNER, COLLABORATOR, ORGANIZATION_MEMBER]"
FONT = 'text{font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}'

LABELS = {
    "es": {
        "head": "GITHUB · TRABAJO PÚBLICO + PRIVADO", "contrib": "contribuciones", "in": "en {y}",
        "repos": "repositorios · {p} privados", "prs": "pull requests",
        "foot": "En GitHub desde {y} · actualizado {d}",
        "cal": "{n} contribuciones en el último año",
        "months": "Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic".split(), "less": "Menos", "more": "Más",
    },
    "en": {
        "head": "GITHUB · PUBLIC + PRIVATE WORK", "contrib": "contributions", "in": "in {y}",
        "repos": "repositories · {p} private", "prs": "pull requests",
        "foot": "On GitHub since {y} · updated {d}",
        "cal": "{n} contributions in the last year",
        "months": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), "less": "Less", "more": "More",
    },
}


def gql(query, **variables):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise SystemExit(f"GitHub API: {body['errors']}")
    return body["data"]


def write(name, parts):
    with open(os.path.join(ROOT, name), "w") as f:
        f.write("\n".join(parts) + "\n")


me = gql(f"""{{ viewer {{ createdAt
  all: repositories(ownerAffiliations: {AFFIL}) {{ totalCount }}
  private: repositories(privacy: PRIVATE, ownerAffiliations: {AFFIL}) {{ totalCount }}
  pullRequests {{ totalCount }}
  contributionsCollection {{ contributionCalendar {{ totalContributions
    weeks {{ contributionDays {{ date contributionCount }} }} }} }} }} }}""")["viewer"]

# All-time contributions, one year per query (the API's limit).
now = dt.datetime.now(dt.timezone.utc)
since = int(me["createdAt"][:4])
total = this_year = 0
for year in range(since, now.year + 1):
    start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
    end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
    c = gql("""query($from: DateTime!, $to: DateTime!) { viewer {
      contributionsCollection(from: $from, to: $to) { contributionCalendar { totalContributions } } } }""",
            **{"from": start.isoformat(), "to": end.isoformat()})
    n = c["viewer"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    total += n
    this_year = n if year == now.year else this_year

# Language mix by code size over every non-fork repository.
langs, cursor = {}, None
while True:
    page = gql(f"""query($after: String) {{ viewer {{
      repositories(first: 100, after: $after, isFork: false, ownerAffiliations: {AFFIL}) {{
        pageInfo {{ hasNextPage endCursor }}
        nodes {{ languages(first: 10, orderBy: {{field: SIZE, direction: DESC}}) {{
          edges {{ size node {{ name color }} }} }} }} }} }} }}""", after=cursor)["viewer"]["repositories"]
    for repo in page["nodes"]:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            prev = langs.get(name, (0, e["node"]["color"] or "#8b5cf6"))
            langs[name] = (prev[0] + e["size"], prev[1])
    if not page["pageInfo"]["hasNextPage"]:
        break
    cursor = page["pageInfo"]["endCursor"]
top = sorted(langs.items(), key=lambda kv: kv[1][0], reverse=True)[:6]
size_sum = sum(v[0] for _, v in top) or 1

calendar = me["contributionsCollection"]["contributionCalendar"]
counts = sorted(d["contributionCount"] for w in calendar["weeks"] for d in w["contributionDays"] if d["contributionCount"])
# Five shades: none, then the quartiles of the active days.
cuts = [counts[int(len(counts) * q)] for q in (0.25, 0.5, 0.75)] if counts else [1, 2, 3]
SHADES = ["#1c1830", "#4c1d95", "#6d28d9", "#8b5cf6", "#c4b5fd"]


def shade(n):
    if n == 0:
        return SHADES[0]
    return SHADES[1 + sum(n > c for c in cuts)]


for lang, L in LABELS.items():
    suffix = "" if lang == "es" else ".en"
    fmt = (lambda n: f"{n:,}".replace(",", ".")) if lang == "es" else (lambda n: f"{n:,}")

    # Stats card.
    W, H = 840, 230
    numbers = [
        (fmt(total), L["contrib"]),
        (fmt(this_year), L["in"].format(y=now.year)),
        (str(me["all"]["totalCount"]), L["repos"].format(p=me["private"]["totalCount"])),
        (fmt(me["pullRequests"]["totalCount"]), L["prs"]),
    ]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats">',
           '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0" stop-color="#1a1235"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>',
           f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#g)" stroke="#3b2a63"/>',
           f'<style>{FONT}.n{{font-size:30px;font-weight:700;fill:#ffffff}}.l{{font-size:13px;fill:#ddd6fe}}'
           '.t{font-size:12px;fill:#ddd6fe;letter-spacing:2px}.s{font-size:12px;fill:#e5e7eb}</style>',
           f'<text x="28" y="36" class="t">{html.escape(L["head"])}</text>']
    col = (W - 56) / 4
    for i, (n, label) in enumerate(numbers):
        x = 28 + i * col
        out.append(f'<text x="{x:.0f}" y="84" class="n">{html.escape(n)}</text>')
        out.append(f'<text x="{x:.0f}" y="106" class="l">{html.escape(label)}</text>')
    x, bar_w = 28.0, W - 56
    out.append(f'<clipPath id="c"><rect x="28" y="134" width="{bar_w}" height="10" rx="5"/></clipPath><g clip-path="url(#c)">')
    for name, (size, color) in top:
        w = bar_w * size / size_sum
        out.append(f'<rect x="{x:.1f}" y="134" width="{w + 0.5:.1f}" height="10" fill="{color}"/>')
        x += w
    out.append("</g>")
    lx = 28.0
    for name, (size, color) in top:
        label = f"{name} {100 * size / size_sum:.0f}%"
        out.append(f'<circle cx="{lx + 5:.0f}" cy="170" r="5" fill="{color}"/>')
        out.append(f'<text x="{lx + 15:.0f}" y="174" class="s">{html.escape(label)}</text>')
        lx += 26 + 7.4 * len(label)
    out.append(f'<text x="28" y="208" class="s">{html.escape(L["foot"].format(y=since, d=f"{now:%Y-%m-%d}"))}</text>')
    out.append("</svg>")
    write(f"stats{suffix}.svg", out)

    # Contribution graph: one column per week, Sunday on top (like GitHub).
    weeks = calendar["weeks"]
    cell, gap, left, top_y = 11, 3, 28, 64
    W2 = left * 2 + len(weeks) * (cell + gap) - gap
    H2 = top_y + 7 * (cell + gap) + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}" role="img" aria-label="Contribution graph">',
           f'<rect x="0.5" y="0.5" width="{W2 - 1}" height="{H2 - 1}" rx="14" fill="#0d1117" stroke="#3b2a63"/>',
           f'<style>{FONT}.h{{font-size:15px;font-weight:600;fill:#ffffff}}.m{{font-size:11px;fill:#ddd6fe}}</style>',
           f'<text x="{left}" y="32" class="h">{html.escape(L["cal"].format(n=fmt(calendar["totalContributions"])))}</text>']
    last_month, last_x = None, -1000
    for i, w in enumerate(weeks):
        x = left + i * (cell + gap)
        first = w["contributionDays"][0]["date"]
        month = int(first[5:7])
        if month != last_month:
            # A month needs 3 columns of room for its label.
            if i <= len(weeks) - 3 and x - last_x >= 3 * (cell + gap):
                out.append(f'<text x="{x}" y="{top_y - 8}" class="m">{L["months"][month - 1]}</text>')
                last_x = x
            last_month = month
        for d in w["contributionDays"]:
            wd = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7
            out.append(f'<rect x="{x}" y="{top_y + wd * (cell + gap)}" width="{cell}" height="{cell}" rx="2" fill="{shade(d["contributionCount"])}"/>')
    ly = top_y + 7 * (cell + gap) + 14
    lx = W2 - left - 5 * (cell + gap) - 40
    out.append(f'<text x="{lx - 8}" y="{ly + 9}" class="m" text-anchor="end">{L["less"]}</text>')
    for j, c in enumerate(SHADES):
        out.append(f'<rect x="{lx + j * (cell + gap)}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{c}"/>')
    out.append(f'<text x="{lx + 5 * (cell + gap) + 4}" y="{ly + 9}" class="m">{L["more"]}</text>')
    out.append("</svg>")
    write(f"calendar{suffix}.svg", out)

print(f"cards: {total} contributions, {me['all']['totalCount']} repos, {len(langs)} languages")
