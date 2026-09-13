"""Paths for the patent-metric notebooks, on Midway.

The ten notebooks in notebook/ were written against a Windows layout: a
`for _ in range(6): os.chdir('..')` hunt for a marker directory, then
`E:/Dawoon Jeong/Data/PatentView/Granted` and `<root>/notebook/patent/output`. None of that
exists here, and the chdir hunt is actively harmful — it walks up from wherever the kernel
happens to start and silently settles somewhere arbitrary.

This module replaces all of it with absolute paths, so a notebook works the same whether it
is run from its own directory, from the project root, or by run_notebook.py.

    import pv_common as pv
    pv.preflight()               # what is present, what is missing
    z = pv.granted('g_patent.tsv.zip')
"""
from __future__ import annotations

import os

BASE       = "/project/jevans/Dawoon/Science of Science/PatentView"
GRANTED    = f"{BASE}/Granted"          # PatentsView granted bulk files (*.tsv.zip)
PREGRANTED = f"{BASE}/Pregranted"       # pre-grant publication files
OUT        = f"{BASE}/output"           # every notebook writes its parquet here
CACHE      = f"{BASE}/cache"            # derived graphs/CSR, not results
for _d in (OUT, CACHE):
    os.makedirs(_d, exist_ok=True)

# The project already holds a complete PatentsView download. The copy under BASE/Granted was
# still in progress when this was written (17 of 35 files), so a file missing there is
# resolved from the project copy instead — and `granted()` says so the first time it does,
# because a silent redirect to a different snapshot is exactly the kind of thing that makes a
# result impossible to reproduce later.
FALLBACK_GRANTED = "/project/jevans/Dawoon/PatentView/Granted"
ALLOW_FALLBACK = True

# What each notebook needs. Used by preflight() so a missing input is a sentence, not a
# stack trace forty minutes into a run.
NEEDS = {
    "patent_metadata":            ["g_patent.tsv.zip", "g_application.tsv.zip",
                                   "g_cpc_current.tsv.zip", "g_assignee_disambiguated.tsv.zip",
                                   "g_inventor_disambiguated.tsv.zip",
                                   "g_us_patent_citation.tsv.zip"],
    "patent_citation":            ["g_patent.tsv.zip", "g_us_patent_citation.tsv.zip",
                                   "g_us_application_citation.tsv.zip",
                                   "@pg_granted_pgpubs_crosswalk.tsv.zip"],
    "patent_citation_trend":      ["g_patent.tsv.zip", "g_us_patent_citation.tsv.zip",
                                   "g_us_application_citation.tsv.zip",
                                   "@pg_granted_pgpubs_crosswalk.tsv.zip"],
    "patent_reference":           ["g_patent.tsv.zip", "g_us_patent_citation.tsv.zip",
                                   "g_us_application_citation.tsv.zip",
                                   "@pg_granted_pgpubs_crosswalk.tsv.zip"],
    "patent_disruption":          ["g_patent.tsv.zip", "g_us_patent_citation.tsv.zip"],
    "patent_disruption_app_add":  ["g_patent.tsv.zip", "g_us_patent_citation.tsv.zip",
                                   "g_us_application_citation.tsv.zip",
                                   "@pg_granted_pgpubs_crosswalk.tsv.zip"],
    "patent_sb":                  ["g_patent.tsv.zip", "g_us_patent_citation.tsv.zip"],
    "patent_hit_probability":     ["g_wipo_technology.tsv.zip"],
    "patent_z_score":             ["g_cpc_current.tsv.zip"],
    "patent_inventor_country":    ["g_patent.tsv.zip", "g_inventor_disambiguated.tsv.zip",
                                   "g_assignee_disambiguated.tsv.zip",
                                   "g_location_disambiguated.tsv.zip"],
    "patent_disruption_app_compare": [],     # reads only this folder's own output
    "patent_feg_disruption_trend":   [],     # ditto
}

_ANNOUNCED = set()


def granted(name: str) -> str:
    """Absolute path to a granted bulk file, preferring BASE/Granted."""
    p = f"{GRANTED}/{name}"
    if os.path.exists(p):
        return p
    q = f"{FALLBACK_GRANTED}/{name}"
    if ALLOW_FALLBACK and os.path.exists(q):
        if name not in _ANNOUNCED:
            print(f"[pv] {name}: not in {GRANTED} yet -> using {FALLBACK_GRANTED}")
            _ANNOUNCED.add(name)
        return q
    raise FileNotFoundError(
        f"{name} is in neither {GRANTED} nor {FALLBACK_GRANTED}.\n"
        f"        The BASE/Granted copy was still running when this was set up; wait for it, "
        f"or point GRANTED at the project copy.")


def pregranted(name: str) -> str:
    p = f"{PREGRANTED}/{name}"
    if os.path.exists(p):
        return p
    raise FileNotFoundError(
        f"{name} is not in {PREGRANTED}, and there is no copy of it anywhere under "
        f"/project/jevans/Dawoon.\n"
        f"        The pre-grant bulk files have not been downloaded. The notebooks that need "
        f"it (patent_citation, patent_citation_trend, patent_disruption_app_add) cannot run "
        f"until they are.")


def out(name: str) -> str:
    return f"{OUT}/{name}"


def preflight(notebook: str | None = None) -> bool:
    """Report which inputs are present. Returns True if everything needed is there."""
    names = [notebook] if notebook else sorted(NEEDS)
    print(f"granted    : {GRANTED}"
          f"   ({len([f for f in os.listdir(GRANTED) if f.endswith('.zip')])} zip files)"
          if os.path.isdir(GRANTED) else f"granted    : {GRANTED}   MISSING")
    print(f"pregranted : {PREGRANTED}"
          f"   ({len(os.listdir(PREGRANTED))} files)"
          if os.path.isdir(PREGRANTED) else f"pregranted : {PREGRANTED}   MISSING")
    print(f"output     : {OUT}\n")
    ok_all = True
    for nb in names:
        rows = []
        for f in NEEDS.get(nb, []):
            pre = f.startswith("@")
            f = f.lstrip("@")
            try:
                p = pregranted(f) if pre else granted(f)
                where = "local" if p.startswith(GRANTED) or p.startswith(PREGRANTED) else "project"
                rows.append((f, where))
            except FileNotFoundError:
                rows.append((f, "MISSING"))
                ok_all = False
        miss = [f for f, w in rows if w == "MISSING"]
        state = "OK" if not miss else f"MISSING {len(miss)}"
        print(f"  {nb:<32}{state}")
        for f, w in rows:
            if w == "MISSING":
                print(f"      {f}  <- not available")
    return ok_all
