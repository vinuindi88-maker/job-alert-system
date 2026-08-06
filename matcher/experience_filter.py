import re


# ============================================================
# EXPERIENCE FILTER
# Accept jobs suitable for 0–2 years experience
# ============================================================

MAX_ALLOWED_EXPERIENCE = 2


FRESHER_KEYWORDS = [
    "fresher",
    "freshers",
    "entry level",
    "entry-level",
    "graduate",
    "new graduate",
    "recent graduate",
    "fresh graduate",
    "no experience required",
    "no prior experience required",
    "0 years experience",
    "0 year experience",
]


def contains_fresher_keyword(text):
    """Detect explicit fresher / graduate opportunities."""

    text = text.lower()

    return any(
        keyword in text
        for keyword in FRESHER_KEYWORDS
    )


def extract_experience_ranges(text):
    """
    Extract experience requirements from job description.

    Examples detected:
    0-2 years
    1 - 2 years
    2-4 years
    3 to 5 years
    """

    text = text.lower()

    pattern = (
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:-|–|—|to)\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:years?|yrs?)"
    )

    matches = re.findall(pattern, text)

    return [
        (float(min_years), float(max_years))
        for min_years, max_years in matches
    ]


def extract_minimum_experience(text):
    """
    Detect requirements such as:

    1+ years
    2+ years
    minimum 2 years
    at least 2 years
    3 years of experience
    """

    text = text.lower()

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)",
        r"minimum\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"at\s+least\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"minimum\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+of\s+(?:relevant\s+)?experience",
    ]

    values = []

    for pattern in patterns:

        matches = re.findall(pattern, text)

        for match in matches:

            try:
                values.append(float(match))
            except ValueError:
                pass

    return values


def check_experience(job_description):
    """
    Main experience decision.

    Returns:

    True  -> suitable for 0–2 years
    False -> requires more than 2 years
    """

    if not job_description:
        return True, "Experience not specified"

    text = job_description.lower()

    # --------------------------------------------------------
    # 1. Explicit fresher wording
    # --------------------------------------------------------

    if contains_fresher_keyword(text):

        return True, "Fresher / Entry-level job"

    # --------------------------------------------------------
    # 2. Experience ranges
    # --------------------------------------------------------

    ranges = extract_experience_ranges(text)

    if ranges:

        for min_years, max_years in ranges:

            # Candidate can enter if minimum requirement <= 2
            if min_years <= MAX_ALLOWED_EXPERIENCE:
                return (
                    True,
                    f"Experience requirement: {min_years:g}-{max_years:g} years"
                )

        return False, "Experience requirement exceeds 2 years"

    # --------------------------------------------------------
    # 3. Minimum experience requirements
    # --------------------------------------------------------

    minimum_values = extract_minimum_experience(text)

    if minimum_values:

        minimum_required = min(minimum_values)

        if minimum_required <= MAX_ALLOWED_EXPERIENCE:

            return (
                True,
                f"Minimum experience: {minimum_required:g} years"
            )

        return (
            False,
            f"Requires minimum {minimum_required:g} years"
        )

    # --------------------------------------------------------
    # 4. Experience not clearly specified
    # --------------------------------------------------------

    return True, "Experience requirement not clearly specified"


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_descriptions = [

        "Fresh graduates are encouraged to apply.",

        "This is an entry-level Data Analyst position.",

        "Candidates should have 0-2 years of experience.",

        "Requires 1-2 years of experience in SQL.",

        "Minimum 2 years of experience required.",

        "Requires 2+ years of relevant experience.",

        "Requires 3+ years of experience.",

        "Candidates should have 3-5 years of experience.",

        "Looking for a Data Analyst with SQL and Power BI skills.",
    ]

    print("\nEXPERIENCE FILTER TEST\n")

    for description in test_descriptions:

        passed, reason = check_experience(description)

        status = "PASS" if passed else "REJECT"

        print(f"{status:7} | {reason}")