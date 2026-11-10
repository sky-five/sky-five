"""Rebuild the project lists in README.md from public repos tagged with a portfolio topic.

Topic `portfolio-data` lists a repo under "Data and AI projects", `portfolio-fun` under
"Builds for fun". Each line uses the repo's description and homepage, newest push first.
Only the text between the marker comments changes, so the rest of the README is hand-written.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

USER = "sky-five"
README = Path(__file__).resolve().parent.parent / "README.md"
SECTIONS = {"data": "portfolio-data", "fun": "portfolio-fun"}


def fetch_repos():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?type=owner&per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def line(repo):
    text = f"- **[{repo['name']}]({repo['html_url']})**"
    if repo.get("description"):
        text += f": {repo['description'].strip()}"
    if repo.get("homepage"):
        text += f" · [live]({repo['homepage']})"
    return text


def render(readme, repos):
    public = [r for r in repos if not r.get("private") and not r.get("fork") and not r.get("archived")]
    for key, topic in SECTIONS.items():
        picked = sorted((r for r in public if topic in r.get("topics", [])), key=lambda r: r["pushed_at"], reverse=True)
        body = "\n".join(line(r) for r in picked) or "- (nothing yet)"
        start, end = f"<!-- projects:{key}:start -->", f"<!-- projects:{key}:end -->"
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        if not pattern.search(readme):
            sys.exit(f"README is missing the {start} / {end} markers")
        readme = pattern.sub(lambda _: f"{start}\n{body}\n{end}", readme)
    return readme


def main():
    old = README.read_text(encoding="utf-8")
    new = render(old, fetch_repos())
    if new != old:
        README.write_text(new, encoding="utf-8")
        print("README updated")
    else:
        print("README unchanged")


if __name__ == "__main__":
    main()
