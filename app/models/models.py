from datetime import datetime


class Dependency:
    id: int
    name: str


class Employee:
    id: int
    employee_number: str
    name: str
    lastname: str
    dependency_id: int
    car_registry: str


class History:
    id: int
    employee_id: int
    dependency_id: int
    entry_time: datetime
    exit_time: datetime
