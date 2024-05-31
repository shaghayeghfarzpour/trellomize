from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
import uuid
from datetime import datetime, timedelta
from enum import Enum
import json
from passlib.hash import sha256_crypt
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from loguru import logger

console = Console()
logger.add("app.log", rotation="500 MB", level="INFO")

class TaskStatus(Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TaskPriority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Task:

    def __init__(self, title, assignees, priority=TaskPriority.LOW, status=TaskStatus.BACKLOG, description=""):
        self.id = uuid.uuid4().hex
        self.title = title
        self.assignees = assignees
        self.priority = priority
        self.status = status
        self.start_time = datetime.now()
        self.end_date = datetime.now() + timedelta(days=1)
        self.comments = []
        self.description = description

    def add_comment(self, user, content):
        comment = {
            "index": len(self.comments) + 1,
            "author": user.username,
            "time": datetime.now(),
            "content": content
        }
        self.comments.append(comment)
    def remove_comment(self,comment_id):
        
        updated_comments = [comment for comment in self.comments if str(comment["index"]) != comment_id]
        if len(updated_comments) < len(self.comments):
            self.comments = updated_comments
            return True
        return False

    def add_member(self, username):
        self.assignees.append(username)

    def remove_assignee(self, username):
        if username in self.assignees:
            self.assignees = [assignee for assignee in self.assignees if assignee != username]
            console.print(f"[green]User {username} removed from the task![/green]")
            return
        console.print("[red]Error: User not found in the task.[/red]")

    def show_assignee(self):
        assignees_str = ', '.join(assignee.username for assignee in self.assignees)
        return f"Assignees: {assignees_str}"

    def get_assignee(self):
        return self.assignees

    def is_comment_exist(self, comment_id):
        for comment in self.comments: 
            if str(comment["index"]) == comment_id:
                return True
        return False

    def generate_comments_table(self):
        table = Table(title="Comments")
        table.add_column("Index")
        table.add_column("Author")
        table.add_column("Time")
        table.add_column("Content")

        for index, comment in enumerate(self.comments, start=1):
            table.add_row(
                str(index),
                comment["author"],
                str(comment["time"]),
                comment["content"]
            )
        return table

    def generate_table(self):
        table = Table(title="Task Details")
        table.add_column("Attribute")
        table.add_column("Value")
        table.add_row("ID", str(self.id))
        table.add_row("Title", self.title)
        table.add_row("Assignees", ', '.join(assignee for assignee in self.assignees))
        table.add_row("Priority", self.priority)
        table.add_row("Status", self.status)
        table.add_row("Start Date", str(self.start_time))
        table.add_row("End Date", str(self.end_date))
        table.add_row("Description", self.description)
        comments_str = ', '.join(
            [f"{comment['author']} ({comment['time']}): {comment['content']}" for comment in self.comments])
        table.add_row("Comments", comments_str)
        return table


class User:
    def __init__(self, email, username, password, activated=True):
        self.email = email
        self.username = username
        self.password = password
        self.activated = activated


class Project:
    def __init__(self, project_id, title, creator, members=None, tasks=None):
        self.project_id = project_id
        self.title = title
        self.creator = creator
        self.members = members if members is not None else [creator]
        self.tasks = []

    def add_member(self, member):
        self.members.append(member)

    def remove_member(self, member):
        if member in self.members:
            self.members.remove(member)

    def get_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def is_member_exist(self,member):
        return member in self.members
    
    def create_task(self, title, assignees, priority=TaskPriority.LOW, status=TaskStatus.BACKLOG, description=""):
        task = Task(title, assignees, priority, status, description)
        print(task.get_assignee())
        self.tasks.append(task)
        logger.info(f"Task created: {task.title} by {self.creator}")
        console.print("[green]Task created successfully![/green]")

    def remove_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                self.tasks.remove(task)
                console.print("[green]Task deleted successfully![/green]")
                return
        console.print("[red]Error: Task not found.[/red]")

    def get_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None


class UserManager:
    def __init__(self):
        self.users = []
        self.projects = []
        self.load_data()
        self.project_id_counter = 1

    def register_user(self, email, username, password):
        if self.is_email_duplicate(email) or self.is_username_duplicate(username):
            console.print("[red]Error: Duplicate email or username. Please choose another one.[/red]")
            return
        hashed_password = sha256_crypt.hash(password)
        user = User(email, username, hashed_password)
        self.users.append(user)
        self.save_data()
        console.print("[green]User registered successfully![/green]")
        logger.info(f"User registered: {username}")

    def is_email_duplicate(self, email):
        return any(user.email == email for user in self.users)

    def is_username_duplicate(self, username):
        return any(user.username == username for user in self.users)

    def login(self, username, password):
        for user in self.users:
            if user.username == username:
                if user.activated:
                    if sha256_crypt.verify(password, user.password):
                        logger.info(f"User logged in: {username}")
                        return user
                    else:
                        logger.warning(f"Failed login attempt for user: {username}")
                        return None
                else:
                    logger.warning(f"Attempted login for disabled user: {username}")
                    console.print("[red]Error: user was disabled![/red]")
                    return -1
        logger.warning(f"Invalid username: {username}")
        return None

    def create_project(self, id, user, title):
        project = Project(id, title, user.username)
        self.projects.append(project)
        self.save_data()
        console.print("[green]Project created successfully![/green]")
        logger.info(f"Project created: {title} by {user.username}")
        return project
    
    def is_project_exist(self,title):
        for project in self.projects:
            if project.title == title:
                return True
        return False

    def add_member_to_project(self, project, username):
        project.add_member(username)
        logger.info(f"User {username} added to project: {project.title}")
        console.print(f"[green]User {username} added to the project![/green]")
        self.save_data()
        return

    def remove_project(self, project):
        self.projects.remove(project)
        logger.info(f"Project deleted: {project.title}")
        console.print("[green]Project deleted successfully![/green]")

    def remove_member_from_project(self, project, username):
        if username in project.members:
            project.remove_member(username)
            logger.info(f"User {username} removed from project: {project.title}")
            console.print(f"[green]User {username} removed from the project![/green]")
        else:
            logger.warning(f"Failed to remove user {username} from project: {project.title}. User not found.")
            console.print("[red]Error: User not found in the project.[/red]")

    def load_data(self):
        try:
            with open("data.json", 'r') as file:
                users_data = json.load(file)
                self.users = [User(**user) for user in users_data["users"]]
                self.projects = [Project(**project) for project in users_data["projects"]]
        except FileNotFoundError:
            return []

    def save_data(self):
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} is not JSON serializable")

        def serialize_project(project):
            serialized_project = project.__dict__.copy()
            serialized_project["tasks"] = [task.__dict__ for task in project.tasks]
            return serialized_project

        data = {
            "users": [user.__dict__ for user in self.users],
            "projects": [serialize_project(project) for project in self.projects]
        }
        with open("data.json", "w") as file:
            json.dump(data, file, default=serialize_datetime)

    def is_username_exists(self, username):
        for user in self.users:
            if user.username == username:
                return True
        return False

    def get_projects_leading(self, user):
        leading_projects = []
        print(user)
        for project in self.projects:
            if project.creator == user.username:
                leading_projects.append(project)
        return leading_projects

    def get_projects_working_on(self, user):
        working_projects = []
        for project in self.projects:
            if user.username in project.members:
                working_projects.append(project)
        return working_projects


def view_tasks(project):
    table = Table(title=f"Tasks in Project: {project.title}")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="cyan")
    table.add_column("Priority", style="cyan")
    table.add_column("Status", style="cyan")
    table.add_column("Assignees", style="cyan")
    table.add_column("Description", style="cyan")

    for task in project.tasks:
        table.add_row(
            task.id,
            task.title,
            task.priority,
            task.status,
            ', '.join(assignee for assignee in task.assignees),
            task.description
        )
    console.print(table)


def main():
    user_manager = UserManager()
    current_user = None

    while True:

        if not current_user:

            console.print("[bold]Welcome to the Application![/bold]")
            choice = Prompt.ask("Select an option: (1) Register, (2) Login, (3) Quit", choices=["1", "2", "3"])

            if choice == "1":
                while True:
                    email = Prompt.ask("Enter your email:")
                    if len(email) >= 10 and "@" in email:
                        break
                    else:
                        console.print("[red]Error: Email must be at least 10 characters long and contain '@'.[/red]")
                
                username = Prompt.ask("Enter your username:")
                password = Prompt.ask("Enter your password:", password=True)
                user_manager.register_user(email, username, password)

            elif choice == "2":
                username = Prompt.ask("Enter your username:")
                password = Prompt.ask("Enter your password:", password=True)
                logged_user = user_manager.login(username, password)
                if logged_user != -1:
                    if logged_user:
                        current_user = logged_user
                        console.print(f"[green]Logged in successfully as {current_user.username}![/green]")
                    else:
                        console.print("[red]Error: Invalid username or password.[/red]")
                else:
                    continue            

            elif choice == "3":
                break

        else:

            console.print(f"[bold]Welcome, {current_user.username}![/bold]")
            choice = Prompt.ask("Select an option: (1) Create Project, (2) View Projects (3) Logout",
                                choices=["1", "2", "3"])

            if choice == "1":
                project_id = input("Enter project ID: ")
                project_name = input("Enter project name: ")
                if user_manager.is_project_exist(project_name):
                    console.print("[red]Error: Project with this name already exists[/red]")
                    continue

                project = user_manager.create_project(project_id, current_user, project_name)

                while True:
                    action = Prompt.ask(
                        "Select an action: (1) Add Member, (2) Remove Member, (3) Remove Project (4) Back",
                        choices=["1", "2", "3", "4"])

                    if action == "1":
                        username = Prompt.ask("Enter username to add to the project:")
                        flag = False
                        for user in user_manager.users:
                            if username == user.username:
                                user_manager.add_member_to_project(project, username)
                                flag = True
                        if flag == False:
                            console.print("[red]Error: user not found[/red]")
                            
                    elif action == "2":
                        username = Prompt.ask("Enter username to remove from the project:")
                        user_manager.remove_member_from_project(project, username)        

                    elif action == "3":
                        user_manager.remove_project(project)

                    elif action == "4":
                        break

            elif choice == "2":
                leading_projects = user_manager.get_projects_leading(current_user)
                working_projects = user_manager.get_projects_working_on(current_user)
                leading_table = Table(title="Projects Leading")
                leading_table.add_column("ID", style="cyan")
                leading_table.add_column("Title", style="green")

                for project in leading_projects:
                    leading_table.add_row(str(project.project_id), project.title)

                console.print(leading_table)

                # Display working projects in a table
                working_table = Table(title="Projects Working On")
                working_table.add_column("ID", style="cyan")
                working_table.add_column("Title", style="green")

                for project in working_projects:
                    working_table.add_row(str(project.project_id), project.title)

                console.print(working_table)

                projects = [project.title for project in working_projects]
                project_name = Prompt.ask("Select a project:", choices=projects)
                selected_project = next((project for project in working_projects if project.title == project_name), None)

                
                if selected_project:
                    while True:
                        view_tasks(selected_project)
                        #project menu
                        action = Prompt.ask(
                            "Select an action: (1) Create Task, (2) view Tasks (3) Back",
                            choices=["1", "2", "3"])

                        if action == "1":
                            if current_user.username == selected_project.creator:
                                task_title = Prompt.ask("Enter task title:")
                                task_description = Prompt.ask("Enter task description:")
                                assignees = []
                                while True:
                                    assignee_username = Prompt.ask(
                                        "Enter username of assignee (or type 'done' to finish adding assignees):")
                                    if assignee_username == "done":
                                        break
                                    user = next(
                                        (user for user in user_manager.users if user.username == assignee_username),
                                        None)
                                    if user:
                                        assignees.append(user.username)
                                    else:
                                        console.print("[red]Error: User not found.[/red]")

                                task_priority = Prompt.ask("Enter task priority (CRITICAL, HIGH, MEDIUM, LOW):",
                                                           choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], default="LOW")
                                task_status = Prompt.ask("Enter task status (BACKLOG, TODO, DOING, DONE, ARCHIVED):",
                                                         choices=["BACKLOG", "TODO", "DOING", "DONE", "ARCHIVED"], default="BACKLOG")

                                selected_project.create_task(task_title, assignees, task_priority, task_status, task_description)
                                logger.info(f"{task_title} by {current_user.username}")
                                user_manager.save_data()

                            else:
                                print(current_user, selected_project.creator)
                                console.print("[red]Error: You are not the project manager![/red]")


                        elif action == "2":
                            while True:
                                task_id = Prompt.ask("Select a task ID to view details (or type 'exit' to go back):")
                                if task_id == "exit":
                                    break
                                for task in selected_project.tasks:
                                    if task.id == task_id:
                                        if current_user.username != selected_project.creator:
                                            if current_user.username not in task.assignees:
                                                console.print(
                                                    "[bold red]Error:[/] You are not an assignee of this task. Access denied.")
                                                break

                                        console.print(task.generate_table())
                                        while True:
                                            console.print("[bold]Select an attribute to modify:[/bold]")
                                            console.print("1. Change Title")
                                            console.print("2. Add Assignee")
                                            console.print("3. Change Priority")
                                            console.print("4. Change Status")
                                            console.print("5. Add comment")
                                            console.print("6. delete Comment")
                                            console.print("7. Back to main menu")

                                            choice = Prompt.ask("Enter your choice: ",
                                                                choices=["1", "2", "3", "4", "5", "6", "7"])

                                            if choice == "1":
                                                new_title = Prompt.ask("Enter new title: ")
                                                task.title = new_title
                                                logger.info(f"Task title changed to '{new_title}' by user '{current_user.username}'")
                                            elif choice == "2":
                                                if current_user.username != selected_project.creator:
                                                    console.print(
                                                        "[bold red]Error:[/] Only the project creator can assign tasks to users. Access denied.")
                                                    continue
                                                new_username = Prompt.ask("Enter new username: ")
                                                if user_manager.is_username_exists(new_username):
                                                    if selected_project.is_member_exist(new_username):
                                                      task.add_member(new_username)
                                                      logger.info(f"User '{new_username}' added to task '{task.title}' by project creator '{current_user.username}'")
                                                    else:
                                                        console.print("[bold red]Error: user already exist!.[/]")
                                                else:
                                                    console.print(
                                                        "[bold red]Error:[/] user not found.")

                                                pass
                                            elif choice == "3":
                                                new_task_priority = Prompt.ask(
                                                    "Enter task priority (CRITICAL, HIGH, MEDIUM, LOW):",
                                                    choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
                                                task.priority = new_task_priority
                                                logger.info(f"Task priority changed to '{new_task_priority}' by user '{current_user.username}'")
                                                pass
                                            elif choice == "4":
                                                new_task_status = Prompt.ask(
                                                    "Enter task status (BACKLOG, TODO, DOING, DONE, ARCHIVED):",
                                                    choices=["BACKLOG", "TODO", "DOING", "DONE", "ARCHIVED"])
                                                task.status = new_task_status
                                                logger.info(f"Task status changed to '{new_task_status}' by user '{current_user.username}'")

                                                pass
                                            elif choice == "5":
                                                comments_table = task.generate_comments_table()
                                                console.print(comments_table)
                                                for task in selected_project.tasks:
                                                    if task.id == task_id:
                                                        comment_content = Prompt.ask("Enter comment:")
                                                        task.add_comment(current_user, comment_content)
                                                        user_manager.save_data()
                                                        console.print("[green]Comment added successfully![/green]")
                                                        user_manager.save_data()
                                                        logger.info(f"Comment added to task '{task.title}' by user '{current_user.username}'")

                                            elif choice == "6":
                                                comments_table = task.generate_comments_table()
                                                console.print(comments_table)
                                                comment_id=Prompt.ask("select a comment to remove:")
                                                if task.is_comment_exist(comment_id):
                                                    if task.remove_comment(comment_id):
                                                        print("Comment removed successfully.")
                                                        logger.info(f"Comment removed from task '{task.title}' by user '{current_user.username}'")
                                                else:
                                                    print("Comment not found.")
                                                pass
                                            elif choice == "7":
                                                user_manager.save_data()
                                                break

                                            console.print("Task attributes updated successfully!")
                                    else:
                                        console.print("")

                        elif action == "3":
                            break

            elif choice == "3":
                current_user = None
                
if __name__ == "__main__":
    main()