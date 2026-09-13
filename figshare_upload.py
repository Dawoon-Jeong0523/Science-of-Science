#!/usr/bin/env python3
"""Upload the metric parquet outputs of every pipeline to one Figshare item.

Scope
-----
For every domain folder ``<repo>/<domain>/output`` (Atypicality is excluded on
purpose, see .gitignore) the script uploads

* every top-level ``*.parquet`` file, renamed ``<domain>__<file>`` so that
  the flat Figshare file list stays unambiguous (``paper_metadata.parquet``
  exists in both Dimensions and OpenAlex), and
* every sub-directory that holds parquet part files (``references_w_year/``,
  ``referenced_works_w_year/``) as one or more *uncompressed* tar bundles,
  ``<domain>__<subdir>.partNN.tar``, each below ``--chunk-gb``.  Parquet is
  already compressed and Figshare items cannot hold thousands of files.

The run is idempotent: files already on the item with the same MD5 are
skipped, half-finished uploads are resumed part by part, and local MD5s are
cached in ``figshare_staging/md5_cache.json``.

Usage
-----
    python figshare_upload.py --dry-run                      # plan only
    python figshare_upload.py --domains "Case law" pcs PPP   # subset
    python figshare_upload.py                                # everything

The token is read from ``FIgshare_token.txt`` (gitignored) or ``--token-file``.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sys
import tarfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import requests

API = "https://api.figshare.com/v2"
ROOT = Path(__file__).resolve().parent
DEFAULT_ARTICLE = 33710572
EXCLUDED_DOMAINS = {"Atypicality"}
GiB = 1024 ** 3


# --------------------------------------------------------------------------- #
# Planning
# --------------------------------------------------------------------------- #
@dataclass
class Item:
    remote_name: str
    local_path: Path          # file to upload (parquet or staged tar)
    size: int
    md5: str = ""
    members: list[Path] = field(default_factory=list)  # tar members, if a bundle

    @property
    def is_bundle(self) -> bool:
        return bool(self.members)


def slug(name: str) -> str:
    return name.replace(" ", "_")


def domain_dirs(domains: list[str] | None) -> list[Path]:
    out = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name in EXCLUDED_DOMAINS or d.name.startswith("."):
            continue
        if domains and d.name not in domains:
            continue
        if (d / "output").is_dir():
            out.append(d)
    if domains:
        missing = set(domains) - {d.name for d in out}
        if missing:
            sys.exit(f"unknown domains (no <domain>/output folder): {sorted(missing)}")
    return out


def excluded(path: Path, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path.name, p) for p in patterns)


def plan_domain(domain: Path, staging: Path, chunk_bytes: int,
                exclude: list[str]) -> list[Item]:
    items: list[Item] = []
    out = domain / "output"
    for f in sorted(out.glob("*.parquet")):
        if f.is_file() and not excluded(f, exclude):
            items.append(Item(f"{slug(domain.name)}__{f.name}", f, f.stat().st_size))
    for sub in sorted(p for p in out.iterdir() if p.is_dir()):
        parts = sorted(p for p in sub.rglob("*.parquet") if not excluded(p, exclude))
        if not parts:
            continue
        chunks: list[list[Path]] = [[]]
        acc = 0
        for p in parts:
            sz = p.stat().st_size
            if chunks[-1] and acc + sz > chunk_bytes:
                chunks.append([])
                acc = 0
            chunks[-1].append(p)
            acc += sz
        for i, members in enumerate(chunks, 1):
            suffix = f".part{i:02d}" if len(chunks) > 1 else ""
            name = f"{slug(domain.name)}__{sub.name}{suffix}.tar"
            # tar size is only known once built; use the member total as estimate
            est = sum(p.stat().st_size for p in members) + 1024 * (len(members) + 2)
            items.append(Item(name, staging / name, est, members=members))
    return items


def build_bundle(item: Item, log) -> None:
    """Create the tar for a bundle item if the staged copy is missing/stale."""
    manifest = item.local_path.with_suffix(".tar.members.json")
    want = [{"p": str(p.relative_to(ROOT)), "s": p.stat().st_size,
             "m": int(p.stat().st_mtime)} for p in item.members]
    if item.local_path.exists() and manifest.exists():
        if json.loads(manifest.read_text()) == want:
            item.size = item.local_path.stat().st_size
            return
    log(f"  building bundle {item.remote_name} ({len(item.members)} members)")
    tmp = item.local_path.with_suffix(".tar.tmp")
    with tarfile.open(tmp, "w", format=tarfile.PAX_FORMAT) as tf:
        for p in item.members:
            tf.add(p, arcname=str(p.relative_to(ROOT)), recursive=False)
    tmp.replace(item.local_path)
    manifest.write_text(json.dumps(want))
    item.size = item.local_path.stat().st_size


# --------------------------------------------------------------------------- #
# MD5 with cache
# --------------------------------------------------------------------------- #
class Md5Cache:
    def __init__(self, path: Path):
        self.path = path
        self.data = json.loads(path.read_text()) if path.exists() else {}

    def get(self, p: Path) -> str:
        st = p.stat()
        key = str(p)
        hit = self.data.get(key)
        if hit and hit["size"] == st.st_size and hit["mtime"] == int(st.st_mtime):
            return hit["md5"]
        h = hashlib.md5()
        with open(p, "rb") as fh:
            for block in iter(lambda: fh.read(64 * 1024 * 1024), b""):
                h.update(block)
        self.data[key] = {"size": st.st_size, "mtime": int(st.st_mtime), "md5": h.hexdigest()}
        self.path.write_text(json.dumps(self.data, indent=1))
        return self.data[key]["md5"]


# --------------------------------------------------------------------------- #
# Figshare client
# --------------------------------------------------------------------------- #
class Figshare:
    def __init__(self, token: str, article: int, log):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"token {token}"
        self.article = article
        self.log = log

    def _req(self, method: str, url: str, retries: int = 6, **kw):
        kw.setdefault("timeout", (30, 600))
        for attempt in range(1, retries + 1):
            try:
                r = self.s.request(method, url, **kw)
                if r.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"{r.status_code} {r.text[:200]}", response=r)
                r.raise_for_status()
                return r
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
                if attempt == retries:
                    raise
                wait = min(2 ** attempt, 60)
                self.log(f"    {method} {url.split('/v2/')[-1][:60]} failed ({e}); retry in {wait}s")
                time.sleep(wait)

    def account(self) -> dict:
        return self._req("GET", f"{API}/account").json()

    def article_files(self) -> list[dict]:
        return self._req("GET", f"{API}/account/articles/{self.article}/files",
                         params={"page_size": 1000}).json()

    def delete_file(self, file_id: int) -> None:
        self._req("DELETE", f"{API}/account/articles/{self.article}/files/{file_id}")

    def initiate(self, item: Item) -> str:
        body = {"name": item.remote_name, "md5": item.md5, "size": item.size}
        r = self._req("POST", f"{API}/account/articles/{self.article}/files", json=body)
        return r.json()["location"]

    def file_info(self, location: str) -> dict:
        return self._req("GET", location).json()

    def upload_parts(self, item: Item, location: str) -> None:
        info = self.file_info(location)
        upload_url = info["upload_url"]
        parts = self._req("GET", upload_url).json()["parts"]
        pending = [p for p in parts if p["status"] != "COMPLETE"]
        self.log(f"  {len(parts)} parts, {len(pending)} pending")
        done_bytes = sum(p["endOffset"] - p["startOffset"] + 1 for p in parts) - \
            sum(p["endOffset"] - p["startOffset"] + 1 for p in pending)
        t0 = time.time()
        with open(item.local_path, "rb") as fh:
            for p in pending:
                fh.seek(p["startOffset"])
                data = fh.read(p["endOffset"] - p["startOffset"] + 1)
                self._req("PUT", f"{upload_url}/{p['partNo']}", data=data)
                done_bytes += len(data)
                el = time.time() - t0
                if p["partNo"] % 20 == 0 or p is pending[-1]:
                    rate = (done_bytes / GiB) / el * 1024 if el else 0
                    self.log(f"    part {p['partNo']}/{len(parts)}  "
                             f"{done_bytes / GiB:.2f}/{item.size / GiB:.2f} GiB  {rate:.0f} MiB/s")
        self._req("POST", location)  # complete
        self.wait_available(item, location)

    # statuses Figshare reports while a completed upload is still being processed
    PROCESSING = ("created", "ic_checking", "moving_to_final")

    def wait_available(self, item: Item, location: str, max_wait_s: int = 300) -> None:
        """Poll until the server-side integrity check finishes and compare MD5."""
        t0 = time.time()
        while True:
            info = self.file_info(location)
            st = info.get("status")
            if st == "available":
                if info.get("computed_md5") and info["computed_md5"] != item.md5:
                    raise RuntimeError(f"md5 mismatch after upload for {item.remote_name}")
                return
            if st not in self.PROCESSING:
                raise RuntimeError(f"unexpected status {st} for {item.remote_name}")
            if time.time() - t0 > max_wait_s:
                self.log(f"  (status still {st}; will be verified on next run)")
                return
            time.sleep(3)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def human(n: float) -> str:
    return f"{n / GiB:6.2f} GiB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--article", type=int, default=DEFAULT_ARTICLE)
    ap.add_argument("--token-file", default=str(ROOT / "FIgshare_token.txt"))
    ap.add_argument("--domains", nargs="*", help="domain folders to include (default: all but Atypicality)")
    ap.add_argument("--exclude", nargs="*", default=[], help="fnmatch patterns on file names to skip, e.g. '*_old*'")
    ap.add_argument("--include", nargs="*", default=[],
                    help="fnmatch patterns on file names to KEEP; everything else in the chosen "
                         "domains is skipped. Applied after --exclude.")
    ap.add_argument("--staging", default=str(ROOT / "figshare_staging"))
    ap.add_argument("--chunk-gb", type=float, default=15.0, help="max size of one tar bundle")
    ap.add_argument("--replace", action="store_true", help="replace remote files whose md5 differs")
    ap.add_argument("--dry-run", action="store_true", help="plan and quota check only")
    ap.add_argument("--readme", metavar="PATH",
                    help="also upload this file as README.md (e.g. FIGSHARE_README.md); "
                         "with --readme-only nothing else is planned")
    ap.add_argument("--readme-only", action="store_true")
    args = ap.parse_args()

    staging = Path(args.staging)
    staging.mkdir(exist_ok=True)
    logf = open(staging / "upload.log", "a")

    def log(msg: str) -> None:
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    token = Path(args.token_file).read_text().strip()
    fs = Figshare(token, args.article, log)
    acct = fs.account()
    quota, used = acct["quota"], acct["used_quota"]
    free = quota - used
    log(f"account {acct.get('email')}  quota {human(quota)}  used {human(used)}  free {human(free)}")

    remote = {f["name"]: f for f in fs.article_files()}
    log(f"article {args.article}: {len(remote)} files already present")

    items: list[Item] = []
    if args.readme:
        rp = Path(args.readme).resolve()
        items.append(Item("README.md", rp, rp.stat().st_size))
    if not args.readme_only:
        for d in domain_dirs(args.domains):
            items += plan_domain(d, staging, int(args.chunk_gb * GiB), args.exclude)
        if args.include:
            items = [i for i in items
                     if any(fnmatch.fnmatch(i.local_path.name, p) or fnmatch.fnmatch(i.remote_name, p)
                            for p in args.include)]
    if not items:
        log("nothing to upload")
        return 0

    # ---- plan report -------------------------------------------------------
    total = sum(i.size for i in items)
    log(f"plan: {len(items)} files, {human(total)} total  (domains: "
        f"{sorted({i.remote_name.split('__')[0] for i in items})})")
    for i in items:
        status = remote.get(i.remote_name, {}).get("status", "-")
        kind = f"tar of {len(i.members)} parts" if i.is_bundle else "parquet"
        log(f"  {human(i.size)}  {i.remote_name:60s} {kind:22s} remote={status}")
    if total > free:
        log(f"WARNING: plan ({human(total)}) exceeds free quota ({human(free)}); "
            f"files that do not fit will be skipped")
    if args.dry_run:
        return 0

    cache = Md5Cache(staging / "md5_cache.json")
    manifest_path = staging / "uploaded_manifest.jsonl"
    n_ok = n_skip = n_fail = 0
    for item in items:
        log(f"-> {item.remote_name}")
        try:
            if item.is_bundle:
                build_bundle(item, log)
            item.md5 = cache.get(item.local_path)
            existing = remote.get(item.remote_name)
            if existing:
                same = existing.get("supplied_md5") == item.md5 or existing.get("computed_md5") == item.md5
                if existing.get("status") == "available" and same:
                    log("  already on Figshare with identical md5, skipping")
                    n_skip += 1
                    continue
                location = f"{API}/account/articles/{args.article}/files/{existing['id']}"
                if existing.get("status") == "created" and same:
                    log("  resuming incomplete upload")
                    fs.upload_parts(item, location)
                    n_ok += 1
                    continue
                if existing.get("status") in fs.PROCESSING and same:
                    log("  upload complete, waiting for Figshare integrity check")
                    fs.wait_available(item, location)
                    n_skip += 1
                    continue
                if not args.replace:
                    log(f"  remote file exists with different md5/status={existing.get('status')}; "
                        f"skipping (use --replace)")
                    n_skip += 1
                    continue
                log("  deleting stale remote copy")
                fs.delete_file(existing["id"])
            if item.size > free:
                log(f"  does not fit in remaining quota ({human(free)}), skipping")
                n_skip += 1
                continue
            location = fs.initiate(item)
            fs.upload_parts(item, location)
            free -= item.size
            with open(manifest_path, "a") as mf:
                mf.write(json.dumps({"remote_name": item.remote_name, "size": item.size, "md5": item.md5,
                                     "local": os.path.relpath(item.local_path, ROOT) if not item.is_bundle
                                     else [os.path.relpath(p, ROOT) for p in item.members],
                                     "location": location, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            n_ok += 1
            log(f"  done  (free quota now {human(free)})")
        except Exception as e:  # keep going with the next file
            n_fail += 1
            log(f"  FAILED: {e!r}")
    log(f"finished: uploaded {n_ok}, skipped {n_skip}, failed {n_fail}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
