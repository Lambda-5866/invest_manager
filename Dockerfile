# python 베이스
FROM python:3.10-slim

WORKDIR /app

# 의존성 복사
COPY pyproject.toml poetry.lock* /app/

# poetry 설치
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# 앱 코드 복사
COPY . /app/

USER lambda

# uvicorn 설치 (poetry 의존성에 포함되어 있으면 생략 가능)
RUN pip install --no-cache-dir uvicorn curl

ENV DJANGO_SETTINGS_MODULE=invest_manager.settings

# 포트
EXPOSE 8000

# ---- HEALTHCHECK 추가 ----
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
# --------------------------

# 실행
CMD ["uvicorn", "invest_manager.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
