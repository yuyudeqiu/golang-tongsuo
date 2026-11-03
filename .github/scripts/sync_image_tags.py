"""Reconcile Docker Hub aliases from published immutable release tags."""

import argparse
import datetime
import json
import re
import subprocess
import urllib.request

RELEASE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)-[0-9a-f]{7}")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
PLATFORMS = {("linux", "amd64"), ("linux", "arm64")}


def list_tags(image):
    url = f"https://hub.docker.com/v2/repositories/{image}/tags?page_size=100"
    tags = []
    while url:
        if not url.startswith("https://hub.docker.com/v2/"):
            raise ValueError(f"Unexpected pagination URL: {url}")
        with urllib.request.urlopen(url, timeout=60) as response:
            page = json.load(response)
        tags.extend(page["results"])
        url = page["next"]
    return tags


def eligible_releases(tags):
    releases = []
    for tag in tags:
        match = RELEASE.fullmatch(tag["name"])
        if not match:
            continue
        # Only complete, active, multi-platform releases are eligible.
        platforms = {(image.get("os"), image.get("architecture"))
                     for image in tag.get("images", []) if image.get("status") == "active"}
        if tag.get("tag_status") != "active" or not PLATFORMS <= platforms:
            continue
        if not DIGEST.fullmatch(tag.get("digest", "")):
            raise ValueError(f"Missing or invalid digest for {tag['name']}")
        version = tuple(map(int, match.groups()))
        timestamp = tag["tag_last_pushed"]
        time_format = "%Y-%m-%dT%H:%M:%S" + (".%f" if "." in timestamp else "") + "%z"
        pushed = datetime.datetime.strptime(timestamp.replace("Z", "+00:00"), time_format)
        releases.append((version, pushed, tag["name"], tag))
    if not releases:
        raise ValueError("No complete release images found; aliases were not changed")

    return sorted(releases)


def select_aliases(tags):
    aliases = {}
    for version, _, _, tag in eligible_releases(tags):
        aliases[f"{version[0]}.{version[1]}"] = tag
        aliases["latest"] = tag
    return aliases


def docker(*args):
    return subprocess.check_output(["docker", "buildx", "imagetools", *args], text=True).strip()


def sync(image, tags, apply=False):
    aliases = select_aliases(tags)
    # Refuse to overwrite an alias that points outside this complete snapshot.
    # This also fails safely if the registry listing is temporarily incomplete.
    release_digests = {entry[3]["digest"] for entry in eligible_releases(tags)}
    for tag in tags:
        if tag["name"] in aliases and tag.get("digest") not in release_digests:
            raise ValueError(f"Cannot resolve existing alias {tag['name']} to a release")

    # Validate every source before updating any alias. Copy by digest to retain
    # both platforms and attestations, independent of later tag changes.
    if apply:
        for digest in sorted({tag["digest"] for tag in aliases.values()}):
            manifest = json.loads(docker("inspect", f"{image}@{digest}", "--raw"))
            platforms = {(entry.get("platform", {}).get("os"),
                          entry.get("platform", {}).get("architecture"))
                         for entry in manifest.get("manifests", [])}
            if not PLATFORMS <= platforms:
                raise ValueError(f"Source {digest} does not contain both supported platforms")

    current = {tag["name"]: tag.get("digest") for tag in tags}
    for alias, tag in aliases.items():
        print(f"{image}:{alias} -> {tag['name']} ({tag['digest']})", flush=True)
        if not apply or current.get(alias) == tag["digest"]:
            continue
        docker("create", "--tag", f"{image}:{alias}", f"{image}@{tag['digest']}")
        actual = docker("inspect", f"{image}:{alias}", "--format", "{{.Manifest.Digest}}")
        if actual != tag["digest"]:
            raise ValueError(f"Digest verification failed for {alias}: {actual}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="Docker Hub namespace/repository")
    parser.add_argument("--apply", action="store_true", help="Push aliases (default: preview only)")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_-]+/[a-z0-9_-]+", args.image):
        parser.error("Expected a Docker Hub namespace/repository")
    sync(args.image, list_tags(args.image), args.apply)


if __name__ == "__main__":
    main()
