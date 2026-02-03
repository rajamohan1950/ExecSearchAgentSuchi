import re

from app.parser.models import (
    CertificationEntry,
    LanguageEntry,
    VolunteerEntry,
    PublicationEntry,
    PatentEntry,
    AwardEntry,
    ProjectEntry,
    CourseEntry,
)


def parse_certifications(text: str) -> list[CertificationEntry]:
    entries = []
    blocks = _split_blocks(text)
    for block in blocks:
        name = block[0]
        authority = None
        date = None
        for line in block[1:]:
            if re.search(r"\d{4}", line):
                date = line.strip()
            elif not authority:
                authority = line.strip()
        entries.append(CertificationEntry(name=name, authority=authority, date=date))
    return entries


def parse_languages(text: str) -> list[LanguageEntry]:
    entries = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # Pattern: "English (Native or Bilingual)" or "Spanish · Professional"
        match = re.match(r"(.+?)\s*[·(]\s*(.+?)\s*\)?$", stripped)
        if match:
            entries.append(LanguageEntry(language=match.group(1).strip(), proficiency=match.group(2).strip()))
        else:
            entries.append(LanguageEntry(language=stripped))
    return entries


def parse_volunteer(text: str) -> list[VolunteerEntry]:
    entries = []
    blocks = _split_blocks(text)
    for block in blocks:
        role = block[0]
        org = block[1] if len(block) > 1 else None
        desc_lines = block[2:] if len(block) > 2 else []
        entries.append(
            VolunteerEntry(
                role=role,
                organization=org,
                description="\n".join(desc_lines) if desc_lines else None,
            )
        )
    return entries


def parse_publications(text: str) -> list[PublicationEntry]:
    entries = []
    blocks = _split_blocks(text)
    for block in blocks:
        title = block[0]
        publisher = block[1] if len(block) > 1 else None
        desc_lines = block[2:] if len(block) > 2 else []
        entries.append(
            PublicationEntry(
                title=title,
                publisher=publisher,
                description="\n".join(desc_lines) if desc_lines else None,
            )
        )
    return entries


def parse_patents(text: str) -> list[PatentEntry]:
    entries = []
    blocks = _split_blocks(text)
    for block in blocks:
        title = block[0]
        patent_number = None
        date = None
        desc_lines = []
        for line in block[1:]:
            if re.search(r"(?:patent|pat\.?\s*(?:no|#|number))\s*[:.]?\s*\w+", line, re.IGNORECASE):
                patent_number = line.strip()
            elif re.search(r"\d{4}", line) and not date:
                date = line.strip()
            else:
                desc_lines.append(line)
        entries.append(
            PatentEntry(
                title=title,
                patent_number=patent_number,
                date=date,
                description="\n".join(desc_lines) if desc_lines else None,
            )
        )
    return entries


def parse_awards(text: str) -> list[AwardEntry]:
    entries = []
    blocks = _split_blocks(text)
    for block in blocks:
        title = block[0]
        issuer = None
        date = None
        desc_lines = []
        for line in block[1:]:
            if re.search(r"\d{4}", line) and not date:
                date = line.strip()
            elif not issuer:
                issuer = line.strip()
            else:
                desc_lines.append(line)
        entries.append(
            AwardEntry(
                title=title,
                issuer=issuer,
                date=date,
                description="\n".join(desc_lines) if desc_lines else None,
            )
        )
    return entries


def parse_projects(text: str) -> list[ProjectEntry]:
    entries = []
    blocks = _split_blocks(text)
    for block in blocks:
        name = block[0]
        desc_lines = block[1:] if len(block) > 1 else []
        entries.append(
            ProjectEntry(
                name=name,
                description="\n".join(desc_lines) if desc_lines else None,
            )
        )
    return entries


def parse_courses(text: str) -> list[CourseEntry]:
    entries = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            entries.append(CourseEntry(name=stripped))
    return entries


def _split_blocks(text: str) -> list[list[str]]:
    lines = text.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(stripped)
    if current:
        blocks.append(current)
    return blocks
