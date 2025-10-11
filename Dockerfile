# -------- Build Stage --------
FROM python:3.10-slim AS build

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 시스템 의존성
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 의존성 설치
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# 소스 복사
COPY . /app

# collectstatic
RUN python manage.py collectstatic --noinput

# -------- Final Stage --------
FROM nginx:alpine

# Nginx 설정 복사
COPY ./deploy/nginx.conf /etc/nginx/conf.d/default.conf

# Django app 복사
COPY --from=build /app /app

# 포트
EXPOSE 16886

# CMD는 nginx + Uvicorn 함께 실행
CMD sh -c "uvicorn invest_manager.asgi:application --host 0.0.0.0 --port 16886 & nginx -g 'daemon off;'"
