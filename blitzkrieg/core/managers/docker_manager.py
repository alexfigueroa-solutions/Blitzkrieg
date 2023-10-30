from blitzkrieg.cli.logging_config import setup_logging
from blitzkrieg.cli.ui_utils import handle_error
from blitzkrieg.core.shared.command_runner import _run_command


ui_logger, backend_logger, console = setup_logging()
def is_container_ready(container_name: str) -> bool:
    try:
        status = _run_command(f"docker inspect --format='{{json .State.Status}}' {container_name}")
        if status == "running":
            console.print(f"[green]Container {container_name} is running![/green]")
            return True
        else:
            console.print(f"[yellow]Container {container_name} found, but not running.[/yellow]")
            console.print("Suggested Action: Run the container manually or check its configuration.")
            return False

    except Exception:
        handle_error(f"An unexpected error occurred while checking container {container_name}")
        return False
