FROM python:3.11-buster as builder

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.7.1 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_CACHE_DIR=/tmp/poetry_cache \
  PATH="${PATH}:/root/.local/bin" 

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN touch README.md

RUN poetry install && rm -rf $POETRY_CACHE_DIR

COPY hl_research ./hl_research

RUN poetry install && poetry build 

FROM python:3.11-slim-buster as runtime

ENV PATH="/root/.local/bin:${PATH}"
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/dist /app/dist

RUN . /app/.venv/bin/activate && pip install /app/dist/*.whl

RUN mkdir /data

ENTRYPOINT ["/bin/bash", "-c", "source /app/.venv/bin/activate && scraper"]



