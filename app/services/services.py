from app.models.models import Employee


async def get_employee_by_car_registry(registry: str) -> Employee | None:
    return None


async def is_registry_registered(registry: str) -> bool:
    return False
