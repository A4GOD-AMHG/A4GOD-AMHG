#!/usr/bin/env python3
"""Writes stats.svg: aggregate GitHub numbers, private work included.

Only totals leave the token's scope (contributions, repositories, pull
requests, language mix): no repository name, link or content. Needs
GH_TOKEN with `repo` + `read:user` (a classic PAT of the profile owner).
"""
import datetime as dt
import html
import json
import os
import urllib.request

API = "https://api.github.com/graphql"
TOKEN = os.environ["GH_TOKEN"]


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


AFFIL = "[OWNER, COLLABORATOR, ORGANIZATION_MEMBER]"
me = gql(f"""{{ viewer {{ login createdAt
  all: repositories(ownerAffiliations: {AFFIL}) {{ totalCount }}
  private: repositories(privacy: PRIVATE, ownerAffiliations: {AFFIL}) {{ totalCount }}
  pullRequests {{ totalCount }} }} }}""")["viewer"]

# Contributions per year (the API caps a range at one year).
now = dt.datetime.now(dt.timezone.utc)
year = dt.datetime.fromisoformat(me["createdAt"].replace("Z", "+00:00")).year
total = this_year = 0
while year <= now.year:
    start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
    end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
    c = gql("""query($from: DateTime!, $to: DateTime!) { viewer {
      contributionsCollection(from: $from, to: $to) { contributionCalendar { totalContributions } } } }""",
            **{"from": start.isoformat(), "to": end.isoformat()})
    n = c["viewer"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    total += n
    if year == now.year:
        this_year = n
    year += 1

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
years = now.year - int(me["createdAt"][:4])

numbers = [
    (f"{total:,}", "contributions"),
    (f"{this_year:,}", f"in {now.year}"),
    (f"{me['all']['totalCount']}", f"repositories · {me['private']['totalCount']} private"),
    (f"{me['pullRequests']['totalCount']:,}", "pull requests"),
]

W, H = 840, 230
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats">',
       '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
       '<stop offset="0" stop-color="#130f24"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>',
       f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#g)" stroke="#3b2a63"/>',
       '<style>text{font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}'
       '.n{font-size:30px;font-weight:700;fill:#f5f3ff}.l{font-size:13px;fill:#a78bfa}'
       '.t{font-size:12px;fill:#c4b5fd;letter-spacing:2px}.s{font-size:12px;fill:#9ca3af}</style>',
       '<text x="28" y="36" class="t">GITHUB · PUBLIC + PRIVATE WORK</text>']
col = (W - 56) / 4
for i, (n, label) in enumerate(numbers):
    x = 28 + i * col
    out.append(f'<text x="{x:.0f}" y="84" class="n">{html.escape(n)}</text>')
    out.append(f'<text x="{x:.0f}" y="106" class="l">{html.escape(label)}</text>')

# Language bar and legend.
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
out.append(f'<text x="28" y="208" class="s">On GitHub for {years} years · updated {now:%Y-%m-%d}</text>')
out.append("</svg>")

with open(os.path.join(os.path.dirname(__file__), "..", "stats.svg"), "w") as f:
    f.write("\n".join(out) + "\n")
print(f"stats.svg: {total} contributions, {me['all']['totalCount']} repos, {len(langs)} languages")
