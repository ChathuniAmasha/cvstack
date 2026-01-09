from pydantic import BaseModel      #Ensures that whatever comes from Gemini or the API is valid JSON, with correct fields
from typing import List, Optional


class UserProfile(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    about: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[str] = None
    target_role: Optional[str] = None
    role_confidence: Optional[float] = None
    marital_status: Optional[str] = None
    gender: Optional[str] = None
    industry: Optional[str] = None
    is_valid_resume: Optional[bool] = None


class UserWebLink(BaseModel):
    web_link: Optional[str] = None
    website_type: Optional[str] = None  # LinkedIn, GitHub, Portfolio, Website, Blog, Other


class Address(BaseModel):
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    is_current_address: Optional[bool] = None


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
    domain: Optional[str] = None
    responsibilities: List[str] = []


class Experience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    summary: Optional[str] = None
    currently_working: Optional[bool] = None
    highlights: List[str] = []


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None


class UserSkill(BaseModel):
    skill: Optional[str] = None
    level_of_skill: Optional[str] = None  # beginner, intermediate, advanced, expert
    system_rating: Optional[int] = None   # 1-10
    description: Optional[str] = None


class ParsedCV(BaseModel):
    user_profile: UserProfile = UserProfile()
    user_web_links: List[UserWebLink] = []
    address: Address = Address()
    education: List[Education] = []
    experience: List[Experience] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    user_skills: List[UserSkill] = []


# Legacy alias for backward compatibility
Candidate = UserProfile
