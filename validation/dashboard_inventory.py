"""Collect the public dashboard's derived-table inventory without scanning tables.

``build_inventory(source_root)`` reads Parquet footers, filesystem metadata, and
small provenance documents under the local Science of Science project, plus the
first rows of each table for one example value per column. Column descriptions
come from ``dashboard_columns``. Returned paths are relative to that project; its
private absolute location is not exposed. Importing this module does not read
files or build an inventory.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import json
import math
import re

from dashboard_columns import describe, is_personal


# Explicitly inventory final top-level outputs. Dated partitions, backups, and reference intermediates are not
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


def _usable(value) -> bool:
    return value is not None and value != [] and not (isinstance(value, float) and math.isnan(value))


def _example_text(value, limit: int = 96) -> str | None:
    """One cell as page text: floats to 6 significant digits, lists to their first three items."""
    if not _usable(value):
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        items = [_example_text(item, 32) or "null" for item in value[:3]]
        more = f", … (+{len(value) - 3})" if len(value) > 3 else ""
        return "[" + ", ".join(items) + more + "]"
    if isinstance(value, dict):
        value = json.dumps(value, default=str)
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _examples(parquet, batch_rows: int = 4096, max_batches: int = 100) -> dict:
    """One example value per column from the first rows of a table.

    Values come from one representative row where possible (the first row of the first
    batch with the most non-null values), so a table's examples belong together; a column
    that is null there takes its first non-null value in the first ``max_batches`` batches.
    """
    found = {}
    for number, batch in enumerate(parquet.iter_batches(batch_size=batch_rows)):
        columns = {name: batch.column(i).to_pylist() for i, name in enumerate(batch.schema.names)}
        if number == 0:
            scores = [sum(_usable(values[i]) for values in columns.values()) for i in range(batch.num_rows)]
            row = scores.index(max(scores)) if scores else 0
            found = {name: values[row] for name, values in columns.items() if values and _usable(values[row])}
        for name, values in columns.items():
            if name not in found:
                value = next((v for v in values if _usable(v)), None)
                if value is not None:
                    found[name] = value
        if len(found) == len(columns) or number + 1 >= max_batches:
            break
    return {name: _example_text(value) for name, value in found.items()}


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
    # PPP was rerun through jobs/OpenAlex/nbsave.sbatch on 2026-10-08, so its log is there.
    logs = [*(root / "jobs/PPP/logs").glob("*.out"), *(root / "jobs/OpenAlex/logs").glob("ppp_citation_trend-*.out")]
    for path in logs:
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
    documents summed across tables. Only the first rows of each table are read
    (for the column examples); large raw inputs are not read.
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
                relative = path.relative_to(root).as_posix()
                examples = _examples(parquet)
                fields = []
                for field in schema:
                    entry = {"name": field.name, "type": str(field.type), "nullable": field.nullable,
                             "description": describe(relative, field.name)}
                    # columns that carry people's names are described but get no example
                    if is_personal(relative, field.name):
                        entry["example_withheld"] = True
                    else:
                        entry["example"] = examples.get(field.name)
                    fields.append(entry)
                row = {
                    "path": relative,
                    "family": family,
                    "rows": metadata.num_rows,
                    "bytes": before.st_size,
                    "columns": schema.names,
                    "schema": fields,
                    "row_groups": metadata.num_row_groups,
                    "modified_utc": _utc(before.st_mtime),
                    "grain": _grain(name, family),
                }
            finally:
                parquet.close()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError(f"Output changed while reading its footer: {path}")
            if name == "paper_author.parquet":
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
            "Parquet footers and filesystem metadata for table inventories, plus the "
            "first rows of each table for one example value per column; small "
            "provenance JSON and run logs for provenance. No table is scanned in "
            "full and no large raw input is read."
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
            "excluded. The legacy paper_team_size table (no producer) was retired with the "
            "2026-09-23 OpenAlex rebuild; team size lives in paper_author."
        ),
        "paper_z_score_provenance": paper_provenance,
        "ppp_provenance": _ppp_provenance(root, files),
    }
