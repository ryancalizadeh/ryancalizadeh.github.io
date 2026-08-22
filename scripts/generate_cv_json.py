#!/usr/bin/env python3
"""
Generate _data/cv.json from the rendercv-format _data/Ryan_Alizadeh_CV.yaml.

_data/Ryan_Alizadeh_CV.yaml is the single hand-edited source of truth for the
CV. This script projects its rendercv schema (cv.sections is a free-form dict
of arbitrarily-named arrays, with entry shape inferred from field presence)
down into the fixed JSON-Resume-like shape that _data/cv.json / _includes/
cv-template.html expect.

Mapping conventions (see plan for full rationale):
  - cv.location (single string "City, Region, CountryCode") is split on
    commas into basics.location.city/region/countryCode. basics.location
    .address/.postalCode are never populated (not representable).
  - cv.social_networks[].username is expanded into a full profile url via
    NETWORK_URL_TEMPLATES, keyed on lowercased network name. An unmatched
    network gets url: "" and a stderr warning.
  - cv.sections keys are matched case-insensitively against SECTION_DISPATCH
    to decide which cv.json array they feed. An unmatched section name is
    dropped with a stderr warning (no generic bucket -- cv-template.html
    has no generic renderer for arbitrary sections).
  - Several rendercv entry fields are repurposed to fill cv.json fields that
    don't exist in rendercv's schema (e.g. teaching/awards entries reuse the
    "location" field to carry role/awarder). See the per-section convert_*
    functions below for exact field mappings.
  - Fields with no home in cv.json (education/work location & summary,
    teaching/involvement highlights, publication authors, gpa, custom
    connections, etc.) are silently dropped -- this is a deliberate,
    documented lossy projection since cv.json is now a generated artifact.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

NETWORK_URL_TEMPLATES = {
    "github": "https://github.com/{username}",
    "linkedin": "https://www.linkedin.com/in/{username}",
    "twitter": "https://twitter.com/{username}",
    "x": "https://x.com/{username}",
    "orcid": "https://orcid.org/{username}",
    "google scholar": "https://scholar.google.com/citations?user={username}",
}

CV_JSON_KEYS = [
    "work", "education", "skills", "languages", "interests", "references",
    "publications", "presentations", "teaching", "portfolio", "involvement",
    "awards",
]

SECTION_DISPATCH = {
    "education": "education",
    "experience": "work",
    "work": "work",
    "teaching": "teaching",
    "involvement": "involvement",
    "service": "involvement",
    "awards": "awards",
    "honors": "awards",
    "publications": "publications",
    "presentations": "presentations",
    "talks": "presentations",
    "skills": "skills",
    "languages": "languages",
    "interests": "interests",
    "references": "references",
    "portfolio": "portfolio",
    "projects": "portfolio",
}


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def convert_basics(cv: dict) -> dict:
    basics = {
        "name": cv.get("name") or "",
        "email": cv.get("email") or "",
        "phone": cv.get("phone") or "",
        "website": cv.get("website") or "",
        "summary": cv.get("headline") or "",
        "location": {
            "address": "",
            "postalCode": "",
            "city": "",
            "countryCode": "",
            "region": "",
        },
        "profiles": [],
    }

    location = cv.get("location")
    if location:
        parts = [p.strip() for p in location.split(",") if p.strip()]
        if len(parts) >= 3:
            basics["location"]["city"] = parts[0]
            basics["location"]["region"] = parts[1]
            basics["location"]["countryCode"] = parts[2]
        elif len(parts) == 2:
            basics["location"]["city"] = parts[0]
            basics["location"]["region"] = parts[1]
        elif len(parts) == 1:
            basics["location"]["city"] = parts[0]

    for entry in cv.get("social_networks") or []:
        network = entry.get("network") or ""
        username = entry.get("username") or ""
        template = NETWORK_URL_TEMPLATES.get(network.strip().lower())
        if template is None:
            print(
                f"WARNING: no URL template for network '{network}' "
                f"(username '{username}') -- url left blank",
                file=sys.stderr,
            )
            url = ""
        else:
            url = template.format(username=username)
        basics["profiles"].append(
            {"network": network, "username": username, "url": url}
        )

    return basics


def _date_str(value) -> str:
    return "" if value is None else str(value)


def convert_education_section(entries: list) -> list:
    return [
        {
            "institution": e.get("institution") or "",
            "area": e.get("area") or "",
            "studyType": e.get("degree") or "",
            "startDate": _date_str(e.get("start_date")),
            "endDate": _date_str(e.get("end_date")),
            "gpa": None,
            "courses": e.get("highlights") or [],
        }
        for e in entries
    ]


def convert_work_section(entries: list) -> list:
    return [
        {
            "company": e.get("company") or "",
            "position": e.get("position") or "",
            "website": "",
            "startDate": _date_str(e.get("start_date")),
            "endDate": _date_str(e.get("end_date")),
            "summary": e.get("summary") or "",
            "highlights": e.get("highlights") or [],
        }
        for e in entries
    ]


def convert_teaching_section(entries: list) -> list:
    return [
        {
            "institution": e.get("company") or "",
            "course": e.get("position") or "",
            "role": e.get("location") or "",
            "date": _date_str(e.get("start_date")),
            "startDate": _date_str(e.get("start_date")),
            "endDate": _date_str(e.get("end_date")),
            "description": e.get("summary") or "",
        }
        for e in entries
    ]


def convert_involvement_section(entries: list) -> list:
    return [
        {
            "organization": e.get("company") or "",
            "role": e.get("position") or "",
            "date": _date_str(e.get("start_date")),
            "startDate": _date_str(e.get("start_date")),
            "endDate": _date_str(e.get("end_date")),
            "description": e.get("summary") or "",
        }
        for e in entries
    ]


def convert_awards_section(entries: list) -> list:
    return [
        {
            "title": e.get("name") or "",
            "date": _date_str(e.get("date")),
            "awarder": e.get("location") or "",
            "summary": e.get("summary") or "",
        }
        for e in entries
    ]


def convert_publications_section(entries: list) -> list:
    result = []
    for e in entries:
        url = e.get("url") or ""
        if not url and e.get("doi"):
            url = f"https://doi.org/{e['doi']}"
        result.append(
            {
                "name": e.get("title") or "",
                "publisher": e.get("journal") or "",
                "releaseDate": _date_str(e.get("date")),
                "website": url,
                "summary": e.get("summary") or "",
            }
        )
    return result


def convert_presentations_section(entries: list) -> list:
    return [
        {
            "name": e.get("name") or "",
            "date": _date_str(e.get("date")),
            "event": e.get("location") or "",
            "location": "",
            "description": e.get("summary") or "",
        }
        for e in entries
    ]


def convert_skills_section(entries: list) -> list:
    return [
        {
            "name": e.get("label") or "",
            "keywords": [
                s.strip() for s in (e.get("details") or "").split(",") if s.strip()
            ],
        }
        for e in entries
    ]


def convert_languages_section(entries: list) -> list:
    return [
        {"language": e.get("label") or "", "fluency": e.get("details") or ""}
        for e in entries
    ]


def convert_interests_section(entries: list) -> list:
    return [
        {
            "name": e.get("label") or "",
            "keywords": [
                s.strip() for s in (e.get("details") or "").split(",") if s.strip()
            ],
        }
        for e in entries
    ]


def convert_references_section(entries: list) -> list:
    return [
        {"name": e.get("name") or "", "reference": e.get("summary") or ""}
        for e in entries
    ]


def convert_portfolio_section(entries: list) -> list:
    return [
        {
            "name": e.get("name") or "",
            "date": _date_str(e.get("date")),
            "category": "",
            "description": e.get("summary") or "",
            "url": "",
        }
        for e in entries
    ]


SECTION_CONVERTERS = {
    "education": convert_education_section,
    "work": convert_work_section,
    "teaching": convert_teaching_section,
    "involvement": convert_involvement_section,
    "awards": convert_awards_section,
    "publications": convert_publications_section,
    "presentations": convert_presentations_section,
    "skills": convert_skills_section,
    "languages": convert_languages_section,
    "interests": convert_interests_section,
    "references": convert_references_section,
    "portfolio": convert_portfolio_section,
}


def build_cv_json(yaml_doc: dict) -> dict:
    cv = yaml_doc.get("cv") or {}
    result = {"basics": convert_basics(cv)}
    for key in CV_JSON_KEYS:
        result[key] = []

    for section_name, entries in (cv.get("sections") or {}).items():
        key = SECTION_DISPATCH.get(section_name.strip().lower())
        if key is None:
            print(
                f"WARNING: YAML section '{section_name}' has no cv.json "
                "mapping -- skipped. Add it to SECTION_DISPATCH in "
                "generate_cv_json.py if it should appear on /cv/.",
                file=sys.stderr,
            )
            continue
        result[key] = SECTION_CONVERTERS[key](entries or [])

    return result


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(repo_root / "_data" / "Ryan_Alizadeh_CV.yaml"),
        help="Path to the rendercv YAML source of truth",
    )
    parser.add_argument(
        "--output",
        default=str(repo_root / "_data" / "cv.json"),
        help="Path to write the generated cv.json",
    )
    args = parser.parse_args()

    yaml_doc = load_yaml(Path(args.input))
    cv_json = build_cv_json(yaml_doc)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(cv_json, f, indent=2)
        f.write("\n")

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
