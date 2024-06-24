from fastapi import FastAPI, HTTPException, Path
from typing import List
import sys
sys.path.insert(0, r'D:\Documentos\UANL\Proyecto servicio social\API\app')
from schemas import *
from crud import *
app = FastAPI()

@app.post("/employees/create", response_model=dict)
async def create_new_employee(employee_data: Employee):
    try:
        # Verificar si ya existe un empleado con la misma matricula
        existing_employee = get_employee_by_number(employee_data.employee_number)
        if existing_employee:
            raise HTTPException(status_code=400, detail=f"Ya existe un empleado con matricula {employee_data.employee_number}")
        # Si no existe, crear el empleado
        create_employee(
            employee_data.employee_number,
            employee_data.name,
            employee_data.lastname,
            employee_data.dependency,
            employee_data.carRegistry
        )
        return {"message": "Empleado creado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/employees/{employee_number}", response_model=Employee)
async def read_employee(employee_number: int = Path(..., description="Número del empleado a consultar")):
    employee = get_employee_by_number(employee_number)
    if employee:
        return employee
    else:
        raise HTTPException(status_code=404, detail=f"Empleado con número {employee_number} no encontrado")


@app.put("/employees/update/{employee_id}", response_model=dict)
async def update_employee_data(employee_id: int, employee_data: EmployeeUpdate):
    try:
        update_employee(
            employee_id,
            employee_data.employee_number,
            employee_data.name,
            employee_data.lastname,
            employee_data.dependency,
            employee_data.carRegistry
        )
        return {"message": f"Empleado con ID {employee_id} actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/employees/delete/{employee_id}", response_model=dict)
async def delete_employee_data(employee_id: int):
    try:
        delete_employee(employee_id)
        return {"message": f"Empleado con ID {employee_id} eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/employees/getbyrange/{start_id}/{end_id}", response_model=List[dict])
async def get_employees_by_range(start_id: int, end_id: int):
    try:
        employees = get_employees_by_id_range(start_id, end_id)
        return employees
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
