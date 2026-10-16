from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================
# COMMON
# ============================================================

class BaseDocument(BaseModel):
    document_id: Optional[str] = None
    document_type: str
    source_file: Optional[str] = None

    name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None


# ============================================================
# CLASS 10
# ============================================================

class Class10Mark(BaseModel):
    total: Optional[float] = None
    max_marks: Optional[float] = None


class Class10Schema(BaseDocument):
    document_type: str = "10th_marksheet"

    board: Optional[str] = None
    school: Optional[str] = None

    marks: Dict[str, Class10Mark] = Field(default_factory=dict)

    total_marks_obtained: Optional[float] = None
    total_max_marks: Optional[float] = None
    percentage: Optional[float] = None
    result: Optional[str] = None


# ============================================================
# CLASS 12
# ============================================================

class Class12Mark(BaseModel):
    total: Optional[float] = None
    max_marks: Optional[float] = None
    subject_type: Optional[str] = None


class Class12Schema(BaseDocument):
    document_type: str = "12th_marksheet"

    board: Optional[str] = None
    school: Optional[str] = None

    marks: Dict[str, Class12Mark] = Field(default_factory=dict)

    total_marks_obtained: Optional[float] = None
    total_max_marks: Optional[float] = None
    percentage: Optional[float] = None
    result: Optional[str] = None


# ============================================================
# COLLEGE
# ============================================================

class CollegeMark(BaseModel):
    internal: Optional[float] = None
    external: Optional[float] = None

    total: Optional[float] = None
    max_marks: Optional[float] = None

    grade: Optional[str] = None
    grade_points: Optional[float] = None
    credits: Optional[float] = None


class CollegeSchema(BaseDocument):
    document_type: str = "college_marksheet"

    college: Optional[str] = None
    university: Optional[str] = None

    course: Optional[str] = None
    branch: Optional[str] = None

    semester: Optional[int] = None
    academic_year: Optional[str] = None
    passing_year: Optional[int] = None

    marks: Dict[str, CollegeMark] = Field(default_factory=dict)

    total_marks_obtained: Optional[float] = None
    total_max_marks: Optional[float] = None

    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    percentage: Optional[float] = None

    result: Optional[str] = None

    extra_details: Dict[str, Any] = Field(default_factory=dict)
