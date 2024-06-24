from pydantic import BaseModel
from typing import Optional

class Employee(BaseModel):
    id: Optional[int]
    employee_number: int
    name: str
    lastname: str
    dependency: str
    carRegistry: str

class EmployeeUpdate(Employee):
    None
