from blitzkrieg.blitz_env_manager import BlitzEnvManager
from blitzkrieg.docker_manager import DockerManager
from blitzkrieg.ui_management.console_instance import console
import subprocess

class WorkspaceDockerManager:
    def __init__(self, blitz_env_manager: BlitzEnvManager):
        self.blitz_env_manager: BlitzEnvManager = blitz_env_manager
        self.docker_manager: DockerManager = DockerManager(blitz_env_manager=blitz_env_manager)
        self.console = console
        self.workspace_path = None
        self.workspace_name = None

    def build_workspace_container(self):
        try:
            self.console.handle_wait("Building workspace container...")
            self.workspace_path = self.blitz_env_manager.get_env_var_value_from_workspace_env_file('WORKSPACE_PATH')
            self.workspace_name = self.blitz_env_manager.get_env_var_value_from_workspace_env_file('WORKSPACE_NAME')
            self.console.handle_info(f"Running docker command to build workspace container on the following dir: {self.workspace_path}")
            self.console.execute_command(command=['docker-compose', 'build'], directory=self.workspace_path, message="Building workspace container...")
            self.console.handle_success(f"Built workspace container")
        except subprocess.CalledProcessError as e:
            return self.console.handle_error(f"Failed to build workspace container: {str(e)}")

    def start_workspace_container(self):
        try:
            self.console.execute_command(command=['docker-compose', 'up', '-d'], directory=self.workspace_path, message="Starting workspace container...")
            self.docker_manager.wait_for_container(container_name=f"{self.workspace_name}-postgres")
            self.docker_manager.wait_for_container(container_name=f"{self.workspace_name}-pgadmin")
            self.blitz_env_manager.add_env_var_to_workspace_file('WORKSPACE_PGADMIN_CONTAINER_NAME', f"{self.workspace_name}-pgadmin")
            self.blitz_env_manager.add_env_var_to_workspace_file('WORKSPACE_POSTGRES_CONTAINER_NAME', f"{self.workspace_name}-postgres")
            self.console.handle_success(f"Started all workspace containers")
        except subprocess.CalledProcessError as e:
            return self.console.handle_error(f"Failed to start workspace container: {str(e)}", error_object=e)
