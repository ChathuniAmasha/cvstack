from pydantic import BaseModel
from typing import List, Optional


class Candidate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


class Education(BaseModel):
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    grade: Optional[str] = None


class Project(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    impact: Optional[str] = None


class Experience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    summary: Optional[str] = None
    highlights: List[str] = []


class ParsedCV(BaseModel):
    candidate: Candidate = Candidate()
    education: List[Education] = []
    projects: List[Project] = []
    skills: List[str] = []
    experience: List[Experience] = []
