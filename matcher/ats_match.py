# ============================================================
# JOB ALERT SYSTEM - STRICT RESUME / JD MATCHER
# ============================================================

import os
import re

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# SETTINGS
# ============================================================

RESUME_PATH = os.path.join(
    "resume",
    "Vinayak_Indi.pdf"
)
RESUME_TEXT_PATH = "resume_text.txt"

# User requirement: DO NOT lower this.
MIN_MATCH_SCORE = 80

# Prevent 1-2 detected skills from creating fake 100% matches.
MIN_RECOGNIZED_JOB_SKILLS = 3


# ============================================================
# CANONICAL SKILL GROUPS
# ============================================================

SKILL_GROUPS = {

    # Programming
    "python": [
        "python"
    ],

    "sql": [
        "sql"
    ],

    # Python / Data
    "pandas": [
        "pandas"
    ],

    "numpy": [
        "numpy"
    ],

    "matplotlib": [
        "matplotlib"
    ],

    "seaborn": [
        "seaborn"
    ],

    "scikit-learn": [
        "scikit-learn",
        "scikit learn",
        "sklearn"
    ],

    # BI
    "power bi": [
        "power bi",
        "powerbi"
    ],

    "tableau": [
        "tableau"
    ],

    "dax": [
        "dax"
    ],

    "data visualization": [
        "data visualization",
        "data visualisation"
    ],

    "dashboard": [
        "dashboard",
        "dashboards",
        "dashboard development",
        "dashboarding"
    ],

    # Excel
    "excel": [
        "excel",
        "microsoft excel",
        "ms excel"
    ],

    "power query": [
        "power query"
    ],

    "pivot tables": [
        "pivot table",
        "pivot tables"
    ],

    # Databases
    "mysql": [
        "mysql"
    ],

    "sqlite": [
        "sqlite"
    ],

    "sql server": [
        "sql server",
        "microsoft sql server",
        "ms sql server"
    ],

    "postgresql": [
        "postgresql",
        "postgres"
    ],

    # Analytics
    "data analysis": [
        "data analysis",
        "data analytics"
    ],

    "exploratory data analysis": [
        "exploratory data analysis",
        "eda"
    ],

    "data cleaning": [
        "data cleaning",
        "data cleansing"
    ],

    "data validation": [
        "data validation"
    ],

    "data quality": [
        "data quality",
        "data quality assurance"
    ],

    "data transformation": [
        "data transformation",
        "data transformations"
    ],

    # Reporting
    "business intelligence": [
        "business intelligence"
    ],

    "reporting": [
        "reporting"
    ],

    "kpi": [
        "kpi",
        "kpis",
        "key performance indicator",
        "key performance indicators"
    ],

    # Modeling / Warehouse
    "data modeling": [
        "data modeling",
        "data modelling"
    ],

    "star schema": [
        "star schema"
    ],

    "data warehousing": [
        "data warehouse",
        "data warehouses",
        "data warehousing"
    ],

    # ETL
    "etl": [
        "etl",
        "extract transform load",
        "extract transform and load"
    ],

    "data ingestion": [
        "data ingestion"
    ],

    "data pipelines": [
        "data pipeline",
        "data pipelines"
    ],

    # Modern Data Platforms
    "snowflake": [
        "snowflake"
    ],

    "databricks": [
        "databricks"
    ],

    # Business / Analytical
    "business requirements": [
        "business requirements"
    ],

    "requirements gathering": [
        "requirements gathering",
        "requirement gathering"
    ],

    "stakeholder management": [
        "stakeholder management",
        "stakeholder communication"
    ],

    "problem solving": [
        "problem solving",
        "problem-solving"
    ],

    "analytical thinking": [
        "analytical thinking",
        "analytical skills"
    ],

    # Machine Learning
    "machine learning": [
        "machine learning"
    ],

    "predictive modeling": [
        "predictive modeling",
        "predictive modelling"
    ],

    "regression": [
        "regression"
    ],

    "classification": [
        "classification"
    ],

    # Development
    "git": [
        "git"
    ],

    "github": [
        "github"
    ],

    "flask": [
        "flask"
    ],
}


# ============================================================
# RESUME CACHE
# ============================================================

_RESUME_TEXT_CACHE = {}


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"[^a-z0-9+#.\s-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# EXTRACT RESUME TEXT
# ============================================================

def extract_resume_text(
    resume_path=RESUME_PATH
):

    # GitHub Actions / cloud
    # Prefer pre-extracted resume text.
    resume_text_path = "resume_text.txt"

    if os.path.exists(resume_text_path):

        absolute_text_path = os.path.abspath(
            resume_text_path
        )

        if absolute_text_path in _RESUME_TEXT_CACHE:

            return _RESUME_TEXT_CACHE[
                absolute_text_path
            ]

        with open(
            absolute_text_path,
            "r",
            encoding="utf-8"
        ) as file:

            resume_text = file.read()

        if not resume_text.strip():

            raise ValueError(
                "resume_text.txt is empty."
            )

        _RESUME_TEXT_CACHE[
            absolute_text_path
        ] = resume_text

        return resume_text

    # Local fallback:
    # Use original PDF if resume_text.txt
    # is unavailable.
    absolute_path = os.path.abspath(
        resume_path
    )

    if absolute_path in _RESUME_TEXT_CACHE:

        return _RESUME_TEXT_CACHE[
            absolute_path
        ]

    if not os.path.exists(
        absolute_path
    ):

        raise FileNotFoundError(
            "Resume not found. Expected "
            "resume_text.txt or "
            f"{absolute_path}"
        )

    reader = PdfReader(
        absolute_path
    )

    pages = []

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            pages.append(
                page_text
            )

    resume_text = "\n".join(
        pages
    )

    if not resume_text.strip():

        raise ValueError(
            "Resume PDF contains no readable text."
        )

    _RESUME_TEXT_CACHE[
        absolute_path
    ] = resume_text

    return resume_text


# ============================================================
# PHRASE DETECTION
# ============================================================

def contains_phrase(
    text,
    phrase
):

    text = clean_text(
        text
    )

    phrase = clean_text(
        phrase
    )

    if not text or not phrase:

        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(phrase)
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            text
        )
    )


# ============================================================
# EXTRACT CANONICAL SKILLS
# ============================================================

def extract_skills(text):

    cleaned_text = clean_text(
        text
    )

    if not cleaned_text:

        return []

    detected = set()

    for canonical_skill, aliases in SKILL_GROUPS.items():

        for alias in aliases:

            if contains_phrase(
                cleaned_text,
                alias
            ):

                detected.add(
                    canonical_skill
                )

                break

    return sorted(
        detected
    )


# ============================================================
# TEXT SIMILARITY
#
# Diagnostic only.
# It DOES NOT reduce genuine skill coverage.
# ============================================================

def calculate_text_similarity(
    resume_text,
    job_description
):

    resume_text = clean_text(
        resume_text
    )

    job_description = clean_text(
        job_description
    )

    if not resume_text or not job_description:

        return 0.0

    try:

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=7000,
            sublinear_tf=True
        )

        matrix = vectorizer.fit_transform(
            [
                resume_text,
                job_description
            ]
        )

        similarity = cosine_similarity(
            matrix[0:1],
            matrix[1:2]
        )[0][0]

        return round(
            float(similarity) * 100,
            2
        )

    except ValueError:

        return 0.0


# ============================================================
# SKILL MATCH
# ============================================================

def calculate_skill_match(
    resume_text,
    job_description
):

    resume_skills = set(
        extract_skills(
            resume_text
        )
    )

    job_skills = set(
        extract_skills(
            job_description
        )
    )

    recognized_count = len(
        job_skills
    )

    # --------------------------------------------------------
    # NO RECOGNIZED JD SKILLS
    # --------------------------------------------------------

    if recognized_count == 0:

        return {

            "score": 0.0,

            "raw_score": 0.0,

            "resume_skills":
                sorted(resume_skills),

            "job_skills": [],

            "matched_skills": [],

            "missing_skills": [],

            "recognized_job_skill_count": 0,

            "matched_skill_count": 0,

            "evidence_sufficient": False
        }

    # --------------------------------------------------------
    # MATCHED / MISSING
    # --------------------------------------------------------

    matched_skills = (
        resume_skills
        & job_skills
    )

    missing_skills = (
        job_skills
        - resume_skills
    )

    matched_count = len(
        matched_skills
    )

    raw_score = (
        matched_count
        / recognized_count
    ) * 100

    evidence_sufficient = (
        recognized_count
        >= MIN_RECOGNIZED_JOB_SKILLS
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # If JD has only 1-2 recognized skills,
    # do NOT call it an 80-100% resume match.
    # --------------------------------------------------------

    if not evidence_sufficient:

        score = 0.0

    else:

        score = raw_score

    return {

        "score":
            round(score, 2),

        "raw_score":
            round(raw_score, 2),

        "resume_skills":
            sorted(resume_skills),

        "job_skills":
            sorted(job_skills),

        "matched_skills":
            sorted(matched_skills),

        "missing_skills":
            sorted(missing_skills),

        "recognized_job_skill_count":
            recognized_count,

        "matched_skill_count":
            matched_count,

        "evidence_sufficient":
            evidence_sufficient
    }


# ============================================================
# FINAL MATCH
# ============================================================

def calculate_match(
    job_description,
    resume_path=RESUME_PATH
):

    # --------------------------------------------------------
    # EMPTY JD
    # --------------------------------------------------------

    if (
        not job_description
        or not str(
            job_description
        ).strip()
    ):

        return {

            "match_score": 0.0,

            "passed": False,

            "skill_score": 0.0,

            "raw_skill_score": 0.0,

            "text_similarity": 0.0,

            "matched_skills": [],

            "missing_skills": [],

            "job_skills": [],

            "recognized_job_skill_count": 0,

            "matched_skill_count": 0,

            "evidence_sufficient": False,

            "reason":
                "Job description is empty"
        }

    # --------------------------------------------------------
    # LOAD RESUME
    # --------------------------------------------------------

    resume_text = extract_resume_text(
        resume_path
    )

    # --------------------------------------------------------
    # SKILL MATCH
    # --------------------------------------------------------

    skill_result = calculate_skill_match(
        resume_text,
        job_description
    )

    skill_score = float(
        skill_result.get(
            "score",
            0
        )
    )

    raw_skill_score = float(
        skill_result.get(
            "raw_score",
            0
        )
    )

    recognized_count = int(
        skill_result.get(
            "recognized_job_skill_count",
            0
        )
    )

    matched_count = int(
        skill_result.get(
            "matched_skill_count",
            0
        )
    )

    evidence_sufficient = bool(
        skill_result.get(
            "evidence_sufficient",
            False
        )
    )

    # --------------------------------------------------------
    # TEXT SIMILARITY
    #
    # Kept for reporting/debugging.
    # Not used to punish a genuine skill match.
    # --------------------------------------------------------

    text_score = calculate_text_similarity(
        resume_text,
        job_description
    )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    if not evidence_sufficient:

        final_score = 0.0

        reason = (
            "Insufficient recognized JD skills "
            f"({recognized_count}/"
            f"{MIN_RECOGNIZED_JOB_SKILLS} minimum)"
        )

    else:

        # ----------------------------------------------------
        # STRICT INTERPRETATION:
        #
        # Resume Match =
        # Matched recognized JD skills
        # ----------------------------
        # Total recognized JD skills
        #
        # Example:
        # 11 / 13 = 84.62%
        # ----------------------------------------------------

        final_score = round(
            skill_score,
            2
        )

        if final_score >= MIN_MATCH_SCORE:

            reason = (
                "Recognized JD skill coverage meets "
                f"{MIN_MATCH_SCORE}% threshold"
            )

        else:

            reason = (
                "Recognized JD skill coverage below "
                f"{MIN_MATCH_SCORE}% threshold"
            )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {

        "match_score":
            final_score,

        "passed":
            (
                evidence_sufficient
                and final_score >= MIN_MATCH_SCORE
            ),

        "skill_score":
            skill_score,

        "raw_skill_score":
            raw_skill_score,

        "text_similarity":
            text_score,

        "matched_skills":
            skill_result.get(
                "matched_skills",
                []
            ),

        "missing_skills":
            skill_result.get(
                "missing_skills",
                []
            ),

        "job_skills":
            skill_result.get(
                "job_skills",
                []
            ),

        "recognized_job_skill_count":
            recognized_count,

        "matched_skill_count":
            matched_count,

        "evidence_sufficient":
            evidence_sufficient,

        "reason":
            reason
    }


# ============================================================
# SELF TEST
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # GENUINE DATA ANALYST
    # --------------------------------------------------------

    genuine_jd = """

    We are hiring an entry-level Data Analyst.

    Candidates will use SQL, Python, Excel and
    Power BI for business data analysis.

    Responsibilities include data cleaning,
    data validation, dashboard development,
    reporting, KPI tracking and data visualization.

    Knowledge of Pandas and Power Query is preferred.

    Candidates with 0-2 years of experience may apply.

    """

    # --------------------------------------------------------
    # IRRELEVANT JOB
    # --------------------------------------------------------

    irrelevant_jd = """

    We are hiring an Automotive HMI Engineer.

    The candidate will work on embedded automotive
    systems, vehicle interfaces, hardware integration,
    infotainment systems and automotive engineering.

    """

    # --------------------------------------------------------
    # ONLY ONE RECOGNIZED SKILL
    # --------------------------------------------------------

    weak_evidence_jd = """

    We are looking for an associate who will work
    with SQL and support business teams.

    """

    # --------------------------------------------------------
    # REAL MISMATCH EXAMPLE
    # --------------------------------------------------------

    mismatch_jd = """

    We are hiring a Data Analyst.

    Required skills include SQL, Tableau,
    Snowflake, Databricks, PostgreSQL,
    data warehousing, ETL and data pipelines.

    """

    tests = [

        (
            "GENUINE DATA ANALYST",
            genuine_jd
        ),

        (
            "IRRELEVANT JOB",
            irrelevant_jd
        ),

        (
            "INSUFFICIENT EVIDENCE",
            weak_evidence_jd
        ),

        (
            "SKILL MISMATCH",
            mismatch_jd
        ),
    ]

    try:

        print(
            "\n"
            "=========================================="
        )

        print(
            "        STRICT ATS MATCHER TEST"
        )

        print(
            "=========================================="
        )

        for test_name, test_jd in tests:

            result = calculate_match(
                test_jd
            )

            print(
                f"\n{test_name}"
            )

            print(
                "------------------------------------------"
            )

            print(
                f"Final Match       : "
                f"{result['match_score']:.2f}%"
            )

            print(
                f"Skill Coverage    : "
                f"{result['skill_score']:.2f}%"
            )

            print(
                f"Raw Skill Match   : "
                f"{result['raw_skill_score']:.2f}%"
            )

            print(
                f"Text Similarity   : "
                f"{result['text_similarity']:.2f}%"
            )

            print(
                f"Recognized Skills : "
                f"{result['recognized_job_skill_count']}"
            )

            print(
                f"Matched Skills    : "
                f"{result['matched_skill_count']}"
            )

            print(
                f"Reason            : "
                f"{result['reason']}"
            )

            print(
                "RESULT            : "
                + (
                    "PASS"
                    if result["passed"]
                    else "REJECT"
                )
            )

            print(
                "Matched:"
            )

            for skill in result[
                "matched_skills"
            ]:

                print(
                    f"  + {skill}"
                )

            print(
                "Missing:"
            )

            for skill in result[
                "missing_skills"
            ]:

                print(
                    f"  - {skill}"
                )

        print(
            "\n"
            "=========================================="
        )

    except FileNotFoundError as error:

        print(
            "\nERROR:"
        )

        print(
            error
        )

    except Exception as error:

        print(
            "\nMATCHER TEST ERROR:"
        )

        print(
            error
        )