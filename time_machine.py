import subprocess
import os
import shutil
import random
from datetime import datetime, timedelta

def day_of_week(year, month, day):
    """Returns the day of the week for a given date using Zeller's Congruence."""
    if month < 3:
        month += 12
        year -= 1
    k = year % 100
    j = year // 100
    h = (day + (13*(month + 1)) // 5 + k + k//4 + j//4 + 5*j) % 7
    # h = 0 -> Saturday, 1 -> Sunday, 2 -> Monday, ..., 6 -> Friday
    names = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return h

def configure_git_user(name, email, date):
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = name
    env['GIT_AUTHOR_EMAIL'] = email
    env['GIT_AUTHOR_DATE'] = date
    env['GIT_COMMITTER_NAME'] = name
    env['GIT_COMMITTER_EMAIL'] = email
    env['GIT_COMMITTER_DATE'] = date
    return env

def create_local_repo(repo_path, remote_url, branch_name="master", start_date=None, num_days=365):
    os.makedirs(repo_path, exist_ok=True)
    os.chdir(repo_path)
    subprocess.run(["git", "init"])
    subprocess.run(["git", "checkout", "-b", branch_name])
    subprocess.run(["git", "remote", "add", "origin", remote_url])
    create_local_commits( remote_url, f"{branch_name}", start_date, num_days)
    
def create_local_commits(remote_url, branch_name="master", start_date=None, num_days=365):
    if start_date is None:
        start = datetime(2024, 1, 1, 12, 0, 0)
    else:
        start = start_date

    for i in range(num_days):
        current = start + timedelta(days=i)
        date_str = current.strftime("%Y-%m-%d %H:%M:%S")
        if day_of_week(current.year, current.month, current.day) in [0, 1]:
            commit_proc(0.2, 3, configure_git_user(username, useremail, date_str))
            continue
        
        commit_proc(0.8, 9, configure_git_user(username, useremail, date_str))
        if current.day == 1:
            push_to_remote(remote_url, branch_name)
    push_to_remote(remote_url, f"{branch_name}")
    
def commit_proc (rate, range,env):
    if random_binary(rate):
        random_number = random.randint(1, range)
        for i in range(random_number):
            subprocess.run(["git", "commit", "-m", f"Commit {i}", "--allow-empty"], env=env)

def push_to_remote(remote_url, branch_name="master"):
    subprocess.run(["git", "push", "-fu", remote_url, branch_name])

def random_binary(probability_of_1):
    """Returns 1 with given probability, 0 otherwise."""
    return 1 if random.random() < probability_of_1 else 0

if __name__ == "__main__":
    workspace = "workspace"
    remote_url = "git@github.com:bachnn92/dummy-2026.git"
    branch_name = "master"
    username = "bachnn92"
    useremail = "bachnn92@gmail.com"
    start = datetime(2026, 1, 1, 12, 0, 0)
    # end = datetime(2026, 12, 31, 12, 0, 0)
    end = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    days = (end - start).days + 1
    shutil.rmtree(workspace, ignore_errors=True)
    create_local_repo( workspace, remote_url, f"{branch_name}", start, days)
    
    

