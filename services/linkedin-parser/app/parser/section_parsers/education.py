import re
import logging

from app.parser.models import EducationEntry

logger = logging.getLogger(__name__)

# Real format:
# Master's in Computer Science & Engineering, Indian Institute of Technology, Madras
# Madras, India Jan 1997 - Jan 2000

DATE_RANGE_PATTERN = re.compile(
    r"(\w{3,9}\s+\d{4})\s*[-–—]\s*(\w{3,9}\s+\d{4}|Present)",
    re.IGNORECASE,
)
YEAR_RANGE_PATTERN = re.compile(r"(\d{4})\s*[-–—]\s*(\d{4}|Present)", re.IGNORECASE)


def parse_education(text: str) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    if not text.strip():
        return entries

    lines = text.split("\n")

    # Find date-range lines to anchor each education entry
    date_line_indices = []
    for i, line in enumerate(lines):
        if DATE_RANGE_PATTERN.search(line) or YEAR_RANGE_PATTERN.search(line):
            date_line_indices.append(i)

    if not date_line_indices:
        # Fallback: block-based
        return _fallback_parse(lines)

    for idx, date_line_idx in enumerate(date_line_indices):
        date_line = lines[date_line_idx].strip()

        # Extract dates
        date_match = DATE_RANGE_PATTERN.search(date_line)
        if not date_match:
            date_match = YEAR_RANGE_PATTERN.search(date_line)
        start_date = date_match.group(1) if date_match else None
        end_date = date_match.group(2) if date_match else None

        # Location is the part before dates on the date line
        location = None
        if date_match:
            loc_part = date_line[:date_match.start()].strip().rstrip(",").strip()
            if loc_part:
                location = loc_part

        # The line(s) above the date line contain degree + school
        # Find the degree/school line
        if idx > 0:
            prev_date_idx = date_line_indices[idx - 1]
            search_start = prev_date_idx + 1
        else:
            search_start = 0

        degree_school_lines = []
        for t in range(search_start, date_line_idx):
            stripped = lines[t].strip()
            if stripped:
                degree_school_lines.append(stripped)

        # Parse "Master's in Computer Science & Engineering, Indian Institute of Technology, Madras"
        degree, field, school = _parse_degree_school(" ".join(degree_school_lines))

        entries.append(EducationEntry(
            school=school,
            degree=degree,
            field=field,
            location=location,
            start_date=start_date,
            end_date=end_date,
        ))

    logger.info(f"Parsed {len(entries)} education entries")
    return entries


def _parse_degree_school(text: str) -> tuple[str | None, str | None, str]:
    """Parse 'Master's in Computer Science & Engineering, Indian Institute of Technology, Madras'"""
    if not text:
        return (None, None, "Unknown School")

    # Pattern: "Degree in Field, School, Campus" or "Degree, School"
    # Try to match "X's in Y, School" pattern
    match = re.match(
        r"((?:Master'?s?|Bachelor'?s?|Doctor\w*|PhD|MBA|B\.?\s*S\.?|M\.?\s*S\.?|B\.?\s*A\.?|M\.?\s*A\.?|Associate'?s?)"
        r"(?:\s+(?:in|of)\s+[\w\s&]+)?)"
        r",\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        degree_part = match.group(1).strip()
        school = match.group(2).strip()

        # Split degree into degree + field
        field_match = re.match(r"(.+?)\s+(?:in|of)\s+(.+)", degree_part, re.IGNORECASE)
        if field_match:
            degree = field_match.group(1).strip()
            field = field_match.group(2).strip()
        else:
            degree = degree_part
            field = None

        return (degree, field, school)

    # Fallback: first part is school
    parts = [p.strip() for p in text.split(",")]
    if len(parts) >= 2:
        return (parts[0], None, ", ".join(parts[1:]))
    return (None, None, text)


def _fallback_parse(lines: list[str]) -> list[EducationEntry]:
    entries = []
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(stripped)
    if current:
        blocks.append(current)

    for block in blocks:
        if block:
            entries.append(EducationEntry(school=block[0]))
    return entries
