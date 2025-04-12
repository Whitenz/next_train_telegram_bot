FROM python:3.12-alpine

ENV TZ="Asia/Yekaterinburg"

WORKDIR /src

COPY src pyproject.toml poetry.lock ./

RUN apk add --no-cache gcc musl-dev linux-headers

RUN pip install poetry==1.8.4
RUN poetry config virtualenvs.create false
RUN poetry install --only main

CMD ["python", "main.py"]
