FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY app /app/app
COPY scripts /app/scripts

RUN pip install --upgrade pip && pip install .

COPY migrations /app/migrations

EXPOSE 5556

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5556"]
