FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.6.1
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 의존성 설치
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

# 소스 복사
COPY . /app

# 6. 포트
EXPOSE 16886

# 7. 진입점 (프로덕션용)
CMD ["uvicorn", "invest_manager.asgi:application", "--host", "0.0.0.0", "--port", "16886", "--reload"]
