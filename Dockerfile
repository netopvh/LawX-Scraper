FROM python:3.9-slim-buster

WORKDIR /app

COPY requeriments.txt .
RUN pip install --no-cache-dir -r requeriments.txt

COPY . /app

CMD ["python", "scrap.py"]