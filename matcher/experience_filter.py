import re


# ============================================================
# STRICT EXPERIENCE FILTER
#
# ALLOWED:
# - Fresher / entry-level wording
# - Internship / trainee (word-boundary match)
# - 0-1 years, 0-2 years
# - Up to 1 year stated alone
# - Experience not stated
#
# REJECT:
# - 1-2 years, 2 years, 2+ years, 3+ years, etc.
# ============================================================

MAX_ALLOWED_EXPERIENCE_YEARS = 2


# ============================================================
# FRESHER KEYWORDS
# ============================================================

FRESHER_KEYWORDS = [
    "fresher",
    "freshers",
    "entry level",
    "entry-level",
    "new graduate",
    "recent graduate",
    "fresh graduate",
    "no experience required",
    "no prior experience required",
]


# ============================================================
# INTERNSHIP PATTERNS (word boundaries)
# ============================================================

INTERNSHIP_PATTERNS = [
    r"\binternship\b",
    r"\binterns\b",
    r"\bintern\b",
    r"\btrainee\b",
    r"\bapprentice\b",
    r"\bapprenticeship\b",
    r"\bpaid internship\b",
    r"\bunpaid internship\b",
    r"\bsummer intern\b",
    r"\bstudent intern\b",
    r"\bgraduate intern\b",
]


# ============================================================
# FRESHER CHECK
# ============================================================

def contains_fresher_keyword(text):

    text = text.lower()

    return any(
        keyword in text
        for keyword in FRESHER_KEYWORDS
    )


# ============================================================
# INTERNSHIP CHECK
# ============================================================

def contains_internship_keyword(text):

    text = text.lower()

    return any(
        re.search(pattern, text)
        for pattern in INTERNSHIP_PATTERNS
    )


# ============================================================
# EXPERIENCE RANGE CHECK
# ============================================================

def extract_experience_ranges(text):

    text = text.lower()

    pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(?:-|–|—|to)\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:years?|yrs?)\b"
    )

    matches = re.findall(
        pattern,
        text
    )

    return [
        (
            float(min_years),
            float(max_years)
        )
        for min_years, max_years in matches
    ]


# ============================================================
# MINIMUM / PLUS EXPERIENCE
# ============================================================

def extract_minimum_experience(text):

    text = text.lower()

    patterns = [

        r"\b(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\b",

        r"\bminimum\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",

        r"\bat\s+least\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",

        r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+of\s+experience\b",

        r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+experience\b",
    ]

    values = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            try:
                values.append(
                    float(match)
                )

            except ValueError:
                pass

    return values


# ============================================================
# MAIN EXPERIENCE CHECK
# ============================================================

def check_experience(job_description):

    if not job_description:

        return (
            False,
            "Rejected: Experience requirement missing"
        )

    text = job_description.lower()

    # ========================================================
    # 1. INTERNSHIP
    # ========================================================

    if contains_internship_keyword(text):

        return (
            True,
            "Internship / Trainee opportunity"
        )

    # ========================================================
    # 2. FRESHER
    # ========================================================

    if contains_fresher_keyword(text):

        return (
            True,
            "Fresher / Entry-level job"
        )

    # ========================================================
    # 3. EXPERIENCE RANGES
    # ========================================================

    ranges = extract_experience_ranges(text)

    if ranges:

        for min_years, max_years in ranges:

            if (
                min_years == 0
                and max_years <= MAX_ALLOWED_EXPERIENCE_YEARS
            ):

                return (
                    True,
                    f"Experience requirement: "
                    f"{min_years:g}-{max_years:g} years"
                )

            return (
                False,
                f"Rejected: Experience requirement "
                f"{min_years:g}-{max_years:g} years"
            )

    # ========================================================
    # 4. MINIMUM / PLUS / EXACT EXPERIENCE
    #
    # STRICT RULE:
    # Reject any standalone mention of >= 1 year
    # Only 0-1 and 0-2 RANGES are acceptable (checked above)
    # ========================================================

    minimum_values = extract_minimum_experience(text)

    if minimum_values:

        lowest = min(
            minimum_values
        )

        if lowest >= 1:

            return (
                False,
                f"Rejected: Requires "
                f"{lowest:g}+ years experience"
            )

        # Only 0 years standalone is acceptable

        return (
            True,
            f"Experience requirement: "
            f"{lowest:g} years (acceptable)"
        )

    # ========================================================
    # 5. EXPLICIT 0 YEARS
    # ========================================================

    if re.search(
        r"\b0\s*(?:years?|yrs?)\b",
        text
    ):

        return (
            True,
            "0 years experience"
        )

    # ========================================================
    # 6. EXPLICIT 1 YEAR - REJECTED
    #
    # Standalone "1 year" means minimum 1 year required.
    # User wants only 0-start ranges.
    # ========================================================

    if re.search(
        r"\b1\s*(?:year|yr)\b",
        text
    ):

        return (
            False,
            "Rejected: Requires 1 year experience"
        )

    # ========================================================
    # 7. UNKNOWN / UNSTATED EXPERIENCE
    # ========================================================

    return (
        True,
        "Experience requirement not stated (allowed through)"
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_descriptions = [

        # PASS
        "Fresh graduates are encouraged to apply.",
        "This is an entry-level Data Analyst position.",
        "Candidates should have 0-1 years of experience.",
        "Candidates should have 0-2 years of experience.",
        "Requires 1 year of experience in SQL.",
        "Paid internship opportunity for Data Analysts.",
        "Unpaid internship opportunity.",
        "Data Analyst Intern position.",
        "Data Analyst with SQL and Power BI skills.",

        # REJECT
        "Requires 1-2 years of experience.",
        "Requires exactly 2 years of experience.",
        "Requires 2 years of experience.",
        "Requires 2+ years of relevant experience.",
        "Candidates should have 2-5 years of experience.",
        "Candidates should have 3-5 years of experience.",
        "Requires minimum 3 years of experience.",
        "Requires 4 years of experience.",
        "Looking for an experienced Data Analyst.",

        # FALSE POSITIVE GUARDS
        "International Data Analyst role with SQL skills.",
        "Internal Audit reporting team needs an analyst.",
    ]


    print(
        "\n"
        "=========================================="
    )

    print(
        "STRICT EXPERIENCE FILTER TEST"
    )

    print(
        "=========================================="
    )


    for description in test_descriptions:

        passed, reason = check_experience(
            description
        )

        status = (
            "PASS"
            if passed
            else "REJECT"
        )

        print(
            f"{status:7} | {reason}"
        )


    print(
        "=========================================="
    )
