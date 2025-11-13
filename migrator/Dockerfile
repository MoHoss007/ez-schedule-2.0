# migrator/Dockerfile
FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

# 1) Install only what the migrator needs
COPY migrator/requirements-migrator.txt .
RUN pip install --no-cache-dir -r requirements-migrator.txt

# 2) Bring in alembic + config + your app package for Base import
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY app ./app

# 3) Migrator handler
COPY migrator/lambda_migrator.py ./lambda_migrator.py

# Helpful env
ENV PYTHONUNBUFFERED=1 \
    SECRET_ID=myapp/prod/db \
    PYTHONPATH=/var/task

# Lambda entrypoint
CMD ["lambda_migrator.lambda_handler"]
