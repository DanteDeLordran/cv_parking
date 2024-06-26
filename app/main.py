from sqlmodel import Session, select
from models.models import Employee, SQLModel
from db.database import engine

SQLModel.metadata.create_all(engine)


def get_all_employees_car_registry():
    with Session(engine) as session:
        employees = session.exec(select(Employee))

        if len(employees.all()) == 0:
            print(f"No registry {len(employees.all())}")
        else:
            for employee in employees:
                print(employee.car_registry)


def get_employee_by_car_registry(registry: str):
    with Session(engine) as session:
        employee = session.exec(select(Employee).where(Employee.car_registry == registry)).first()
        if employee is not None:
            print(f"{employee.name} {employee.lastname}")
            return True
        else:
            print(f"No employee with car registry {registry}")
            return False
