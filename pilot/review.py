"""Check reviewed excerpts against the supplied PDFs and render the assessments."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from functools import cache
from html import escape
from pathlib import Path
from urllib.parse import quote

PILOT = Path(__file__).resolve().parent


def read_records(name):
    return json.loads((PILOT / name).read_text(encoding="utf-8"))


def normalized(text):
    text = re.sub(r"(?<=[A-Za-z])-[ \t]*\n[ \t]*(?=[a-z])", "", text)
    return " ".join(text.split())


@cache
def page_text(pdf, page):
    text = subprocess.check_output(
        ["pdftotext", "-f", str(page), "-l", str(page), "-raw", str(pdf), "-"],
        encoding="utf-8",
    )
    return normalized(text)


def group_result(statuses):
    if not set(statuses) <= {"supports", "contradicts", "insufficient", "ambiguous"}:
        raise ValueError(f"Unknown support judgment in {statuses!r}")
    if "ambiguous" in statuses:
        return "Too vague"
    count = statuses.count("supports")
    if not count:
        return "None"
    if count == len(statuses):
        return "All"
    return "Some"


def verify_export(export, groups, sources, reviewed=False):
    raw = export.read_text()
    if export.suffix == ".json":
        rows = [json.loads(raw)]
    else:
        rows = [json.loads(line) for line in raw.splitlines()]
    records = {(r["citing_work"]["id"], r["cited_work"]["id"]): r for r in rows}
    if len(records) != len(rows):
        raise ValueError("Duplicate target and citing paper in Anekanta export")
    for group in groups:
        citer = sources[group["citer"]]
        matches = group.get("reviewed_matches", {}) if reviewed else group["matches"]
        for key, passage_id in matches.items():
            citer_id = citer["id"] if reviewed else "local:" + Path(citer["file"]).stem
            record = records[(citer_id, sources[key]["id"])]
            if record["source"]["sha256"] != citer["sha256"]:
                raise ValueError(f"Different PDF in export for {group['id']}")
            hits = [p for p in record["passages"] if p["id"] == passage_id]
            if len(hits) != 1 or hits[0]["location"]["pdf_page"] != group["page"]:
                raise ValueError(f"Missing or displaced match for {group['id']}")
            if reviewed and (
                hits[0].get("review") != "source_checked"
                or hits[0].get("marker") != group["marker"]
            ):
                raise ValueError(f"Unverified or different marker for {group['id']}")
            # Anekanta collapses PDF line breaks, retaining the line-ending hyphen.
            excerpt = re.sub(r"(?<=[A-Za-z])- +(?=[a-z])", "", hits[0]["quote"])
            if group["passage"] not in excerpt:
                raise ValueError(f"Different passage in export for {group['id']}")


def run(pdf_dir, out, local_links, export, reviewed):
    groups = read_records("groups.json")
    assessments = read_records("assessments.json")
    sources = read_records("sources.json")
    if export:
        verify_export(export, groups, sources)
    if reviewed:
        verify_export(reviewed, groups, sources, reviewed=True)
    paths = {key: pdf_dir / value["file"] for key, value in sources.items()}
    for key, path in paths.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != sources[key]["sha256"]:
            raise ValueError(f"PDF differs from reviewed version: {path}")

    def source_link(key, page):
        url = sources[key]["url"]
        if local_links:
            url = quote(os.path.relpath(paths[key], out.parent)) + f"#page={page}"
        return f'<a href="{url}">{escape(sources[key]["label"])} · PDF p. {page}</a>'

    expected = {
        (claim["id"], ref)
        for group in groups
        for claim in group["claims"]
        for ref in group["references"]
    }
    indexed = {(a["claim"], a["source"]): a for a in assessments}
    if len(indexed) != len(assessments) or set(indexed) != expected:
        raise ValueError(
            "The judgments must cover each claim–source link exactly once."
        )
    summary = defaultdict(Counter)
    for group in groups:
        counts = summary[group["citer"]]
        counts["Groups"] += 1
        counts["Links"] += len(group["references"])
        for claim in group["claims"]:
            statuses = [indexed[claim["id"], k]["status"] for k in group["references"]]
            counts[group_result(statuses)] += 1
            counts["Judgments"] += len(statuses)
    columns = ["Groups", "Links", "Judgments", "All", "Some", "None", "Too vague"]
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>How quota studies cite evidence together</title>",
        "<style>body{max-width:840px;margin:2rem auto;padding:0 1rem;color:#25312b;"
        "font:17px/1.5 system-ui}h1,h2,blockquote{font-family:Georgia,serif}"
        "article{margin:2em 0}blockquote{margin:1rem 0;padding:1rem;background:#eef4ef}"
        "h2{border-top:1px solid #89988e;padding-top:1rem}a{color:#165f4a}"
        "table{border-collapse:collapse;display:block;overflow-x:auto}"
        "th,td{padding:.45rem;border-bottom:1px solid #cad3cd;text-align:right}"
        "th:first-child{text-align:left}li{margin:1em 0}</style>",
        "<main><h1>How quota studies cite evidence together</h1>"
        "<p>These selected passages concern India’s village council quotas. "
        "One sentence can credit several studies for investigating the same "
        "question; another can enlist them as evidence of the same result. "
        "Follow the wording to the cited evidence below.</p>",
        "<h2>Selected citation groups by paper</h2>"
        "<p>A link connects one citation occurrence with a source. Judgments count "
        "each link once for each interpretation tested. The last four columns count "
        "interpretations by how many sources support them. None includes insufficient "
        "evidence. These counts describe the selected examples only.</p>"
        "<table><thead><tr><th>Citing paper</th>"
        + "".join(f"<th>{c}</th>" for c in columns)
        + "</tr></thead><tbody>",
    ]
    totals = sum(summary.values(), Counter())
    for key, counts in [*summary.items(), ("total", totals)]:
        name = "Total" if key == "total" else sources[key]["label"]
        parts.append(
            f"<tr><th>{escape(name)}</th>"
            + "".join(f"<td>{counts[c]}</td>" for c in columns)
            + "</tr>"
        )
    parts.append("</tbody></table>")
    for group in groups:
        text = group["passage"]
        if normalized(text) not in page_text(paths[group["citer"]], group["page"]):
            raise ValueError(f"Could not verify citing passage {group['id']}")
        parts.append(
            f'<article><h2>{escape(group["id"].capitalize())}</h2>'
            f"<blockquote>{escape(text)}</blockquote>"
            f'{source_link(group["citer"], group["page"])}'
        )
        for ref, entry in group.get("bibliography", {}).items():
            pdf = paths[group["citer"]]
            if entry["excerpt"] not in page_text(pdf, entry["page"]):
                raise ValueError(f"Bibliography entry differs for {group['id']}, {ref}")
            cite_link = source_link(group["citer"], entry["page"])
            parts.append(f'<p>{cite_link}<br>“{escape(entry["excerpt"])}”</p>')
        for claim in group["claims"]:
            if claim["scope"] not in text:
                raise ValueError(f"Claim excerpt missing from {group['id']}")
            links = [indexed[claim["id"], ref] for ref in group["references"]]
            statuses = [row["status"] for row in links]
            label = group_result(statuses)
            if label != "Too vague":
                label = f"{statuses.count('supports')} of {len(statuses)} support it"
            parts.append(
                f"<h3>{label}</h3>"
                f'<p><b>Words assessed</b> “{escape(claim["scope"])}”</p>'
                f'<p>{escape(claim["reading"])}</p><ul>'
            )
            for row in links:
                key, page = row["source"], row["page"]
                if normalized(row["evidence"]) not in page_text(paths[key], page):
                    raise ValueError(
                        f"Could not verify evidence for {claim['id']}, {key}"
                    )
                parts.append(
                    f"<li>{source_link(key, page)}<br>"
                    f'<b>{escape(row["status"].capitalize())}.</b> '
                    f'“{escape(row["evidence"])}”<br>{escape(row["reason"])}</li>'
                )
            parts.append("</ul>")
            print(f'{claim["id"]}: {label}')
        parts.append("</article>")
    parts.append("</main></html>")
    out.write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_dir", type=Path)
    parser.add_argument("--output", type=Path, default=PILOT / "review.html")
    parser.add_argument("--local-links", action="store_true", help="link to local PDFs")
    parser.add_argument("--anekanta", type=Path, help="verify PDF, work and page joins")
    parser.add_argument(
        "--reviewed", type=Path, help="verify source-checked Anekanta records"
    )
    args = parser.parse_args()
    run(
        args.pdf_dir.resolve(),
        args.output.resolve(),
        args.local_links,
        args.anekanta,
        args.reviewed,
    )
