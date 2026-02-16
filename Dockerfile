FROM ghcr.io/astral-sh/uv:python3.12-alpine

ENV TZ="Asia/Yekaterinburg"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH=".venv/bin:$PATH"

RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY src/ ./src/
COPY main.py ./

ENTRYPOINT []
CMD ["uv", "run", "main.py"]
