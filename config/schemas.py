from typing import Optional, List
from pydantic import BaseModel, Field

class Subject(BaseModel):
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    theory_marks: Optional[float] = None
    practical_marks: Optional[float] = None
    total_marks: Optional[float] = None

class DocumentExtraction(BaseModel):
    document_type: str

    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    category: Optional[str] = None

    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None

    roll_no: Optional[str] = None
    registration_no: Optional[str] = None
    enrollment_no: Optional[str] = None

    school: Optional[str] = None
    college: Optional[str] = None
    university: Optional[str] = None
    board: Optional[str] = None

    course: Optional[str] = None
    branch: Optional[str] = None
    academic_year: Optional[str] = None
    passing_year: Optional[str] = None
    semester: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    document_date: Optional[str] = None

    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    result: Optional[str] = None

    subjects: List[Subject] = Field(default_factory=list)


class SelfReportedForm(BaseModel):
    # Personal information
    name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    category: Optional[str] = None

    # Academic identification
    roll_no: Optional[str] = None
    registration_no: Optional[str] = None
    enrollment_no: Optional[str] = None

    # Institution
    school: Optional[str] = None
    college: Optional[str] = None
    university: Optional[str] = None

    # Academic results
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    result: Optional[str] = None

    # Subject-wise marks
    subjects: List[Subject] = Field(default_factory=list)
