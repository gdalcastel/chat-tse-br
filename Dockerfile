FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY chatse ./chatse
COPY data ./data

RUN pip install --no-cache-dir .

ENV CHATSE_PORT=8000
EXPOSE 8000

CMD ["python", "-m", "chatse", "--http"]
