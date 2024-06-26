FROM python:3.11-slim

ENV TZ="Asia/Yekaterinburg"

WORKDIR /src

COPY src pyproject.toml poetry.lock ./

RUN pip3 install poetry==1.8.3
RUN poetry config virtualenvs.create false
RUN poetry install --only main

CMD ["python3", "main.py"]
