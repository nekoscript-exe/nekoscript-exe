import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone

USER = "nekoscript-exe"

def api(endpoint):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "nekoscript-metrics"
    }

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        f"https://api.github.com/{endpoint}",
        headers=headers
    )

    with urlopen(request, timeout=30) as response:
        return json.load(response)

profile = api(f"users/{USER}")

repos = []
page = 1

while True:
    batch = api(f"users/{USER}/repos?per_page=100&page={page}")
    repos.extend(batch)

    if len(batch) < 100:
        break

    page += 1

repos = [r for r in repos if not r["private"]]

metrics = [
    ("Public repositories", len(repos)),
    ("Stars earned", sum(r["stargazers_count"] for r in repos)),
    ("Followers", profile["followers"]),
    ("Repository forks", sum(r["forks_count"] for r in repos)),
]

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 310">
<title>Nekoscript developer metrics</title>
<rect width="960" height="310" rx="16" fill="#141624"/>

<g font-family="monospace">
<text x="30" y="40" fill="#a78bfa" font-size="22"
font-weight="bold">NEKOSCRIPT // METRICS</text>

<text x="930" y="40" text-anchor="end"
fill="#69edc5" font-size="12">SYSTEM ONLINE</text>
'''

for i, (label, value) in enumerate(metrics):
    x = 30 + (i % 2) * 460
    y = 65 + (i // 2) * 100

    svg += f'''
    <rect x="{x}" y="{y}" width="440" height="85"
    rx="10" fill="#1a1e30" stroke="#293449"/>

    <text x="{x+20}" y="{y+37}" fill="#69edc5"
    font-size="28" font-weight="bold">{value}</text>

    <text x="{x+20}" y="{y+63}" fill="#e6edf3"
    font-size="14">{label}</text>
    '''

updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

svg += f'''
<text x="30" y="286" fill="#94a3b8" font-size="12">
SOURCE: GITHUB API
</text>
<text x="930" y="286" text-anchor="end"
fill="#94a3b8" font-size="12">UPDATED: {updated}</text>
</g>
</svg>
'''

output = Path("assets/branding/metrics.svg")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n", encoding="utf-8")

for label, value in metrics:
    print(f"{label}: {value}")

print("Metrics generated:", output)

# Public repository language distribution

from collections import Counter
from xml.sax.saxutils import escape

languages = Counter()

for repo in repos:
    if repo["fork"] or repo["name"] == USER:
        continue

    data = api(f"repos/{USER}/{repo['name']}/languages")
    languages.update(data)

total = sum(languages.values())

palette = [
    "#69edc5", "#a78bfa", "#e0af68",
    "#60a5fa", "#f0abfc", "#94a3b8",
    "#f7768e", "#7dcfff"
]

items = languages.most_common(7)
remaining = total - sum(value for _, value in items)

if remaining:
    items.append(("Others", remaining))

svg = '''<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 960 320">
<title>Nekoscript language distribution</title>

<rect width="960" height="320" rx="16" fill="#141624"/>

<g font-family="monospace">
<text x="30" y="40" font-size="22"
font-weight="bold" fill="#a78bfa">NEKOSCRIPT // LANGUAGES</text>

<text x="30" y="68" font-size="12"
fill="#94a3b8">PUBLIC REPOSITORIES // SOURCE CODE</text>
'''

x = 30

for i, (language, value) in enumerate(items):
    percentage = value / total * 100
    width = value / total * 900
    color = palette[i]

    svg += f'''
<rect x="{x:.3f}" y="85" width="{width:.3f}"
height="18" fill="{color}"/>
'''
    x += width

    lx = 30 + (i % 2) * 460
    ly = 140 + (i // 2) * 35

    svg += f'''
<circle cx="{lx+7}" cy="{ly-5}" r="6" fill="{color}"/>
<text x="{lx+25}" y="{ly}" font-size="16"
fill="#e6edf3">{escape(language)}</text>
<text x="{lx+420}" y="{ly}" text-anchor="end"
font-size="16" fill="#94a3b8">{percentage:.1f}%</text>
'''

    print(f"{language}: {percentage:.2f}%")

if not total:
    svg += '''
<text x="480" y="160" text-anchor="middle"
fill="#94a3b8">No language data available</text>
'''

svg += '''
<path d="M30 275 H930" stroke="#293449"/>
<text x="480" y="300" text-anchor="middle"
font-size="12" fill="#94a3b8">POWERED BY PYTHON &amp; GITHUB API</text>
</g>
</svg>
'''

output = Path("assets/branding/languages.svg")
output.write_text(
    "\n".join(line.rstrip() for line in svg.splitlines()) + "\n",
    encoding="utf-8"
)

print("Language distribution generated:", output)
