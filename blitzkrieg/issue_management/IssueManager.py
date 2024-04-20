import uuid
from datetime import datetime
from blitzkrieg.project_management.db.connection import get_db_session
from blitzkrieg.project_management.db.services.issues_service import IssueService
from blitzkrieg.project_management.db.services.project_service import ProjectService
import os
from rich import print as rprint

class IssueManager:
    def __init__(self, database_manager, file_manager, console_interface, markdown_manager):
        self.database_manager = database_manager
        self.file_manager = file_manager
        self.console_interface = console_interface
        self.markdown_manager = markdown_manager
        self.error_manager = console_interface.error_manager

    def process_issues(self, issues_dir, project_name):
        files = self.file_manager.list_files_with_suffix(issues_dir, '.md')
        table = self.console_interface.configure_table()

        with get_db_session() as session:
            for file in files:
                file_path = os.path.join(issues_dir, file)
                try:
                    self.handle_issue_file(file_path, project_name, session, table)
                except Exception as e:
                    self.console_interface.console.print(f"Error in file {file}: {e}", style="error")
                    table.add_row(file, "Error", "[red]Failed[/red]")

            self.synchronize_database_issues_to_markdown(issues_dir, project_name, session, table)

        self.console_interface.console.print(table)
        self.console_interface.console.print("Issue processing completed.", style="success")

    def handle_issue_file(self, file_path, project_name, session, table):
        try:
            issue_id, title, content = self.extract_file_details(file_path)
            action, status = "", ""

            if not self.verify_uuid_format(issue_id):
                new_uuid = str(uuid.uuid4())
                self.file_manager.prepend_uuid_to_file(file_path, new_uuid)
                issue_id = new_uuid
                action, status = "UUID Prepended", "[green]New UUID Added[/green]"

            issue_exists, issue_in_db = self.check_issue_presence_in_database(issue_id, session)

            if action == "" and status == "":
                if not issue_exists:
                    action, status = self.manage_new_issue_creation(file_path, issue_id, title, content, project_name, session)
                elif issue_exists:
                    action, status = self.update_issue_if_modified(file_path, issue_id, title, content, issue_in_db, session)

            table.add_row(file_path, action, status)
        except Exception as e:
            self.error_manager.display_error(f"Error processing file {file_path}: {e}", exception=e)
            table.add_row(file_path, "Error", "[red]Failed[/red]")

    def extract_file_details(self, file_path):
        try:
            content = self.file_manager.read_file(file_path)
            lines = content.split('\n')
            id_line, title = lines[:2]
            content = '\n'.join(lines[2:])
            return id_line.strip(), title.strip(), content.strip()
        except Exception as e:
            self.error_manager.display_error(f"Error extracting file details: {e}", exception=e)
            return None, None, None

    def verify_uuid_format(self, uuid_to_test, version=4):
        try:
            uuid_obj = uuid.UUID(uuid_to_test, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == uuid_to_test

    def check_issue_presence_in_database(self, issue_id, session):
        issue = IssueService().get_issues(session, issue_id)
        return issue is not None, issue

    def manage_new_issue_creation(self, file_path, issue_id, title, content, project_name, session):
        try:
            issue = self.generate_issue_metadata(issue_id, title, content, project_name)
            created_issue = self.save_issue_to_database(issue, project_name, session)
            if created_issue:
                self.file_manager.prepend_uuid_to_file(file_path, issue_id)
                self.error_manager.display_success(f"New issue created: ID {issue_id}", emoji=':check_mark_button:')
                return "Created", "[green]New Issue Created[/green]"
            else:
                raise Exception("Failed to create new issue in database.")
        except Exception as e:
            self.error_manager.display_error(f"Error creating new issue: {e}", exception=e)
            return "Error", "[red]Error Creating Issue[/red]"

    def generate_issue_metadata(self, issue_id, title, content, project_name):
        shorthand_tag = ''.join(ch for ch in project_name if ch not in 'aeiou').lower()[:4]
        branch_name = f'{shorthand_tag}{title[1:].replace(" ", "-").lower() if title.startswith("#") else title.replace(" ", "-").lower()}'
        return {'id': issue_id, 'title': title.replace('#', '').strip(), 'branch_name': branch_name, 'content': content}

    def save_issue_to_database(self, issue, project_name, session):
        index = IssueService().get_next_index(session)
        project = ProjectService().get_project_by_name(session, project_name)
        IssueService().create_issue(
            session=session,
            id=issue['id'],
            title=issue['title'],
            index=index,
            branch_name=issue['branch_name'],
            description=issue['content'],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_id=project.id
        )

    def update_issue_if_modified(self, file_path, issue_id, title, content, existing_issue, session):
        title_changed = existing_issue.title != title
        content_changed = existing_issue.description != content
        if title_changed or content_changed:
            existing_issue.title = title if title_changed else existing_issue.title
            existing_issue.description = content if content_changed else existing_issue.description
            existing_issue.updated_at = datetime.now()
            session.commit()
            self.file_manager.write_file(file_path, f'{issue_id}\n{title}\n\n{content}')
            return "Updated", "[orange]Updated in DB & Markdown[/orange]"
        return "Unchanged", "[blue]No Changes[/blue]"

    def synchronize_database_issues_to_markdown(self, issues_dir, project_name, session, table):
        issues = IssueService().get_all_issues(session)
        markdown_files = self.file_manager.list_files_with_suffix(issues_dir, '.md')
        markdown_ids = [self.extract_file_details(os.path.join(issues_dir, f))[0] for f in markdown_files]

        for issue in issues:
            if str(issue.id) not in markdown_ids:
                file_name = f"{self.convert_title_to_snakecase(issue.title)}.md"
                file_path = os.path.join(issues_dir, file_name)
                self.file_manager.write_file(file_path, f'{issue.id}\n{issue.title}\n\n{issue.description}')
                table.add_row(file_name, "Synced", "[green]Markdown File Created[/green]")

    def convert_title_to_snakecase(self, title):
        snake_case_title = title.replace('-', ' ').replace('#', '').replace(' ', '_').replace(":", "").lower()
        return snake_case_title.lstrip('_')

    def rewrite_markdown_file(issue, file_path):
        with open(file_path, 'w') as file:
            file.write(f'{issue.id}\n')
            file.write(f'{issue.title}\n\n')
            file.write(issue.description)

    def check_uuid_or_new_issue(self, uuid_to_test, session):
        if not uuid_to_test or not self.markdown_manager.verify_uuid_format(uuid_to_test):
            return False, True  # Invalid UUID, but might be a new issue
        exists, _ = self.check_issue_presence_in_database(uuid_to_test, session)
        return exists, False  # Valid UUID and issue exists

    def generate_markdown_from_db_entry(self, issue, issues_dir):
        snakecase_title = self.convert_title_to_snakecase(issue.title)
        file_name = f"{snakecase_title}.md"
        file_path = os.path.join(issues_dir, file_name)
        with open(file_path, 'w') as file:
            file.write(f'{issue.id}\n')
            file.write(f'{issue.title}\n\n')
            file.write(issue.description)
        rprint(f"[green]Markdown file created for issue {issue.id} ({file_name})[/green]")