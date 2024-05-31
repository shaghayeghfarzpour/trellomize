import os
import argparse
import json
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt
from rich.prompt import Confirm

class User:
    def __init__(self, username, email, password, activated=True):
        self.username = username
        self.email = email
        self.password = password
        self.activated = activated

    def activate(self):
        self.activated = True

    def deactivate(self):
        self.activated = False

class UserManager:
    def __init__(self, data_file):
        self.data_file = data_file
        self.users = self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, 'r') as file:
                users_data = json.load(file)
                return [User(**user) for user in users_data["users"]]
        except FileNotFoundError:
            return []

    def save_data(self):
        with open(self.data_file, 'r') as file:
            all_data = json.load(file)

        data = {
            "users": [user.__dict__ for user in self.users],
            "projects": all_data["projects"]
        }

        with open(self.data_file, 'w') as file:
            json.dump(data, file)

    def get_user_by_username(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def activate_user(self, username):
        user = self.get_user_by_username(username)
        if user:
            user.activate()
            console.print(f"User '{username}' has been activated successfully.")
            self.save_data()
        else:
            console.print(f"User '{username}' not found.")

    def deactivate_user(self, username):
        user = self.get_user_by_username(username)
        if user:
            user.deactivate()
            console.print(f"User '{username}' has been deactivated successfully.")
            self.save_data()
        else:
            console.print(f"User '{username}' not found.")

    def print_users_table(self):
        table = Table(title="Users")
        table.add_column("Username")
        table.add_column("Email")
        table.add_column("Active")

        for user in self.users:
            table.add_row(user.username, user.email, "Yes" if user.activated else "No")

        console.print(table)


if __name__ == "__main__":
    def create_admin(username, password):
        admin_file = "admin.txt"
        if os.path.exists(admin_file):
            print("Error: System administrator already exists.")
        else:
            with open(admin_file, "w") as file:
                file.write(f"Username: {username}\nPassword: {password}")
            print("System administrator created successfully.")
    parser = argparse.ArgumentParser(description="Manage system administrators.")
    parser.add_argument("action", choices=["create-admin","menu","purge-data"], help="Action to perform")
    parser.add_argument("--username", help="Username for system administrator")
    parser.add_argument("--password", help="Password for system administrator")

    args = parser.parse_args()

    if args.action == "create-admin":
        if args.username and args.password:
            create_admin(args.username, args.password)
        else:
            print("Error: Username and password are required for creating an administrator.")
    if args.action == "purge-data":
        confirmed = Confirm.ask("Are you sure you want to purge all saved data?")
        if confirmed:
            os.remove("data.json")
            print("All saved data has been purged.")
        else:
            print("Operation canceled.")
    console = Console()
    data_file = "data.json"
    user_manager = UserManager(data_file)

    while True:
        console.print("[bold green]Admin Menu[/bold green]")
        console.print("1. Activate User")
        console.print("2. Deactivate User")
        console.print("3. Print All Users")
        console.print("4. Exit")

        choice = Prompt.ask("Enter your choice: ", choices=["1", "2", "3", "4"])

        if choice == "1":
            username = Prompt.ask("Enter the username to activate: ")
            user_manager.activate_user(username)
        elif choice == "2":
            username = Prompt.ask("Enter the username to deactivate: ")
            user_manager.deactivate_user(username)
        elif choice == "3":
            user_manager.print_users_table()
        elif choice == "4":
            break
        else:
            console.print("Invalid choice. Please choose again.")
 