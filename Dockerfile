# 1. 베이스 이미지
FROM python:3.12-slim

# 2. 환경 변수
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.7.1

# 3. 작업 디렉토리
WORKDIR /app

# 4. 의존성 설치
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# 5. 프로젝트 소스 복사
COPY . /app

# 6. 포트
EXPOSE 8000

# 7. 진입점 (프로덕션용)
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
