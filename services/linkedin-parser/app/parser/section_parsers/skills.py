import re
import logging

from app.parser.models import SkillCategory, LanguageEntry

logger = logging.getLogger(__name__)

# Real LinkedIn PDF Skills format:
# Top Skills :
# Virtual Machines, Transmission Control Protocol (TCP), Routing Protocols
# Languages :
# English (Full Professional)
# Hard Skills :
# Machine Learning
# Data Science & Machine Learning :
# Natural Language Processing, Computer Vision, ...
# Soft Skills :
# Leadership, Initiative, ...

CATEGORY_PATTERN = re.compile(r"^(.+?)\s*:\s*$")


def parse_skills(text: str) -> tuple[list[str], list[SkillCategory], list[LanguageEntry]]:
    """Parse skills section. Returns (flat_skills, skill_categories, languages)."""
    if not text.strip():
        return ([], [], [])

    lines = text.split("\n")
    categories: list[SkillCategory] = []
    languages: list[LanguageEntry] = []
    all_skills: list[str] = []

    current_category: str | None = None
    current_skills: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this is a category header like "Top Skills :"
        cat_match = CATEGORY_PATTERN.match(stripped)
        if cat_match:
            # Save previous category
            if current_category and current_skills:
                if current_category.lower().startswith("language"):
                    # Parse language entries
                    for s in current_skills:
                        lang = _parse_language(s)
                        if lang:
                            languages.append(lang)
                else:
                    categories.append(SkillCategory(
                        category=current_category,
                        skills=current_skills,
                    ))
                    all_skills.extend(current_skills)

            current_category = cat_match.group(1).strip()
            current_skills = []
            continue

        # This is skill content — may be comma-separated on one line
        # or may span multiple lines
        skills_on_line = _extract_skills_from_line(stripped)
        current_skills.extend(skills_on_line)

    # Don't forget the last category
    if current_category and current_skills:
        if current_category.lower().startswith("language"):
            for s in current_skills:
                lang = _parse_language(s)
                if lang:
                    languages.append(lang)
        else:
            categories.append(SkillCategory(
                category=current_category,
                skills=current_skills,
            ))
            all_skills.extend(current_skills)

    # If no categories detected, treat all as flat skills
    if not categories and not languages:
        for line in lines:
            stripped = line.strip()
            if stripped:
                all_skills.extend(_extract_skills_from_line(stripped))

    logger.info(f"Parsed {len(all_skills)} skills in {len(categories)} categories, {len(languages)} languages")
    return (all_skills, categories, languages)


def _extract_skills_from_line(line: str) -> list[str]:
    """Split comma-separated skills from a line."""
    skills = []
    # Remove endorsement counts
    cleaned = re.sub(r"\s*·\s*\d+\s*(?:endorsements?)?", "", line, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*\(\d+\s*(?:endorsements?)?\)", "", cleaned, flags=re.IGNORECASE)

    if "," in cleaned:
        for s in cleaned.split(","):
            s = s.strip()
            if s and len(s) < 150 and not s.isdigit():
                skills.append(s)
    else:
        cleaned = cleaned.strip()
        if cleaned and len(cleaned) < 150 and not cleaned.isdigit():
            skills.append(cleaned)

    return skills


def _parse_language(text: str) -> LanguageEntry | None:
    """Parse 'English (Full Professional)' into LanguageEntry."""
    text = text.strip()
    if not text:
        return None

    match = re.match(r"(.+?)\s*\((.+?)\)", text)
    if match:
        return LanguageEntry(language=match.group(1).strip(), proficiency=match.group(2).strip())

    # Try "Language · Proficiency" pattern
    match = re.match(r"(.+?)\s*·\s*(.+)", text)
    if match:
        return LanguageEntry(language=match.group(1).strip(), proficiency=match.group(2).strip())

    return LanguageEntry(language=text)
