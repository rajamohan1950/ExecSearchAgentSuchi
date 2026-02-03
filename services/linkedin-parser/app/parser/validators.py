import re
import logging

from app.parser.models import ParsedProfile

logger = logging.getLogger(__name__)

# Real LinkedIn PDF header format:
# Email: jabbalarajamohan@gmail.com
# Rajamohan Jabbala
# Mobile Number: +919611125430 (Mobile)
# Director of AI & Platform Engineering | GenAI, Cloud, ML | IIT Web Link: https://www.alphaforgeai.com/
# Madras LinkedIn: https://www.linkedin.com/in/rajamohanja
# bbala
# Address: Bengaluru, Karnataka, India

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-\(\)]{7,15}\d")
LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+", re.IGNORECASE)
WEBSITE_PATTERN = re.compile(r"https?://[\w\.\-]+\.\w{2,}[/\w\.\-]*", re.IGNORECASE)

# Known label prefixes in LinkedIn PDF headers
LABEL_PATTERNS = {
    "email": re.compile(r"^(?:Email|E-mail)\s*:\s*(.+)", re.IGNORECASE),
    "phone": re.compile(r"^(?:Mobile\s*(?:Number)?|Phone|Tel)\s*:\s*(.+)", re.IGNORECASE),
    "address": re.compile(r"^Address\s*:\s*(.+)", re.IGNORECASE),
    "linkedin": re.compile(r"LinkedIn\s*:\s*(https?://[\S]+)", re.IGNORECASE),
    "web_link": re.compile(r"Web\s*Link\s*:\s*(https?://[\S]+)", re.IGNORECASE),
}


def extract_contact_from_header(header: str, profile: ParsedProfile) -> ParsedProfile:
    """Extract name, email, phone, location, LinkedIn URL, headline from header block."""
    lines = header.split("\n")
    non_empty = [l.strip() for l in lines if l.strip()]

    # First pass: extract labeled fields
    consumed_indices: set[int] = set()
    linkedin_parts: list[str] = []

    for i, line in enumerate(non_empty):
        stripped = line.strip()

        # Email: field
        email_label = LABEL_PATTERNS["email"].match(stripped)
        if email_label:
            profile.email = email_label.group(1).strip()
            consumed_indices.add(i)
            continue

        # Phone field
        phone_label = LABEL_PATTERNS["phone"].match(stripped)
        if phone_label:
            phone_text = phone_label.group(1).strip()
            # Clean "(Mobile)" suffix
            phone_text = re.sub(r"\s*\((?:Mobile|Home|Work)\)\s*$", "", phone_text, flags=re.IGNORECASE)
            profile.phone = phone_text.strip()
            consumed_indices.add(i)
            continue

        # Address field
        addr_label = LABEL_PATTERNS["address"].match(stripped)
        if addr_label:
            profile.location = addr_label.group(1).strip()
            consumed_indices.add(i)
            continue

        # LinkedIn URL (may be split across lines due to PDF wrapping)
        linkedin_label = LABEL_PATTERNS["linkedin"].match(stripped)
        if linkedin_label:
            linkedin_parts.append(linkedin_label.group(1))
            consumed_indices.add(i)
            continue

        # Web Link
        web_label = LABEL_PATTERNS["web_link"].match(stripped)
        if web_label:
            profile.website_url = web_label.group(1).strip()
            consumed_indices.add(i)
            continue

        # Inline email detection (email may appear on long lines mixed with other text)
        if not profile.email:
            email_match = EMAIL_PATTERN.search(stripped)
            if email_match:
                profile.email = email_match.group()
                # Only consume the line if it's primarily an email line
                if len(stripped) < 80:
                    consumed_indices.add(i)
                continue

    # Handle LinkedIn URL continuation (split across lines like "rajamohanja\nbbala")
    if linkedin_parts:
        url = linkedin_parts[0]
        profile.linkedin_url = url
    elif not profile.linkedin_url:
        # Search full header for LinkedIn URL
        full_header = " ".join(non_empty)
        match = LINKEDIN_PATTERN.search(full_header)
        if match:
            profile.linkedin_url = match.group()

    # Fallback: look for "www.linkedin.com/in/" on one line and username on next
    if not profile.linkedin_url:
        for i, line in enumerate(non_empty):
            stripped = line.strip()
            if re.search(r"linkedin\.com/in/\s*$", stripped, re.IGNORECASE):
                # URL continues on next line
                if i + 1 < len(non_empty):
                    next_line = non_empty[i + 1].strip()
                    # Next line might be "username (LinkedIn)" or just "username"
                    username = re.sub(r"\s*\(LinkedIn\)\s*$", "", next_line, flags=re.IGNORECASE).strip()
                    if username and len(username) < 40 and " " not in username:
                        base = stripped.rstrip("/").rstrip()
                        profile.linkedin_url = f"https://{base.lstrip('htps:/')}/{username}"
                        consumed_indices.add(i)
                        consumed_indices.add(i + 1)
                break
            # Also match "username (LinkedIn)" pattern
            linkedin_ref = re.match(r"^(\w[\w\-]+)\s*\(LinkedIn\)\s*$", stripped, re.IGNORECASE)
            if linkedin_ref and not profile.linkedin_url:
                profile.linkedin_url = f"https://www.linkedin.com/in/{linkedin_ref.group(1)}"
                consumed_indices.add(i)

    # Extract name: first non-consumed, non-label line that looks like a name
    for i, line in enumerate(non_empty):
        if i in consumed_indices:
            continue
        stripped = line.strip()
        # Skip lines that are clearly not names
        if EMAIL_PATTERN.search(stripped) or WEBSITE_PATTERN.search(stripped):
            continue
        if any(lp.search(stripped) for lp in LABEL_PATTERNS.values()):
            continue
        # A name line: typically 2-5 words, no special chars except spaces
        if re.match(r"^[A-Za-z\s\.\-']{2,60}$", stripped) and len(stripped.split()) <= 5:
            # Strip "Contact" prefix that LinkedIn PDFs sometimes prepend
            name_cleaned = re.sub(r"^Contact\s+", "", stripped, flags=re.IGNORECASE).strip()
            profile.name = name_cleaned
            consumed_indices.add(i)
            break

    # Extract headline: the line with pipe-separated keywords like "Director of AI | GenAI, Cloud"
    for i, line in enumerate(non_empty):
        if i in consumed_indices:
            continue
        stripped = line.strip()
        if "|" in stripped or (len(stripped) > 20 and not stripped.startswith("•")):
            # Likely a headline — clean off any trailing "Web Link: ..." or "LinkedIn: ..."
            cleaned = re.sub(r"\s*Web\s*Link\s*:.*$", "", stripped, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*LinkedIn\s*:.*$", "", cleaned, flags=re.IGNORECASE)
            # Strip leading phone number + (Mobile) pattern
            cleaned = re.sub(r"^\+?\d[\d\s\-\(\)]{7,15}\d\s*\((?:Mobile|Home|Work)\)\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip()
            if cleaned and not EMAIL_PATTERN.search(cleaned) and not any(lp.search(cleaned) for lp in LABEL_PATTERNS.values()):
                profile.headline = cleaned
                consumed_indices.add(i)
                break

    # Fallback location: look for "City, State/Country" pattern
    if not profile.location:
        for i, line in enumerate(non_empty):
            if i in consumed_indices:
                continue
            stripped = line.strip()
            if re.search(r",\s*\w{2,}", stripped) and not EMAIL_PATTERN.search(stripped) and not WEBSITE_PATTERN.search(stripped):
                profile.location = stripped
                break

    # Fallback phone: search all lines
    if not profile.phone:
        phone_match = PHONE_PATTERN.search(header)
        if phone_match:
            candidate = phone_match.group().strip()
            if sum(c.isdigit() for c in candidate) >= 10:
                profile.phone = candidate

    logger.info(f"Extracted contact: name={profile.name}, email={profile.email}, "
                f"phone={profile.phone}, location={profile.location}, "
                f"linkedin={profile.linkedin_url}")
    return profile


def calculate_experience_years(experience: list) -> int | None:
    """Calculate rough total experience years from experience entries."""
    if not experience:
        return None

    from datetime import datetime

    total_months = 0
    for exp in experience:
        start = exp.get("start_date") if isinstance(exp, dict) else getattr(exp, "start_date", None)
        end = exp.get("end_date") if isinstance(exp, dict) else getattr(exp, "end_date", None)

        if not start:
            continue

        try:
            start_dt = _parse_date(start)
            end_dt = _parse_date(end) if end and end.lower() != "present" else datetime.now()
            if start_dt and end_dt:
                months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                total_months += max(0, months)
        except Exception:
            continue

    return total_months // 12 if total_months > 0 else None


def _parse_date(date_str: str) -> "datetime | None":
    from datetime import datetime
    if not date_str:
        return None
    for fmt in ["%b %Y", "%B %Y", "%Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def deduplicate_skills(skills: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        normalized = skill.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            result.append(skill.strip())
    return result
