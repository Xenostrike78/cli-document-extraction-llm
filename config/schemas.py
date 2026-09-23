from typing import Optional
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
    father_name: Optional[str] = None
    dob: Optional[str] = None
    roll_no: Optional[str] = None
    percentage: Optional[float] = Field(default=None, ge=0, le=100)
    cgpa: Optional[float] = Field(default=None, ge=0)
    monthly_income: Optional[float] = Field(default=None, ge=0)
    annual_income: Optional[float] = Field(default=None, ge=0)
    result: Optional[str] = None
    subjects: list[Subject] = []


class SelfReportedForm(BaseModel):
    """
    What the candidate declared themselves, e.g. NIC/<candidate_id>/self_reported.json.
    Compared against what the AI extracts from the uploaded documents.
    """
    name: Optional[str] = None
    father_name: Optional[str] = None
    dob: Optional[str] = None
    roll_no: Optional[str] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    monthly_income: Optional[float] = None
    annual_income: Optional[float] = None
