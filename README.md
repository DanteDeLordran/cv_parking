# CVParking
A computational vision NN project for detecting and giving access to cars based on their car registration

## Stack used
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/opencv/opencv-original-wordmark.svg" height=80/> <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/numpy/numpy-original.svg" height=80/> <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg" height=80/> <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/sqlalchemy/sqlalchemy-original.svg" height=80 /> <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/docker/docker-original-wordmark.svg" height=80 />

## Start project
1. Install dependencies
This might take some minutes since some dependencies are very heavy sized
```
pip install --no-cache-dir -r requirements.txt
```

## Start DB

For development runtime we use a local Docker Postgres image
```
docker compose up -d
```
This will download Postgres and pgAdmin images if not found and run both on a container with can be access in port 5432 for Postgres and 80 for pgAdmin

## Migrations

```
alembic init migrations
```
In alembic.ini change :
```
sqlalchemy.url = postgres:///database.db
```
In migrations/env.py change :
```
from app.models.models import SQLModel
target_metadata = SQLModel.metadata
```
In .mako add :
```
import sqlmodel
```
Execute change
```
alembic revision --autogenerate -m "<message>"
```
Run migration
```
alembic upgrade head
```