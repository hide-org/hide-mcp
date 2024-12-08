import click
import e2b_code_interpreter as e2b


def create_sandbox(timeout: int = 300) -> e2b.Sandbox:
    return e2b.Sandbox(timeout=timeout)


def run_code(sbx: e2b.Sandbox, code: str) -> e2b.Execution:
    return sbx.run_code(code)


def upload_file(sbx: e2b.Sandbox, src: str, dst: str) -> None:
    with open(src, "rb") as f:
        sbx.files.write(dst, f)


def run_cmd(sbx: e2b.Sandbox, cmd: str) -> e2b.CommandResult:
    return sbx.commands.run(cmd)


def run_background_cmd(sbx: e2b.Sandbox, cmd: str) -> e2b.CommandHandle:
    return sbx.commands.run(cmd, background=True, timeout=0)


def get_url(sbx: e2b.Sandbox, port: int) -> str:
    return f"https://{sbx.get_host(port)}"


def kill_sandbox(sbx: e2b.Sandbox) -> bool:
    return sbx.kill()


def kill_all() -> bool:
    result = []
    for info in e2b.Sandbox.list():
        sbx = e2b.Sandbox.connect(info.sandbox_id)
        result.append(sbx.kill())
    return all(result)


def print_logs(handle: e2b.CommandHandle) -> None:
    for stdout, stderr, _ in handle:
        if stdout:
            click.echo(stdout)
        if stderr:
            click.echo(stderr, err=True)


def setup_hide_mcp(sbx: e2b.Sandbox, verbose: bool = False) -> str:
    try:
        if verbose:
            click.echo("Installing uv...")
        run_cmd(sbx, "curl -LsSf https://astral.sh/uv/install.sh | sh")

        if verbose:
            click.echo("Cloning hide-mcp repository...")
        run_cmd(sbx, "git clone https://github.com/hide-org/hide-mcp.git")

        if verbose:
            click.echo("Installing hide-mcp...")
        run_cmd(sbx, "~/.local/bin/uv --directory ~/hide-mcp sync")

        if verbose:
            click.echo("Running hide-mcp in background...")
        handle = run_background_cmd(
            sbx,
            "~/.local/bin/uv --directory ~/hide-mcp run hide-mcp server --transport sse",
        )

        url = f"https://{sbx.get_host(8945)}/sse"

        if verbose:
            click.echo(f"Hide MCP is running at: {url}")
        return url
    except Exception as e:
        if verbose:
            # TODO: replace with logger?
            click.echo(f"Error setting up hide-mcp: {e}", err=True)
        kill_sandbox(sbx)
        raise
