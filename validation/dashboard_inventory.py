"""Collect the public dashboard's derived-table inventory without scanning tables.

``build_inventory(source_root)`` reads Parquet footers, filesystem metadata, and
small provenance documents under the local Science of Science project. Returned
paths are relative to that project; its private absolute location is not exposed.
Importing this module does not read files or build an inventory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re


# Explicitly inventory final top-level outputs, including the documented legacy
# team-size table. Dated partitions, backups, and reference intermediates are not
# separate final outputs and must not inflate the displayed totals.
_PATSTAT_TABLES = (
    "patstat_citation.parquet",
    "patstat_citation_trend.parquet",
    "patstat_disruption.parquet",
    "patstat_disruption_trend.parquet",
    "patstat_disruption_trend_summary.parquet",
    "patstat_feg_disruption_trend.parquet",
    "patstat_hit_probability.parquet",
    "patstat_inventor.parquet",
    "patstat_inventor_country.parquet",
    "patstat_metadata.parquet",
    "patstat_reference.parquet",
    "patstat_sb.parquet",
    "patstat_uniqueC_trend.parquet",
    "patstat_z_score.parquet",
    "z_score_pair.parquet",
)
CANONICAL_TABLES = {
    "OpenAlex": (
        "paper",
        (
            "paper_author.parquet",
            "paper_author_country.parquet",
            "paper_citation.parquet",
            "paper_citation_trend.parquet",
            "paper_disruption.parquet",
            "paper_hit_probability.parquet",
            "paper_metadata.parquet",
            "paper_sb.parquet",
            "paper_team_size.parquet",
            "paper_z_score.parquet",
            "z_score_pair.parquet",
        ),
    ),
    # The same paper metrics on the Dimensions June 2025 index. Atypicality has been
    # written for the 1990-2000 partition only, so that partition is the canonical file
    # here (there is no merged paper_z_score.parquet to represent it).
    "Dimensions": (
        "dimension",
        (
            "paper_author.parquet",
            "paper_author_country.parquet",
            "paper_citation.parquet",
            "paper_citation_trend.parquet",
            "paper_disruption.parquet",
            "paper_hit_probability.parquet",
            "paper_metadata.parquet",
            "paper_sb.parquet",
            "paper_z_score_1990_2000.parquet",
            "z_score_pair_1990_2000.parquet",
        ),
    ),
    "PatentView": (
        "patent",
        (
            "patent_citation.parquet",
            "patent_citation_trend.parquet",
            "patent_disruption.parquet",
            "patent_disruption_app.parquet",
            "patent_disruption_compare.parquet",
            "patent_feg_disruption_trend.parquet",
            "patent_hit_probability.parquet",
            "patent_inventor_country.parquet",
            "patent_metadata.parquet",
            "patent_reference.parquet",
            "patent_sb.parquet",
            "patent_z_score.parquet",
            "z_score_pair.parquet",
        ),
    ),
    # PATSTAT Global 2023 Autumn, three sets: "<directory>:<output folder>" names a further
    # output folder of the same pipeline (default "output"). Same file names in all three:
    # filing clock (output), grant clock (output_grant), DOCDB family unit (output_family).
    **{key: ("patstat", _PATSTAT_TABLES)
       for key in ("PATSTAT", "PATSTAT:output_grant", "PATSTAT:output_family")},
    "pcs": (
        "pcs",
        (
            "pcs_citation.parquet",
            "pcs_citation_trend.parquet",
            "pcs_hit_probability.parquet",
        ),
    ),
    "PPP": ("ppp", ("ppp_paper_trend.parquet", "ppp_patent_trend.parquet")),
    "Case law": (
        "caselaw",
        (
            "case_citation.parquet",
            "case_citation_trend.parquet",
            "case_disruption.parquet",
            "case_feg_disruption_trend.parquet",
            "case_hit_probability.parquet",
            "case_metadata.parquet",
            "case_sb.parquet",
        ),
    ),
}

GRAINS = {
    "paper_author.parquet": (
        "One work_id with ordered, deduplicated author IDs and team_size."
    ),
    "paper_team_size.parquet": "One paper_id with a legacy team_size value.",
    "paper_author_country.parquet": (
        "One work with the ISO2 countries of its authors' institutions: the sorted "
        "distinct set, the per-country author counts, and the first and last author's "
        "own countries."
    ),
    "patent_inventor_country.parquet": (
        "One utility patent with the ISO2 countries of the inventor addresses printed "
        "on the grant, the per-country inventor counts, and the assignee countries."
    ),
    "paper_z_score_1990_2000.parquet": (
        "One publication with journal-pair atypicality scores; 1990-2000 partition "
        "only, no merged corpus-wide file yet."
    ),
    "z_score_pair_1990_2000.parquet": (
        "One journal pair per cohort year; 1990-2000 partition only."
    ),
    "patent_reference.parquet": (
        "One distinct (citing_id, cited_id, type) reference; grant_id identifies "
        "the granted cited endpoint."
    ),
    "patent_disruption_compare.parquet": (
        "One citation window (3, 5, 10, or all) with paired comparison statistics."
    ),
    "patent_feg_disruption_trend.parquet": (
        "One grant cohort year with aggregate metrics."
    ),
    "case_feg_disruption_trend.parquet": (
        "One decision cohort year with aggregate metrics."
    ),
    "patstat_metadata.parquet": (
        "One application (appln_id) in the universe: a patent of invention, a real application, "
        "filed 1900-2023, with its office, years, family, classification, WIPO sector and persons."
    ),
    "patstat_reference.parquet": (
        "One citation row resolved to (citing application, cited application), with both clock "
        "years, age, the recorded origin and its examiner / applicant / other bucket, and a "
        "replenished flag."
    ),
    "patstat_citation.parquet": (
        "One cited application with citation rows (C) and distinct citing applications (uniqueC) "
        "per window and provenance bucket."
    ),
    "patstat_citation_trend.parquet": "One cited application per citing year.",
    "patstat_uniqueC_trend.parquet": (
        "One cited application per year since filing (grant) with its new distinct citing applications."
    ),
    "patstat_disruption.parquet": (
        "One application in the citation graph with CD, F / E / G and ni / nj / nk per window, plus "
        "CD percentiles within filing year x CPC Section."
    ),
    "patstat_disruption_trend.parquet": (
        "One application per year with new and cumulative ni / nj / nk, CD and F / E / G."
    ),
    "patstat_disruption_trend_summary.parquet": (
        "One (cohort year, years since) cell with mean cumulative CD / F / E / G."
    ),
    "patstat_feg_disruption_trend.parquet": "One cohort year with aggregate metrics.",
    "patstat_hit_probability.parquet": (
        "One application with a WIPO sector: citation percentiles within sector x cohort year."
    ),
    "patstat_sb.parquet": "One cited application with its beauty coefficient and awakening time.",
    "patstat_z_score.parquet": (
        "One application with at least two CPC subclasses: atypicality z summaries."
    ),
    "patstat_inventor.parquet": (
        "One application with inventors: the person_id list in sequence order, its length, "
        "first and last (person records, not disambiguated inventors)."
    ),
    "patstat_inventor_country.parquet": (
        "One application with inventors: the ISO2 countries of its inventors and applicants."
    ),
    "ppp_paper_trend.parquet": (
        "One paper-patent linkage pair per citing year with paper-side counts."
    ),
    "ppp_patent_trend.parquet": (
        "One paper-patent linkage pair per citing year with patent-side counts."
    ),
}

LEGACY_TEAM_SIZE_NOTE = (
    "The current project has no producer for this legacy file. Native team-size "
    "validation uses the reproducible paper_author.parquet output, whose "
    "team_size counts distinct authors rather than affiliation rows."
)

_PPP_SOURCES = {
    "plus": "PPP/_patent_paper_pairs_plus.csv",
    "adjusted": "PPP/finalpppsadjusted_260831.csv",
}


def _utc(timestamp: float | None = None) -> str:
    value = (
        datetime.now(timezone.utc)
        if timestamp is None
        else datetime.fromtimestamp(timestamp, timezone.utc)
    )
    return value.isoformat().replace("+00:00", "Z")


def _grain(name: str, family: str) -> str:
    if name == "z_score_pair.parquet":
        kind = "journal" if family == "paper" else "CPC-subclass"
        return f"One {kind} pair per cohort year."
    if name in GRAINS:
        return GRAINS[name]
    if name.endswith("_citation_trend.parquet"):
        return "One document per citing year."
    return "One document."


def _paper_provenance(root: Path, paper_rows: int) -> dict:
    relative_path = "OpenAlex/output/paper_z_score_provenance.json"
    result = {
        "path": relative_path,
        "producer": "OpenAlex/notebook/paper_z_score_merge.ipynb",
        "status": "unavailable",
    }
    path = root / relative_path
    if not path.is_file():
        return result
    raw = json.loads(path.read_text(encoding="utf-8"))
    recorded_rows = raw.get("rows", {}).get("paper_z_score")
    coverage = raw.get("coverage_years")
    if (
        recorded_rows != paper_rows
        or not isinstance(coverage, list)
        or len(coverage) != 2
        or not all(isinstance(year, int) for year in coverage)
        or coverage[0] > coverage[1]
    ):
        result["status"] = "does_not_match_current_output"
        return result
    result.update(
        status="row_count_matches_current_output",
        coverage_years=coverage,
        paper_rows=paper_rows,
        note=(
            "Coverage is explicitly recorded in the provenance file; the bare "
            "output filename does not imply coverage beginning in 1900."
        ),
    )
    # Only known, non-path metadata is copied into the public result.
    if raw.get("vintage") == (
        "post-MAG-alignment fix (is_journal-only mapping) and post two-pass rewrite"
    ):
        result["vintage"] = raw["vintage"]
    result["partitions"] = [
        value
        for value in raw.get("partitions", [])
        if isinstance(value, str)
        and re.fullmatch(r"paper_z_score_\d{4}_\d{4}\.parquet", value)
    ]
    return result


def _ppp_provenance(root: Path, files: list[dict]) -> dict:
    """Match output counts to a recorded run, without inferring the pair count."""
    expected = {
        Path(row["path"]).stem: row["rows"]
        for row in files
        if row["family"] == "ppp"
    }
    result = {
        "status": "no_matching_run_log",
        "producer": "PPP/notebook/ppp_citation_trend.ipynb",
        "configuration": "PPP/ppp_common.py",
        "output_rows": expected,
        "note": (
            "Pair counts describe linkage records, not trend rows. Saved outputs "
            "embedded in the producing notebook may be stale; provenance below "
            "requires a job log matching both current output row counts."
        ),
    }
    pattern = re.compile(
        r"\[ppp\] pairs '(plus|adjusted)': ([^\r\n]+?) -> "
        r"([\d,]+) pairs \| ([\d,]+) distinct papers \| "
        r"([\d,]+) distinct patents"
    )
    matches = []
    for path in (root / "jobs/PPP/logs").glob("*.out"):
        text = path.read_text(encoding="utf-8", errors="replace")
        found = list(pattern.finditer(text))
        if not found:
            continue
        # A single log should describe one producing run. Ambiguous multi-run
        # logs are not suitable provenance for a single pair of output files.
        if len(found) != 1:
            continue
        source, basename, pairs, papers, patents = found[0].groups()
        source_path = _PPP_SOURCES[source]
        if basename != Path(source_path).name:
            continue
        recorded = {}
        for stem in expected:
            counts = re.findall(rf"{re.escape(stem)}: ([\d,]+) rows", text)
            if len(counts) == 1:
                recorded[stem] = int(counts[0].replace(",", ""))
        if recorded != expected:
            continue
        stat = path.stat()
        entry = {
            "source": source_path,
            "source_option": source,
            "pairs": int(pairs.replace(",", "")),
            "distinct_papers": int(papers.replace(",", "")),
            "distinct_patents": int(patents.replace(",", "")),
            "run_log": path.relative_to(root).as_posix(),
            "run_log_modified_utc": _utc(stat.st_mtime),
        }
        if (root / source_path).is_file():
            entry["source_bytes"] = (root / source_path).stat().st_size
        matches.append((stat.st_mtime_ns, entry))
    if matches:
        result.update(max(matches, key=lambda item: item[0])[1])
        result["status"] = "run_log_matches_current_output_counts"
    return result


def build_inventory(source_root: Path) -> dict:
    """Return JSON-serializable metadata for the canonical derived tables (43 as of 2026-09-11).

    Raises FileNotFoundError for a missing canonical file and RuntimeError if a
    file changes during its footer read. Rows are stored records, not unique
    documents summed across tables. Neither Parquet data pages nor large raw
    inputs are read.
    """
    import pyarrow.parquet as pq

    root = Path(source_root)
    files = []
    excluded_files = []
    for key, (family, names) in CANONICAL_TABLES.items():
        directory, _, outdir = key.partition(":")
        output = root / directory / (outdir or "output")
        for name in names:
            path = output / name
            if not path.is_file():
                raise FileNotFoundError(f"Missing canonical output: {path}")
            before = path.stat()
            parquet = pq.ParquetFile(path)
            try:
                metadata = parquet.metadata
                schema = parquet.schema_arrow
                row = {
                    "path": path.relative_to(root).as_posix(),
                    "family": family,
                    "rows": metadata.num_rows,
                    "bytes": before.st_size,
                    "columns": schema.names,
                    "schema": [
                        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                        for field in schema
                    ],
                    "row_groups": metadata.num_row_groups,
                    "modified_utc": _utc(before.st_mtime),
                    "grain": _grain(name, family),
                }
            finally:
                parquet.close()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError(f"Output changed while reading its footer: {path}")
            if name == "paper_team_size.parquet":
                row.update(
                    status="legacy",
                    note=LEGACY_TEAM_SIZE_NOTE,
                    provenance="OpenAlex/notebook/paper_author.ipynb",
                )
            elif name == "paper_author.parquet":
                row["provenance"] = "OpenAlex/notebook/paper_author.ipynb"
            if family == "patstat":
                row["note"] = {
                    "output_grant": "Grant clock: grant years at both ends, granted applications only.",
                    "output_family": ("Family unit: one row per DOCDB family (key docdb_family_id), "
                                      "earliest priority year at both ends, distinct family-to-family "
                                      "citations; read 'application' in the row meaning as 'family'."),
                }.get(outdir, "Filing clock: filing years at both ends, every application.")
            elif name == "patent_reference.parquet":
                row["provenance"] = "PatentView/notebook/patent_reference.ipynb"
                row["note"] = (
                    "Granted and application references may share a grant_id. "
                    "Deduplicate (citing_id, grant_id) when unique patent edges "
                    "are required; cited_id preserves the original cited identifier."
                )
            files.append(row)
        excluded_files.extend(
            path.relative_to(root).as_posix()
            for path in output.glob("*.parquet*")
            if path.is_file() and path.name not in names
        )

    paper_rows = next(
        row["rows"] for row in files if row["path"] == "OpenAlex/output/paper_z_score.parquet"
    )
    paper_provenance = _paper_provenance(root, paper_rows)
    for row in files:
        if row["path"] in {
            "OpenAlex/output/paper_z_score.parquet",
            "OpenAlex/output/z_score_pair.parquet",
        }:
            row["provenance"] = paper_provenance["path"]
            if "coverage_years" in paper_provenance:
                row["coverage_years"] = paper_provenance["coverage_years"]

    return {
        "schema_version": 1,
        "source_project": "Science of Science",
        "generated_utc": _utc(),
        "method": (
            "Parquet footers and filesystem metadata only for table inventories; "
            "small provenance JSON and run logs for provenance. No table data "
            "pages or large raw inputs are scanned."
        ),
        "count_unit": "Stored rows across derived tables; not unique documents.",
        "files": files,
        "total_files": len(files),
        "total_rows": sum(row["rows"] for row in files),
        "total_bytes": sum(row["bytes"] for row in files),
        "excluded_files": sorted(excluded_files),
        "excluded_datasets": [
            {
                "path": "OpenAlex/output/referenced_works_w_year",
                "reason": "Sharded reference intermediate, not a final top-level table.",
            }
        ],
        "exclusions_note": (
            "Explicit canonical top-level outputs only. Old vintages, backups, "
            "dated z-score partitions and sharded reference intermediates are "
            "excluded. The legacy paper_team_size table remains listed and labeled."
        ),
        "paper_z_score_provenance": paper_provenance,
        "ppp_provenance": _ppp_provenance(root, files),
    }
