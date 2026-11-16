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
