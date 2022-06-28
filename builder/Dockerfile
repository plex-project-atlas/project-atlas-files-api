FROM python:3.10-alpine3.16
# OS python libs requirements
ENV  TZ=UTC
RUN  apk add --no-cache build-base libmagic
# Python requirements
RUN  mkdir -p /app /files /tmp/pytest
COPY ./builder/requirements.txt /app/requirements.txt
RUN  python -m pip install --no-cache-dir --upgrade pip
RUN  pip install --no-cache-dir --upgrade -r /app/requirements.txt
# Application code
COPY    ./app /app
WORKDIR /app
# Run app
CMD ["python", "main.py"]
