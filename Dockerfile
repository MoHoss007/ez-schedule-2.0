# Dockerfile
FROM amazon/aws-lambda-python:3.11

# 1) install deps into the Lambda task root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -t ${LAMBDA_TASK_ROOT}
COPY setup.py .
RUN pip install -e .

# 2) copy your code
COPY . ${LAMBDA_TASK_ROOT}

# 3) set the Lambda handler: <module>.<function>
#    Do NOT use a web server here; Lambda invokes this handler directly.
CMD ["lambda_handler.handler"]