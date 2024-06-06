from typing import Optional
from sqlmodel import Field, SQLModel


class Dependency(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name : str

class Employee(SQLModel, table=True):
    id : int | None = Field(default=None, primary_key=True)
    employee_number : str
    name: str
    lastname : str
    dependency_id : int = Field(foreign_key="dependency.id")
    car_registry : str