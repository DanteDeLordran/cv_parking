import psycopg2
from psycopg2 import sql, errors
from database import get_db_conn

#id SERIAL PRIMARY KEY,
#employee_number INT,
#name VARCHAR(100),
#lastname VARCHAR(100),
#dependency VARCHAR(100),
#carRegistry VARCHAR(100)

# Función para crear un nuevo empleado
def create_employee(employee_number, name, lastname, dependency, carRegistry):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        insert_query = sql.SQL("INSERT INTO employees (employee_number, name, lastname, dependency, carRegistry) VALUES (%s, %s, %s, %s, %s)")
        cursor.execute(insert_query, (employee_number, name, lastname, dependency, carRegistry))
        conn.commit()
        print("Empleado creado correctamente")
    except errors.UniqueViolation as e:
        print(f"Error al crear empleado: {e}")
        raise
    except Exception as e:
        print(f"Error inesperado: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_employee_by_number(employee_number: int):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        select_query = """
            SELECT id, employee_number, name, lastname, dependency, carRegistry 
            FROM employees 
            WHERE employee_number = %s
        """
        cursor.execute(select_query, (employee_number,))
        employee = cursor.fetchone()
        if employee:
            employee_dict = {
                "id": employee[0],
                "employee_number": employee[1],
                "name": employee[2],
                "lastname": employee[3],
                "dependency": employee[4],
                "carRegistry": employee[5]
            }
            print(employee_dict)
            return employee_dict
        else:
            return None
    except Exception as e:
        print(f"Error al obtener empleado por número de empleado: {e}")
        raise
    finally:
        cursor.close()
        conn.close()



def get_employees_by_id_range(start_id, end_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        select_query = sql.SQL("""
            SELECT id, employee_number, name, lastname, dependency, carRegistry 
            FROM employees 
            WHERE id >= %s AND id <= %s
        """)
        cursor.execute(select_query, (start_id, end_id))
        employees = cursor.fetchall()
        
        # Convert the fetched data into a list of dictionaries
        employee_list = []
        for employee in employees:
            employee_dict = {
                'id': employee[0],
                'employee_number': employee[1],
                'name': employee[2],
                'lastname': employee[3],
                'dependency': employee[4],
                'carRegistry': employee[5]
            }
            employee_list.append(employee_dict)
        return employee_list
    except Exception as e:
        print(f"Error al obtener empleados por rango de IDs: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def update_employee(employee_id, employee_number, name, lastname, dependency, carRegistry): #Actualiza a un empleado por su matricula
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        update_query = sql.SQL("""
            UPDATE employees 
            SET employee_number = %s, name = %s, lastname = %s, dependency = %s, carRegistry = %s
            WHERE id = %s
        """)
        cursor.execute(update_query, (employee_number, name, lastname, dependency, carRegistry, employee_id))
        conn.commit()
        print(f"Empleado con ID {employee_id} actualizado correctamente")
    except Exception as e:
        print(f"Error al actualizar empleado: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def delete_employee(employee_id): #Borra a un empleado por su ID (matricula)
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        delete_query = sql.SQL("DELETE FROM employees WHERE id = %s")
        cursor.execute(delete_query, (employee_id,))
        conn.commit()
        print(f"Empleado con ID {employee_id} eliminado correctamente")
    except Exception as e:
        print(f"Error al eliminar empleado: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
