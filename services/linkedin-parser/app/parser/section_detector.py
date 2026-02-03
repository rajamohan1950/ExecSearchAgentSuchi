import re
import logging

logger = logging.getLogger(__name__)

# LinkedIn PDF section headings - match both ALL CAPS and Title Case
# Order matters: more specific patterns first to avoid false matches
SECTION_PATTERNS = [
    ("summary", r"^(?:SUMMARY|Summary|ABOUT|About)\s*$"),
    ("experience", r"^(?:WORK\s+EXPERIENCE|EXPERIENCE|Work\s+Experience|Experience)\s*$"),
    ("earlier_experience", r"^(?:EARLIER\s+EXPERIENCE|Earlier\s+Experience)\s*$"),
    ("education", r"^(?:EDUCATION|Education)\s*$"),
    ("skills", r"^(?:SKILLS|Skills|TOP\s+SKILLS|Top\s+Skills)\s*$"),
    ("certifications", r"^(?:CERTIFICATIONS?|Certifications?|LICENSES?\s*(?:&|AND)\s*CERTIFICATIONS?)\s*$"),
    ("languages", r"^(?:LANGUAGES?|Languages?)\s*$"),
    ("volunteer", r"^(?:VOLUNTEER\s*(?:EXPERIENCE)?|Volunteer\s*(?:Experience)?|VOLUNTEERING|Volunteering)\s*$"),
    ("patents", r"^(?:PATENTS?|Patents?)\s*$"),
    ("publications", r"^(?:PUBLICATIONS?|Publications?)\s*$"),
    ("awards", r"^(?:AWARDS?|Awards?|HONORS?\s*[-–&]?\s*AWARDS?|Honors?\s*[-–&]?\s*Awards?)\s*$"),
    ("projects", r"^(?:PROJECTS?|Projects?)\s*$"),
    ("courses", r"^(?:COURSES?|Courses?)\s*$"),
    ("recommendations", r"^(?:RECOMMENDATIONS?|Recommendations?)\s*$"),
    ("interests", r"^(?:INTERESTS?|Interests?)\s*$"),
    ("organizations", r"^(?:ORGANIZATIONS?|Organizations?)\s*$"),
]

# Sidebar-only sections (appear in LinkedIn PDF sidebar, interleaved with main content)
SIDEBAR_SECTIONS = {"skills", "languages", "awards", "patents", "publications"}

# Page markers
PAGE_MARKER = re.compile(r"^Page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE)


def detect_sections(text: str) -> dict[str, str]:
    """
    Detects LinkedIn PDF sections and returns dict mapping section name to content.
    Handles:
    - Multi-page PDFs with === PAGE N === markers
    - Two-column layout (sidebar interleaved with main content)
    - "Earlier Experience" merged into experience
    """
    # Remove page markers
    text = re.sub(r"=== PAGE \d+ ===\n?", "", text)
    text = re.sub(r"^Page\s+\d+\s+of\s+\d+\s*$", "", text, flags=re.MULTILINE)

    lines = text.split("\n")
    sections: list[tuple[str, int]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for section_name, pattern in SECTION_PATTERNS:
            if re.match(pattern, stripped):
                sections.append((section_name, i))
                logger.info(f"Detected section '{section_name}' at line {i}: '{stripped}'")
                break

    result: dict[str, str] = {}

    if not sections:
        result["header"] = text.strip()
        return result

    # Check if this is a two-column (sidebar-interleaved) format
    # Indicator: sidebar sections appear BEFORE the main "experience" section
    # and very close to each other (within a few lines)
    is_two_column = _detect_two_column(sections)

    if is_two_column:
        result = _parse_two_column(lines, sections)
    else:
        result = _parse_single_column(lines, sections)

    # Merge "earlier_experience" into "experience"
    if "earlier_experience" in result:
        if "experience" in result:
            result["experience"] = result["experience"] + "\nEarlier Experience\n" + result["earlier_experience"]
        else:
            result["experience"] = result["earlier_experience"]
        del result["earlier_experience"]

    logger.info(f"Detected {len(result)} sections: {list(result.keys())}")
    return result


def _detect_two_column(sections: list[tuple[str, int]]) -> bool:
    """Detect two-column layout: sidebar sections intermixed with summary before experience."""
    exp_line = None
    sidebar_before_exp = 0

    for name, line_num in sections:
        if name == "experience":
            exp_line = line_num
            break

    if exp_line is None:
        return False

    for name, line_num in sections:
        if line_num >= exp_line:
            break
        if name in SIDEBAR_SECTIONS:
            sidebar_before_exp += 1

    # If multiple sidebar sections appear before experience, it's two-column
    return sidebar_before_exp >= 2


def _parse_two_column(lines: list[str], sections: list[tuple[str, int]]) -> dict[str, str]:
    """
    Parse two-column LinkedIn PDF where sidebar is interleaved with main content.

    In these PDFs, the first page has:
    - Left column: Summary text (long lines, wrapped across multiple lines)
    - Right column: Sidebar items like "Top Skills", "Languages", etc. (short lines)

    The PDF text extractor interleaves them line by line:
      Line 9:  Summary              (heading)
      Line 10: Top Skills           (sidebar heading)
      Line 11: VP Engineering...    (summary text - long)
      Line 12: Strategic Planning   (sidebar item - short)
      Line 13: ML platforms...      (summary text - long)
      ...

    Strategy: sidebar headings mark where sidebar items start. Between each pair of
    sidebar headings, odd-numbered lines relative to the heading are sidebar items (short)
    and the remaining lines are main content (summary). We use line length as heuristic:
    sidebar items are typically < 40 chars, summary text is longer.
    """
    result: dict[str, str] = {}

    # Find the "experience" section
    exp_idx = None
    for i, (name, line_num) in enumerate(sections):
        if name == "experience":
            exp_idx = i
            break

    # Header
    header_lines = lines[: sections[0][1]]
    result["header"] = "\n".join(header_lines).strip()

    if exp_idx is None:
        return _parse_single_column(lines, sections)

    pre_exp_sections = sections[:exp_idx]
    exp_line = sections[exp_idx][1]

    # Identify sidebar section headings (everything except "summary")
    sidebar_heading_lines: set[int] = set()
    summary_heading_line = None

    for name, line_num in pre_exp_sections:
        if name == "summary":
            summary_heading_line = line_num
        else:
            sidebar_heading_lines.add(line_num)

    # In two-column format, sidebar content is interleaved with main summary text.
    # Strategy: collect ALL text between section headings, then separate sidebar
    # items from summary text. Sidebar items are short standalone phrases,
    # while summary text forms coherent sentences/paragraphs.
    #
    # We know the sidebar section headings and their expected content type:
    # - "skills": 1-3 word skill names
    # - "languages": "English (Full Professional)" format
    # - "awards": short award names
    # - "patents": short patent titles
    # - "publications": short publication titles

    sidebar_headings_sorted = sorted(sidebar_heading_lines)
    all_sidebar_items: dict[str, list[str]] = {}
    all_sidebar_item_texts: set[str] = set()

    # First pass: identify sidebar items by finding lines immediately after
    # each sidebar heading that match expected content patterns
    for sh_idx, sh_line in enumerate(sidebar_headings_sorted):
        sec_name = None
        for name, line_num in pre_exp_sections:
            if line_num == sh_line:
                sec_name = name
                break
        if not sec_name:
            continue

        # Sidebar items appear interleaved with main content after each heading.
        # Expected counts: Top Skills = 3, Languages = 1-3, Awards/Patents/Pubs = 1-3
        max_items = 3 if sec_name == "skills" else 3
        items: list[str] = []

        for offset in range(1, 12):  # search up to 12 lines after heading
            if len(items) >= max_items:
                break
            ln = sh_line + offset
            if ln >= exp_line:
                break
            if ln in sidebar_heading_lines:
                break
            stripped = lines[ln].strip()
            if not stripped:
                continue

            # Sidebar items characteristics:
            # - Short (< 35 chars for skills, < 45 for others)
            # - No bullets
            # - For skills: 1-4 word phrases, Title Case
            # - For languages: "Language (Proficiency)" pattern
            # - For awards/patents/pubs: short titles
            max_len = 30 if sec_name == "skills" else 45
            is_sidebar = False

            if len(stripped) < max_len and not stripped.startswith("-") and not stripped.startswith("•"):
                if sec_name == "skills":
                    # Skills are 1-4 word Title Case phrases
                    words = stripped.split()
                    if 1 <= len(words) <= 4 and stripped[0].isupper() and not stripped.endswith("."):
                        is_sidebar = True
                elif sec_name == "languages":
                    # "English (Full Professional)" or just "English"
                    if re.match(r"^[A-Z]\w+(?:\s*\([^)]+\))?\s*$", stripped):
                        is_sidebar = True
                else:
                    # Awards, patents, publications: short titles
                    if len(stripped) < 45 and stripped[0].isupper():
                        is_sidebar = True

            if is_sidebar:
                items.append(stripped)
                all_sidebar_item_texts.add(stripped)

        if items:
            all_sidebar_items[sec_name] = items

    # Extract summary: all lines between summary heading and experience,
    # excluding sidebar headings and known sidebar items
    if summary_heading_line is not None:
        summary_lines = []
        for ln in range(summary_heading_line + 1, exp_line):
            if ln in sidebar_heading_lines:
                continue
            stripped = lines[ln].strip()
            if not stripped:
                continue
            if stripped in all_sidebar_item_texts:
                continue
            summary_lines.append(stripped)
        if summary_lines:
            result["summary"] = "\n".join(summary_lines)

    # Add sidebar sections to result
    for sec_name, items in all_sidebar_items.items():
        result[sec_name] = "\n".join(items)

    # Parse sections from "experience" onward normally (single-column)
    post_exp_sections = sections[exp_idx:]
    for idx, (name, line_num) in enumerate(post_exp_sections):
        if idx + 1 < len(post_exp_sections):
            end_line = post_exp_sections[idx + 1][1]
        else:
            end_line = len(lines)
        content = "\n".join(lines[line_num + 1: end_line]).strip()
        if content:
            result[name] = content

    return result


def _parse_single_column(lines: list[str], sections: list[tuple[str, int]]) -> dict[str, str]:
    """Standard single-column section parsing."""
    result: dict[str, str] = {}

    # Header
    header_lines = lines[: sections[0][1]]
    result["header"] = "\n".join(header_lines).strip()

    # Extract content between section headings
    for idx, (name, line_num) in enumerate(sections):
        if idx + 1 < len(sections):
            end_line = sections[idx + 1][1]
        else:
            end_line = len(lines)
        content = "\n".join(lines[line_num + 1: end_line]).strip()
        if content:
            result[name] = content

    return result
