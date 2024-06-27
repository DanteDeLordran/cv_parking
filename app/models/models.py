import datetime

from sqlmodel import Field, SQLModel


class Dependency(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_number: str
    name: str
    lastname: str
    dependency_id: int = Field(foreign_key="dependency.id")
    car_registry: str


class History(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    dependency_id: int = Field(foreign_key="dependency.id")
    entry_time = Field(default=datetime.datetime.now())
    exit_time = Field(default=datetime.datetime.now())
