from typing import Optional,List
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
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None

    roll_no: Optional[str] = None
    registration_no: Optional[str] = None

    school: Optional[str] = None

    document_date: Optional[str] = None

    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    result: Optional[str] = None

    subjects: List[Subject]


class SelfReportedForm(BaseModel):
    """
    What the candidate declared themselves, e.g.
    NIC/<candidate_id>/self_reported.json.

    Compared against what the AI extracts from the uploaded documents.
    """

    # Personal information
    name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    dob: Optional[str] = None

    # Academic identification
    roll_no: Optional[str] = None
    registration_no: Optional[str] = None

    # Institution
    school: Optional[str] = None

    # Academic results
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    result: Optional[str] = None

    # Subject-wise marks
    subjects: List[Subject] = Field(default_factory=list)