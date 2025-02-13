import asyncio
import logging
import os
from pathlib import Path
from typing import Any, ClassVar, Literal

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult

DESCRIPTION: str = """
Run commands in a bash shell
* When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.
* You have access to a mirror of common linux and python packages via apt and pip.
* State is persistent across command calls and discussions with the user.
* To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
* Please avoid commands that may produce a very large amount of output.
* Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.
"""

logger = logging.getLogger(__name__)


class _BashSession:
    """A session of a bash shell."""

    _started: bool
    _process: asyncio.subprocess.Process

    command: str = "/bin/bash"
    _output_delay: float = 0.2  # seconds
    _timeout: float = 120.0  # seconds
    _sentinel: str = "<<exit>>"

    @staticmethod
    def _get_user_shell() -> tuple[str, list[str]]:
        """Get the user's default shell and its config file.
        Returns a tuple of (shell_path, config_file_path)."""
        import pwd
        import shutil

        # Get user's default shell from passwd database
        shell = os.getenv("HIDE_SHELL", pwd.getpwuid(os.getuid()).pw_shell)
        home = str(Path.home())

        # If shell path isn't available, fall back to bash
        if not shell or not os.path.exists(shell):
            shell = shutil.which("bash") or "/bin/bash"

        # Map common shells to their config files
        shell_configs = {
            "bash": [".bash_profile", ".bashrc"],
            "zsh": [".zprofile", ".zshrc"],
        }

        # Determine which shell we're dealing with
        shell_name = Path(shell).name
        config_files = shell_configs.get(shell_name, [])

        # Find the first existing config file
        configs = []
        for config in config_files:
            test_path = os.path.join(home, config)
            if os.path.exists(test_path):
                configs.append(test_path)

        return shell, configs

    def __init__(self):
        self._started = False
        # Get user's shell and config
        self.command, self._configs = self._get_user_shell()
        logger.debug(f"Using shell: {self.command}, configs: {self._configs}")

    async def start(self):
        if self._started:
            return

        logger.debug(f"Starting shell: {self.command}")

        # Standard handling for bash/zsh
        self._process = await asyncio.create_subprocess_shell(
            self.command,
            preexec_fn=os.setsid,
            shell=True,
            bufsize=0,
            limit=65536 * 8,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(Path.home()),
        )

        # Mark as started right after process creation but before config sourcing
        self._started = True
        logger.debug(f"Shell process started, return code: {self._process.returncode}")

        # Source config for bash/zsh
        for config in self._configs:
            logger.debug(f"Sourcing config file: {config}")
            result = await self.run(f"source {config}")
            logger.debug(f"Result of sourcing {config}: {result}")
            if result.output:
                logger.warning(
                    f"Output/errors while sourcing {config}:\n{result.output.strip()}"
                )

    def stop(self):
        """Terminate the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is None:
            self._process.terminate()
        self._started = False

    async def restart(self):
        """Restart the bash shell."""
        self.stop()
        await self.start()

    async def run(self, command: str):
        """Execute a command in the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            logger.warning(
                f"bash has previously exited with returncode {self._process.returncode}, restarting"
            )
            await self.restart()

        # we know these are not None because we created the process with PIPEs
        assert self._process.stdin
        assert self._process.stdout

        logger.debug(f"Running command: {command}")
        # send command to the process
        self._process.stdin.write(
            command.encode() + f"; echo '{self._sentinel}'\n".encode()
        )
        await self._process.stdin.drain()

        # read output from the process, until the sentinel is found
        try:
            logger.debug("Waiting for output...")
            async with asyncio.timeout(self._timeout):
                while True:
                    logger.debug("Checking for sentinel...")
                    await asyncio.sleep(self._output_delay)
                    # if we read directly from stdout/stderr, it will wait forever for
                    # EOF. use the StreamReader buffer directly instead.
                    output = (
                        self._process.stdout._buffer.decode()  # pyright: ignore[reportAttributeAccessIssue]
                    )
                    if self._sentinel in output:
                        logger.debug("Sentinel found!")
                        # strip the sentinel and break
                        output = output[: output.index(self._sentinel)]
                        break
        except asyncio.TimeoutError:
            logger.error("Timed out, restarting bash session")
            await self.restart()

            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and has been restarted",
            ) from None

        if output.endswith("\n"):
            output = output[:-1]

        logger.debug(f"Output: {output}")
        logger.debug("Clearing buffers...")
        # clear the buffers so that the next output can be read correctly
        self._process.stdout._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]
        logger.debug("Done!")

        return CLIResult(output=output)


class BashTool(BaseAnthropicTool):
    """
    A tool that allows the agent to run bash commands.
    The tool parameters are defined by Anthropic and are not editable.
    """

    _session: _BashSession | None
    name: ClassVar[Literal["bash"]] = "bash"

    def __init__(self):
        self._session = None
        super().__init__()

    async def __call__(
        self, command: str | None = None, restart: bool = False, **kwargs
    ):
        if restart:
            logger.debug("Restarting bash session")
            if self._session:
                self._session.stop()
            self._session = _BashSession()
            await self._session.start()

            return ToolResult(system="tool has been restarted.")

        if self._session is None:
            logger.debug("Starting bash session")
            self._session = _BashSession()
            await self._session.start()

        if command is not None:
            return await self._session.run(command)

        raise ToolError("no command provided.")

    def to_params(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": DESCRIPTION,
            "inputSchema": {
                "properties": {
                    "command": {
                        "description": "The bash command to run. Required unless the tool is being restarted.",
                        "type": "string",
                    },
                    "restart": {
                        "description": "Specifying true will restart this tool. Otherwise, leave this unspecified.",
                        "type": "boolean",
                    },
                },
                "type": "object",
            },
        }
