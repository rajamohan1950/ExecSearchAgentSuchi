import logging

from app.parser.models import ParsedProfile
from app.parser.text_extractor import extract_text
from app.parser.section_detector import detect_sections
from app.parser.section_parsers.experience import parse_experience
from app.parser.section_parsers.education import parse_education
from app.parser.section_parsers.skills import parse_skills
from app.parser.section_parsers.generic import (
    parse_certifications,
    parse_languages,
    parse_volunteer,
    parse_publications,
    parse_patents,
    parse_awards,
    parse_projects,
    parse_courses,
)
from app.parser.validators import (
    extract_contact_from_header,
    deduplicate_skills,
    calculate_experience_years,
)

logger = logging.getLogger(__name__)


def parse_linkedin_pdf(pdf_bytes: bytes) -> ParsedProfile:
    # Step 1: Extract raw text
    raw_text = extract_text(pdf_bytes)
    logger.info(f"Extracted {len(raw_text)} characters from PDF")

    # Step 2: Detect sections
    sections = detect_sections(raw_text)
    logger.info(f"Detected sections: {list(sections.keys())}")

    # Step 3: Build profile from sections
    profile = ParsedProfile(raw_text=raw_text)

    # Parse header for contact info (name, email, phone, location, headline, linkedin_url)
    if "header" in sections:
        profile = extract_contact_from_header(sections["header"], profile)

    # Summary
    if "summary" in sections:
        profile.summary = sections["summary"]

    # Experience
    if "experience" in sections:
        profile.experience = parse_experience(sections["experience"])

    # Education
    if "education" in sections:
        profile.education = parse_education(sections["education"])

    # Skills — new parser returns (flat_skills, categories, languages_from_skills)
    if "skills" in sections:
        flat_skills, skill_categories, languages_from_skills = parse_skills(sections["skills"])
        profile.skills = deduplicate_skills(flat_skills)
        profile.skill_categories = skill_categories

        # Merge languages found in skills section
        if languages_from_skills:
            profile.languages.extend(languages_from_skills)

    # Standalone languages section (if separate from skills)
    if "languages" in sections:
        standalone_languages = parse_languages(sections["languages"])
        # Deduplicate with any already parsed from skills
        existing_langs = {l.language.lower() for l in profile.languages}
        for lang in standalone_languages:
            if lang.language.lower() not in existing_langs:
                profile.languages.append(lang)

    if "certifications" in sections:
        profile.certifications = parse_certifications(sections["certifications"])

    if "volunteer" in sections:
        profile.volunteer = parse_volunteer(sections["volunteer"])

    if "patents" in sections:
        profile.patents = parse_patents(sections["patents"])

    if "publications" in sections:
        profile.publications = parse_publications(sections["publications"])

    if "awards" in sections:
        profile.awards = parse_awards(sections["awards"])

    if "projects" in sections:
        profile.projects = parse_projects(sections["projects"])

    if "courses" in sections:
        profile.courses = parse_courses(sections["courses"])

    # Calculate total experience years
    profile.total_experience_years = calculate_experience_years(
        [e.model_dump() for e in profile.experience]
    )

    logger.info(
        f"Parsed profile: name={profile.name}, email={profile.email}, "
        f"phone={profile.phone}, location={profile.location}, "
        f"headline={profile.headline}, linkedin={profile.linkedin_url}, "
        f"experience={len(profile.experience)} ({profile.total_experience_years}y), "
        f"education={len(profile.education)}, "
        f"skills={len(profile.skills)} in {len(profile.skill_categories)} categories, "
        f"languages={len(profile.languages)}"
    )

    return profile
