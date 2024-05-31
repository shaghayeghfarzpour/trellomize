import pytest
from datetime import datetime
from passlib.hash import sha256_crypt
from unittest.mock import MagicMock
from main import UserManager, User, Project, Task, TaskStatus, TaskPriority

@pytest.fixture
def user_manager():
    return UserManager()

@pytest.fixture
def user():
    return User("test@example.com", "testuser", sha256_crypt.hash("password"))

@pytest.fixture
def project(user):
    return Project("1", "Test Project", user.username)

@pytest.fixture
def task():
    return Task("Test Task", ["testuser"], TaskPriority.HIGH, TaskStatus.TODO, "Task description")

def test_register_user(user_manager):
    user_manager.register_user("test@example.com", "testuser", "password")
    assert len(user_manager.users) == 1
    assert user_manager.users[0].username == "testuser"

def test_login(user_manager, user):
    user_manager.users.append(user)
    logged_user = user_manager.login("testuser", "password")
    assert logged_user is not None
    assert logged_user.username == "testuser"

def test_create_project(user_manager, user):
    project = user_manager.create_project("1", user, "Test Project")
    assert project is not None
    assert project.title == "Test Project"
    assert project.creator == user.username

def test_create_task(project):
    project.create_task("Test Task", ["testuser"], TaskPriority.HIGH, TaskStatus.TODO, "Task description")
    assert len(project.tasks) == 1
    task = project.tasks[0]
    assert task.title == "Test Task"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.TODO
    assert task.description == "Task description"

def test_add_member_to_project(user_manager, project):
    user_manager.projects.append(project)
    user_manager.add_member_to_project(project, "newuser")
    assert "newuser" in project.members

def test_remove_member_from_project(user_manager, project):
    user_manager.projects.append(project)
    project.members.append("newuser")
    user_manager.remove_member_from_project(project, "newuser")
    assert "newuser" not in project.members

def test_add_comment(task):
    task.add_comment(User("test@example.com", "testuser", "password"), "Test comment")
    assert len(task.comments) == 1
    assert task.comments[0]["content"] == "Test comment"

def test_remove_comment(task):
    task.add_comment(User("test@example.com", "testuser", "password"), "Test comment")
    assert task.remove_comment("1")
    assert len(task.comments) == 0

def test_task_generate_table(task):
    task.add_comment(User("test@example.com", "testuser", "password"), "Test comment")

    # Mock the TaskPriority and TaskStatus to return their names as strings
    task.priority = TaskPriority.HIGH.name
    task.status = TaskStatus.TODO.name

    table = task.generate_table()
    assert table is not None

def test_task_generate_comments_table(task):
    task.add_comment(User("test@example.com", "testuser", "password"), "Test comment")
    comments_table = task.generate_comments_table()
    assert comments_table is not None

def test_get_projects_leading(user_manager, user):
    user_manager.projects = []  # پاکسازی لیست پروژه‌ها برای جلوگیری از تداخل داده‌ها
    project = Project("1", "Test Project", user.username)
    user_manager.projects.append(project)
    leading_projects = user_manager.get_projects_leading(user)
    assert len(leading_projects) == 1
    assert leading_projects[0].title == "Test Project"

def test_get_projects_working_on(user_manager, user):
    user_manager.projects = []  # پاکسازی لیست پروژه‌ها برای جلوگیری از تداخل داده‌ها
    project = Project("1", "Test Project", user.username, members=["testuser"])
    user_manager.projects.append(project)
    working_projects = user_manager.get_projects_working_on(user)
    assert len(working_projects) == 1
    assert working_projects[0].title == "Test Project"

def test_is_email_duplicate(user_manager, user):
    user_manager.users.append(user)
    assert user_manager.is_email_duplicate("test@example.com")
    assert not user_manager.is_email_duplicate("notindb@example.com")

def test_is_username_duplicate(user_manager, user):
    user_manager.users.append(user)
    assert user_manager.is_username_duplicate("testuser")
    assert not user_manager.is_username_duplicate("notindb")