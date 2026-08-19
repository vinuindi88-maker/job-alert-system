import re

TARGET_ROLE_PATTERNS = [
    r"\bdata\s+analyst\b",
    r"\bdata\s+analytics?\b",
    r"\bdata\s+scientist\b",
    r"\bdata\s+engineer\b",
    r"\bbusiness\s+analyst\b",
    r"\bbusiness\s+intelligence\b",
    r"\bbi\s+analyst\b",
    r"\bbi\s+developer\b",
    r"\banalytics?\s+analyst\b",
    r"\banalytics?\s+engineer\b",
    r"\banalytics?\s+scientist\b",
    r"\bproduct\s+analyst\b",
    r"\bproduct\s+analytics?\b",
    r"\bmarketing\s+analyst\b",
    r"\bmarketing\s+analytics?\b",
    r"\boperations?\s+analyst\b",
    r"\boperations?\s+analytics?\b",
    r"\bdecision\s+scientist\b",
    r"\breporting\s+analyst\b",
    r"\binsights?\s+analyst\b",
]

DATA_SKILLS = [
    "sql",
    "python",
    "pandas",
    "numpy",
    "excel",
    "power bi",
    "tableau",
    "looker",
    "qlik",
    "statistics",
    "data visualization",
    "data analysis",
    "data analytics",
    "business intelligence",
    "machine learning",
    "data modeling",
    "etl",
    "data warehouse",
]

EXCLUDED_ROLE_PATTERNS = [
    r"\brecruiter\b",
    r"\brecruitment\b",
    r"\bhuman\s+resources\b",
    r"\bsoftware\s+engineer\b",
    r"\bsoftware\s+developer\b",
    r"\bfrontend\b",
    r"\bfront[-\s]?end\b",
    r"\bbackend\b",
    r"\bback[-\s]?end\b",
    r"\bfull[-\s]?stack\b",
    r"\bdevops\b",
    r"\bsite\s+reliability\b",
    r"\bsre\b",
    r"\bnetwork\s+engineer\b",
    r"\bsystem\s+administrator\b",
    r"\bsystems?\s+administrator\b",
    r"\btechnical\s+support\b",
    r"\bcustomer\s+support\b",
    r"\bsales\s+representative\b",
    r"\bsales\s+manager\b",
    r"\baccount\s+executive\b",
    r"\baccountant\b",
    r"\blawyer\b",
    r"\bdesigner\b",
    r"\bproject\s+manager\b",
    r"\bprogram\s+manager\b",
    r"\bproduct\s+manager\b",
    r"\bmarketing\s+manager\b",
    r"\boperations\s+manager\b",
    r"\bdirector\b",
    r"\bvice\s+president\b",
    r"\bvp\b",
    r"\bchief\b",
]

SENIORITY_EXCLUSIONS = [
    r"\bsenior\b",
    r"\bsr\.\b",
    r"\bsr\b",
    r"\blead\b",
    r"\bprincipal\b",
    r"\bstaff\b",
    r"\bmanager\b",
    r"\bdirector\b",
    r"\bhead\s+of\b",
    r"\bvp\b",
    r"\bvice\s+president\b",
]

def normalize(text):
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9+#.\-/ ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def is_target_role(title):
    title = normalize(title)
    if not title:
        return False

    for pattern in SENIORITY_EXCLUSIONS:
        if re.search(pattern, title):
            return False

    for pattern in EXCLUDED_ROLE_PATTERNS:
        if re.search(pattern, title):
            return False

    return any(
        re.search(pattern, title)
        for pattern in TARGET_ROLE_PATTERNS
    )

def calculate_role_score(title, description=""):
    title = normalize(title)
    description = normalize(description)
    score = 10 if is_target_role(title) else 0

    for skill in DATA_SKILLS:
        if skill in title:
            score += 2
        elif skill in description:
            score += 1

    return score

def match_keyword(title, description=""):
    title = normalize(title)
    description = normalize(description)

    if not title:
        return False, 0, "Missing job title"

    for pattern in SENIORITY_EXCLUSIONS:
        if re.search(pattern, title):
            return False, 0, "Senior/Lead/Manager level role"

    for pattern in EXCLUDED_ROLE_PATTERNS:
        if re.search(pattern, title):
            return False, 0, "Not a relevant Data/Analytics role"

    if is_target_role(title):
        return True, calculate_role_score(title, description), "Relevant Data/Analytics role"

    skill_hits = sum(
        2 if skill in title else 1
        for skill in DATA_SKILLS
        if skill in title or skill in description
    )

    if skill_hits >= 4:
        return True, skill_hits, "Data/Analytics skills indicate relevant role"

    return False, 0, "Not a relevant Data/Analytics role"

def keyword_match(title, description=""):
    return match_keyword(title, description)

def check_keyword_match(title, description=""):
    return match_keyword(title, description)

if __name__ == "__main__":
    tests = [
        "Data Analyst",
        "Junior Data Analyst",
        "Data Analyst Intern",
        "Business Analyst",
        "Analytics Analyst",
        "Data Scientist",
        "Data Engineer",
        "Product Analyst",
        "Senior Data Analyst",
        "Lead Data Analyst",
        "Data Analytics Manager",
        "Java Developer",
        "Recruiter",
    ]

    print("==========================================")
    print("KEYWORD MATCH TEST")
    print("==========================================")

    for title in tests:
        passed, score, reason = match_keyword(title)
        print(
            f"{'PASS' if passed else 'REJECT':7} | "
            f"{score:3} | {title:35} | {reason}"
        )
