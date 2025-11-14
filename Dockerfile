# python 베이스
FROM python:3.10-slim

RUN useradd -m lambda

WORKDIR /app

# 의존성 복사
COPY pyproject.toml poetry.lock* /app/

RUN apt-get update && apt-get install --no-install-recommends -y curl && rm -rf /var/lib/apt/lists/*

# poetry 설치
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# 앱 코드 복사
COPY . /app/ 

USER lambda

ENV DJANGO_SETTINGS_MODULE=invest_manager.settings

# 포트
EXPOSE 8000

# ---- HEALTHCHECK 추가 ----
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
# --------------------------

# 실행
CMD ["uvicorn", "invest_manager.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
