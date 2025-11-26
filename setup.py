from setuptools import setup, find_packages

setup(
    name="cvstack",
    version="0.1",
    description="CV parsing and analysis system",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "python-dotenv",
        "psycopg[binary]",
        "pydantic",
        "pypdf",
        "fastapi",
        "uvicorn",
        "google-generativeai",
        "python-multipart",
        "pandas",
        "openpyxl",
        "setuptools>=42",
        "wheel",
        "pgvector"  # for vector operations with PostgreSQL
    ],
)