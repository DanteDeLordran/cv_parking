from db.database import engine
from models.models import SQLModel
from ann.serial_reader import run

SQLModel.metadata.create_all(engine)

if __name__ == '__main__':
    run()
