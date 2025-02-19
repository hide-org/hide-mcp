FROM sweb.eval.x86_64.sympy__sympy-14248:latest
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY src /hide-mcp/src
COPY pyproject.toml /hide-mcp/pyproject.toml
COPY uv.lock /hide-mcp/uv.lock
COPY README.md /hide-mcp/README.md

RUN uv --directory /hide-mcp sync

ENTRYPOINT ["uv", "--directory", "/hide-mcp", "run", "hide-mcp", "server"]
