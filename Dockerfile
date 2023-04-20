FROM python:3.11-slim

ENV TZ="Asia/Yekaterinburg"

WORKDIR /src

COPY src .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]
