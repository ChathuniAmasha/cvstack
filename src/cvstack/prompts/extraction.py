from __future__ import annotations

import json

SYSTEM_PROMPT = (
    """You are a precise CV parsing engine. Your task is to extract data from the provided CV text into valid JSON following the schema provided below.

    ### STRICT EXTRACTION RULES (Adhere to these above all else):

    1. **NO HALLUCINATION / NO INFERENCE:**
    - **Industry:** Extract the industry ONLY if it is explicitly written in the CV (e.g., "Industry: Automotive"). DO NOT infer the industry from the candidate's job titles or company names. If not explicitly stated, return null.
    - **Address:** If no physical address (Street, City, etc.) is found, set `address` fields to null. CRITICAL: If `address_line_1` is null, `is_current_address` must also be null. Do not default it to true/false.
    - **General:** If a field is not found in the text, return `null` (for strings/objects) or `false` (for booleans, only if applicable). Do not use "N/A" or "Unknown".

    2. **DATA FORMATTING:**
    - **Web Links:** Aggressively scan for URLs, hyperlinks, and text patterns like "linkedin.com/in/...", "github.com/...", or "portfolio...". Include incomplete URLs if they are clearly meant to be links.
    - **Dates (Certifications/Education):** Extract dates ONLY as "YYYY-MM" or "Month YYYY". If the text contains garbage characters (e.g., "2023 xyz"), strip the garbage. If a valid date cannot be parsed, return null. Do not output random letters.

    3. **CONTEXT-AWARE SKILL SCORING:**
    - You must rate `user_skills.system_rating` (1–10) based on **Evidence + Professional Context**.
    - **Step A:** Determine the candidate's primary domain based on their experience (e.g., "Junior Frontend Dev" vs. "Senior Systems Architect").
    - **Step B:** Rate the skill using the rubric below, but **penalize** lack of evidence heavily if the skill is critical to their specific domain.
    - **Rubric:**
        - **1–2:** Keyword only; no context.
        - **3–4:** Basic usage/academic. (Standard for juniors; low for seniors).
        - **5–6:** Professional practical use with context.
        - **7–8:** Advanced usage, leadership, or measurable optimization.
        - **9–10:** Distinguished authority (patents, books, major open source).
    - *Constraint:* Never rate >3 without explicit project/work experience evidence linked to that skill in the text.

    ### OUTPUT FORMAT:
    - Output ONLY valid JSON.
    - No markdown blocks (```json), no preamble, no commentary."""
)

EXAMPLE_CV_TEXT = """Akhiliny Vijeyagumar Aspiring Data Engineer | Data scientist | Data Analyst akhilinyv@gmail.com Akhiliny V. Akhiliny V. Kilinochchi, Sri Lanka +94 766254606
PROFILE Detail-oriented Data Engineering undergraduate with hands-on experience in building data pipelines for ingestion, transformation, and reporting, and generating actionable insights through interactive dashboards.
PROFESSIONAL EXPERIENCE
Intern Data Science Developer - AryaLabs Pvt Ltd Apr 2025 – Present | Remote
• Collaborated on multiple data analysis and visualization projects focused on real-world datasets.
• Created interactive dashboards for Australian Road Deaths and Northumbria University Graduation using Power BI, providing actionable insights and detailed reports.
• Conducted a literature review to support insights from road safety data and visual trends.
• Cleaned, modeled, and analyzed datasets from movie databases, student information systems, and customer data to extract meaningful patterns.
• Delivered comprehensive reports and dashboards to support decision-making processes.
• Performed end-to-end data preparation, including cleaning, transformation, visualization, and reporting.
Technologies Used: Power BI, Excel, Python (Pandas, NumPy), Plotly, Jupyter Notebook, Google Colab, Data Cleaning, DAX, Data Analysis
PROJECTS
Apple Data Analysis - Individual Apr 2025 – Apr 2025
Built ETL pipelines using PySpark, implemented the Factory Pattern for data ingestion, and optimized performance with advanced Spark techniques.
Technologies: Apache Spark, Databricks, PySpark, Spark SQL
IPL Data Analysis - Individual Mar 2025 – Apr 2025
Designed a complete data pipeline to ingest, transform, and analyze IPL 2023 datasets. Extracted actionable insights on player performance and match statistics.
Technologies: Databricks, Apache Spark, Python, SparkSQL, Pandas
Netflix Data Analysis - Individual Feb 2025 – Mar 2025
Engineered an end-to-end ELT pipeline in Python to clean and analyze Netflix data, extracting insights on content trends, genres, and user preferences, with data cleaning and visualization.
Technologies: Python, Pandas, NumPy, Plotly Express, TextBlob, ELT, Data Cleaning, Data Analysis
Spotify Data Pipeline - Individual Feb 2025 – Mar 2025
Devised an ETL pipeline to process and analyze Spotify data, extracting insights on user behavior, song trends, and playlists.
Technologies: AWS (Athena, Glue, S3), PySpark, Python, Data Processing, ETL Pipelines
Sonar Rock vs Mine Prediction - Individual Apr 2025 – May 2025
Developed a binary classification model using Logistic Regression to identify sonar signals as Rock or Mine based on 60 numerical features from the UCI dataset. Achieved 83.42% training accuracy and 76.19% test accuracy and built a real-time prediction system with user input capability.
Technologies: Python, NumPy, Pandas, scikit-learn
PIMDB Movie Review Sentiment Analysis using Deep Learning (LSTM) - Individual Apr 2025 – May 2025
Implemented an LSTM-based deep learning model to classify IMDb movie reviews as positive or negative. Deployed an interactive web app using Gradio for real-time sentiment prediction. Preprocessed data with Tokenizer & Padding, achieved high-accuracy sentiment classification with LSTM, and built and deployed a user-friendly Gradio web interface.
Technologies: Python, Keras, TensorFlow, LSTM, NumPy, Gradio, Google Colab
EDUCATION
BSc (Hons) in Software Engineering Sabaragamuwa University of Sri Lanka Aug 2022 – Aug 2026
G.C.E Advanced Level - Combined Mathematics, Physics, ICT KN/Kilinochchi Hindu College Jul 2010 – Aug 2018
SKILLS
Programming Languages — Python, SQL, C, JavaScript, HTML, CSS, Java (Basics)
ETL & Data Pipelines — Data Ingestion, Transformation, Validation, Data Warehousing, Architecture, Deployment
Big Data & Data Engineering — Apache Spark, PySpark, Databricks, Hadoop, Hive, Sqoop, HBase, Apache Airflow
Cloud Platforms — Google Cloud Platform (GCP), Amazon Web Services (AWS), Microsoft Azure
Databases — Power BI, Tableau, Plotly Express, DAX, Star Schema Design
Tools — pgAdmin, PHPMyAdmin, Trello, Protégé
Data Visualization — Power BI, Tableau, Plotly Express, DAX, Star Schema Design
Data Analysis & ML — Pandas, NumPy, scikit-learn, TensorFlow, Keras, TextBlob, Data Cleaning
Operating Systems — Linux, Windows
Soft Skills — Analytical Thinking, Problem Solving, Troubleshooting, Communication, Team Collaboration, Time Management, Documentation
CERTIFICATES
Oracle Data Platform 2025 Foundations Associate (Oracle, April 2025)
Data Engineering on AWS – Foundations (AWS, April 2025)
Data Engineering Foundations Specialization – IBM (Coursera, April 2025)
Fundamentals of Machine Learning and Artificial Intelligence (AWS, April 2025)
30 Days Data Analytics Masterclass (Navitech, 2025)
Data Science and Analytics (HP Life, 2025)
Diploma in Using Python for Data Science (Alison, April 2025)
Master in Data Warehouse and Data Visualization (Udemy, June 2024)
Foundations in Machine Learning (Microsoft Plus, July 2024)
Machine Learning with Python (Coursera, March 2024)
REFERENCES
Prof. S. Vasantha Priyan, Dean, Faculty of Computing and Chair – IEEE Sri Lanka Section, Sabaragamuwa University of Sri Lanka, priyan@foc.sab.ac.lk, 0717851500
Ms. Kumudu Kaushalya, Lecturer, Faculty of Computing, Sabaragamuwa University of Sri Lanka, kaushalya@foc.sab.ac.lk, 0717063574
"""

EXAMPLE_JSON = json.dumps(
    {
        "user_profile": {
            "first_name": "Akhiliny",
            "middle_name": "",
            "last_name": "Vijeyagumar",
            "about": "Detail-oriented Data Engineering undergraduate with hands-on experience in building data pipelines for ingestion, transformation, and reporting, and generating actionable insights through interactive dashboards.",
            "email": "akhilinyv@gmail.com",
            "phone": "+94 766254606",
            "dob": "",
            "marital_status": "",
            "gender": "",
            "industry": "Data Engineering",
            "is_valid_resume": True
        },
        "user_web_links": [],
        "address": {
            "address_line_1": "",
            "address_line_2": "",
            "city": "Kilinochchi",
            "postal_code": "",
            "province": "Northern Province",
            "country": "Sri Lanka",
            "is_current_address": True
        },
        "education": [
            {
                "degree": "BSc (Hons) in Software Engineering",
                "field": "",
                "institution": "Sabaragamuwa University of Sri Lanka",
                "start": "Aug 2022",
                "end": "Aug 2026",
                "grade": "",
                "city": "Belihuloya",
                "province": "Sabaragamuwa Province",
                "country": "Sri Lanka"
            },
            {
                "degree": "G.C.E Advanced Level",
                "field": "Combined Mathematics, Physics, ICT",
                "institution": "KN/Kilinochchi Hindu College",
                "start": "Jul 2010",
                "end": "Aug 2018",
                "grade": "",
                "city": "Kilinochchi",
                "province": "Northern Province",
                "country": "Sri Lanka"
            }
        ],
        "certifications": [
            {
                "name": "Oracle Data Platform 2025 Foundations Associate",
                "issuer": "Oracle",
                "issue_date": "Apr 2025"
            },
            {
                "name": "Data Engineering on AWS – Foundations",
                "issuer": "Amazon Web Services",
                "issue_date": "Apr 2025"
            },
            {
                "name": "Data Engineering Foundations Specialization",
                "issuer": "IBM / Coursera",
                "issue_date": "Apr 2025"
            },
            {
                "name": "Fundamentals of Machine Learning and Artificial Intelligence",
                "issuer": "Amazon Web Services",
                "issue_date": "Apr 2025"
            },
            {
                "name": "30 Days Data Analytics Masterclass",
                "issuer": "Navitech",
                "issue_date": "2025"
            },
            {
                "name": "Data Science and Analytics",
                "issuer": "HP Life",
                "issue_date": "2025"
            },
            {
                "name": "Diploma in Using Python for Data Science",
                "issuer": "Alison",
                "issue_date": "Apr 2025"
            },
            {
                "name": "Master in Data Warehouse and Data Visualization",
                "issuer": "Udemy",
                "issue_date": "Jun 2024"
            },
            {
                "name": "Foundations in Machine Learning",
                "issuer": "Microsoft Plus",
                "issue_date": "Jul 2024"
            },
            {
                "name": "Machine Learning with Python",
                "issuer": "Coursera",
                "issue_date": "Mar 2024"
            }
        ],
        "experience": [
            {
                "company": "AryaLabs Pvt Ltd",
                "role": "Intern Data Science Developer",
                "start": "Apr 2025",
                "end": "Present",
                "currently_working": True,
                "summary": "Collaborated on multiple data analysis and visualization projects focused on real-world datasets, delivering dashboards and reports that supported decision-making processes.",
                "highlights": [
                    "Created interactive dashboards for Australian Road Deaths and Northumbria University Graduation using Power BI.",
                    "Conducted literature review to support road safety data insights.",
                    "Cleaned, modeled, and analyzed datasets from diverse domains.",
                    "Delivered comprehensive reports and dashboards for stakeholders.",
                    "Performed end-to-end data preparation including cleaning, transformation, visualization, and reporting."
                ]
            }
        ],
        "projects": [
            {
                "title": "Apple Data Analysis",
                "summary": "Built ETL pipelines using PySpark, implemented the Factory Pattern for data ingestion, and optimized performance with advanced Spark techniques.",
                "skills": [
                    "Apache Spark",
                    "Databricks",
                    "PySpark",
                    "Spark SQL"
                ],
                "domain": "Data Engineering",
                "responsibilities": [
                    "Individual Contributor"
                ]
            },
            {
                "title": "IPL Data Analysis",
                "summary": "Designed a complete data pipeline to ingest, transform, and analyze IPL 2023 datasets, extracting actionable insights on player performance and match statistics.",
                "skills": [
                    "Databricks",
                    "Apache Spark",
                    "Python",
                    "SparkSQL",
                    "Pandas"
                ],
                "domain": "Data Engineering",
                "responsibilities": [
                    "Individual Contributor"
                ]
            },
            {
                "title": "Netflix Data Analysis",
                "summary": "Engineered an end-to-end ELT pipeline in Python to clean and analyze Netflix data, revealing content trends, genres, and user preferences.",
                "skills": [
                    "Python",
                    "Pandas",
                    "NumPy",
                    "Plotly Express",
                    "TextBlob",
                    "ELT",
                    "Data Cleaning",
                    "Data Analysis"
                ],
                "domain": "Data Analysis",
                "responsibilities": [
                    "Individual Contributor"
                ]
            },
            {
                "title": "Spotify Data Pipeline",
                "summary": "Devised an ETL pipeline processing Spotify data to uncover user behavior, song trends, and playlist insights using AWS services.",
                "skills": [
                    "AWS Athena",
                    "AWS Glue",
                    "AWS S3",
                    "PySpark",
                    "Python",
                    "Data Processing"
                ],
                "domain": "Data Engineering",
                "responsibilities": [
                    "Individual Contributor"
                ]
            },
            {
                "title": "Sonar Rock vs Mine Prediction",
                "summary": "Developed a logistic regression classifier to distinguish sonar signals, achieving 83.42% training accuracy and 76.19% test accuracy, with a user-facing prediction interface.",
                "skills": [
                    "Python",
                    "NumPy",
                    "Pandas",
                    "scikit-learn"
                ],
                "domain": "Machine Learning",
                "responsibilities": [
                    "Individual Contributor"
                ]
            },
            {
                "title": "PIMDB Movie Review Sentiment Analysis",
                "summary": "Implemented an LSTM model for sentiment classification and deployed a Gradio web app for real-time predictions.",
                "skills": [
                    "Python",
                    "Keras",
                    "TensorFlow",
                    "LSTM",
                    "NumPy",
                    "Gradio"
                ],
                "domain": "Deep Learning",
                "responsibilities": [
                    "Individual Contributor"
                ]
            }
        ],
        "user_skills": [
            {
                "skill": "Python",
                "level_of_skill": "Expert",
                "system_rating": 8,
                "description": "Extensive use across professional work and multiple projects, covering ETL, analytics, machine learning, and deployment."
            },
            {
                "skill": "Data Analysis",
                "level_of_skill": "Advanced",
                "system_rating": 7,
                "description": "Delivered insights from diverse datasets, supporting decision-making with dashboards and reports."
            },
            {
                "skill": "Data Visualization",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Created actionable dashboards with Power BI and Plotly; visualized trends across multiple projects."
            },
            {
                "skill": "ETL / Data Pipelines",
                "level_of_skill": "Expert",
                "system_rating": 8,
                "description": "Built end-to-end ingestion, transformation, and reporting pipelines across several projects."
            },
            {
                "skill": "Apache Spark",
                "level_of_skill": "Advanced",
                "system_rating": 7,
                "description": "Developed Spark-based pipelines, optimizing performance and handling large datasets."
            },
            {
                "skill": "PySpark",
                "level_of_skill": "Advanced",
                "system_rating": 7,
                "description": "Implemented multiple ETL pipelines leveraging PySpark for data processing."
            },
            {
                "skill": "Power BI",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Produced interactive dashboards for real-world datasets with actionable insights."
            },
            {
                "skill": "Pandas",
                "level_of_skill": "Advanced",
                "system_rating": 7,
                "description": "Used for cleaning, modeling, and analysis across multiple projects."
            },
            {
                "skill": "NumPy",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Applied in analytical and machine-learning contexts for numerical processing."
            },
            {
                "skill": "Data Cleaning",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Handled end-to-end data preparation, including cleaning for several projects."
            },
            {
                "skill": "Machine Learning",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Built supervised models with measured accuracy metrics and relevant certifications."
            },
            {
                "skill": "Deep Learning",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Implemented LSTM-based models for sentiment analysis with deployment."
            },
            {
                "skill": "AWS",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Applied AWS services (Athena, Glue, S3) in ETL pipelines; holds AWS certifications."
            },
            {
                "skill": "Databricks",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Used in Spark-based analytics projects for data engineering workloads."
            },
            {
                "skill": "Spark SQL",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Applied within Spark projects for querying and transformations."
            },
            {
                "skill": "SQL",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Foundational usage implied via Spark SQL and listed skillset."
            },
            {
                "skill": "Plotly",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Used in visual analytics tasks across multiple projects."
            },
            {
                "skill": "Plotly Express",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Applied for interactive visualizations in Netflix analytics project."
            },
            {
                "skill": "Jupyter Notebook",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Tool listed among technologies used for analysis."
            },
            {
                "skill": "Google Colab",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Used in several analytics and deep learning projects."
            },
            {
                "skill": "DAX",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Applied within Power BI dashboards."
            },
            {
                "skill": "TextBlob",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Used for text processing in analytics projects."
            },
            {
                "skill": "scikit-learn",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Implemented supervised models with evaluation metrics."
            },
            {
                "skill": "TensorFlow",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Used for LSTM-based sentiment models."
            },
            {
                "skill": "Keras",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Framework for building deep learning models."
            },
            {
                "skill": "LSTM",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Core technique for sentiment classification project."
            },
            {
                "skill": "Gradio",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Enabled interactive deployment of ML models."
            },
            {
                "skill": "Data Ingestion",
                "level_of_skill": "Advanced",
                "system_rating": 7,
                "description": "Designed ingestion steps within multiple pipelines."
            },
            {
                "skill": "Data Transformation",
                "level_of_skill": "Advanced",
                "system_rating": 7,
                "description": "Performed transformations across end-to-end workflows."
            },
            {
                "skill": "Data Warehousing",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Baseline knowledge supported by coursework and certificates."
            },
            {
                "skill": "Star Schema Design",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Concepts referenced in tooling and training."
            },
            {
                "skill": "Data Reporting",
                "level_of_skill": "Intermediate",
                "system_rating": 6,
                "description": "Delivered reports and dashboards for stakeholders."
            },
            {
                "skill": "Microsoft Excel",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Tool usage noted among technologies."
            },
            {
                "skill": "Data Modeling",
                "level_of_skill": "Intermediate",
                "system_rating": 5,
                "description": "Modeled datasets as part of analysis projects."
            },
            {
                "skill": "Analytical Thinking",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Highlighted through repeated insight generation."
            },
            {
                "skill": "Problem Solving",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Soft skill inferred from successful projects."
            },
            {
                "skill": "Troubleshooting",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Soft skill supporting technical workflow resolutions."
            },
            {
                "skill": "Communication",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Evidenced by delivering stakeholder reports."
            },
            {
                "skill": "Team Collaboration",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Mentioned via collaborative project experience."
            },
            {
                "skill": "Time Management",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Implied by handling multiple concurrent projects."
            },
            {
                "skill": "Documentation",
                "level_of_skill": "Beginner",
                "system_rating": 3,
                "description": "Listed as a soft skill; implied through project deliveries."
            },
            {
                "skill": "Data Engineering",
                "level_of_skill": "Expert",
                "system_rating": 8,
                "description": "Core focus across education, experience, projects, and certifications."
            },
            {
                "skill": "Data Science",
                "level_of_skill": "Advanced",
                "system_rating": 7,
                "description": "Professional experience and multiple credentials in analytics."
            },
            {
                "skill": "Artificial Intelligence",
                "level_of_skill": "Beginner",
                "system_rating": 4,
                "description": "Foundational exposure demonstrated by coursework and projects."
            }
        ]
    },
    indent=2
)

SCHEMA = {
    "user_profile": {
        "first_name": "text",
        "middle_name": "text",
        "last_name": "text",
        "about": "text",
        "email": "text",
        "phone": "text",
        "dob": "text",
        "marital_status": "text",
        "gender": "text",
        "industry": "text",
        "is_valid_resume": "boolean"
    },
    "user_web_links": [
        {
            "web_link": "text",
            "website_type": "text"
        }
    ],
    "address": {
        "address_line_1": "text",
        "address_line_2": "text",
        "city": "text",
        "postal_code": "text",
        "province": "text",
        "country": "text",
        "is_current_address": "boolean"
    },
    "education": [
        {
            "degree": "text",
            "field": "text",
            "institution": "text",
            "start": "text",
            "end": "text",
            "grade": "text"
        }
    ],
    "experience": [
        {
            "company": "text",
            "role": "text",
            "start": "text",
            "end": "text",
            "summary": "text",
            "currently_working": "boolean",
            "highlights": [
                "text"
            ]
        }
    ],
    "projects": [
        {
            "title": "text",
            "summary": "text",
            "skills": [
                "text"
            ],
            "domain": "text",
            "responsibilities": [
                "text"
            ]
        }
    ],
    "certifications": [
        {
            "name": "text",
            "issuer": "text",
            "issue_date": "text"
        }
    ],
    "user_skills": [
        {
            "skill": "text",
            "level_of_skill": "text",
            "system_rating": "integer",
            "description": "text"
        }
    ]
}

USER_PROMPT_TEMPLATE = """
Example CV text:
\"\"\"{example_cv}\"\"\"

Expected JSON:
```json
{example_json}
```

Extract data from the following CV. Use the SCHEMA below.
Rules:
- Respect field types.
- Dates as found (no reformat guesses).
- For user_skills: derive level_of_skill (e.g., Beginner, Intermediate, Advanced, Expert) consistent with system_rating.
- system_rating MUST be an integer 1–10 per rubric and evidence.
- description: concise evidence-based justification (source phrases).
- Do not include skills not present.
- If is_valid_resume is false (e.g., very sparse, job listing, or not a CV), keep minimal fields and set is_valid_resume=false.

SCHEMA:
{schema}

CV TEXT:
\"\"\"
{cv_text}
\"\"\"

Return ONLY the JSON object.
"""

def build_user_prompt(cv_text: str) -> str:
    """Build the user prompt with CV text embedded."""
    if not cv_text or not cv_text.strip():
        raise ValueError("cv_text cannot be empty")
    
    prompt = USER_PROMPT_TEMPLATE.format(
        example_cv=EXAMPLE_CV_TEXT,
        example_json=EXAMPLE_JSON,
        schema=json.dumps(SCHEMA, indent=2),
        cv_text=cv_text,
    )
    
    if not prompt or not prompt.strip():
        raise ValueError("Generated prompt is empty")
    
    return prompt