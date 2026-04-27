import subprocess
import os
import shutil
import random
import json
from datetime import datetime, timedelta

class TimeMachine:
    """A class to simulate Git repository creation and commit history."""

    def __init__(self, repo_path: str, remote_url: str |None, branch_name: str = "master", username: str | None = None, useremail: str | None = None):
        self.repo_path = repo_path
        self.remote_url = remote_url
        self.branch_name = branch_name
        self.username = username
        self.useremail = useremail

    @staticmethod
    def configure_git_user(name: str, email: str, date: str) -> dict[str, str]:
        """Configures environment variables for Git commits with the given user details and date."""
        env: dict[str, str] = os.environ.copy()
        env['GIT_AUTHOR_NAME'] = name
        env['GIT_AUTHOR_EMAIL'] = email
        env['GIT_AUTHOR_DATE'] = date
        env['GIT_COMMITTER_NAME'] = name
        env['GIT_COMMITTER_EMAIL'] = email
        env['GIT_COMMITTER_DATE'] = date
        return env

    @staticmethod
    def random_binary(probability_of_1: float) -> int:
        """Returns 1 with given probability, 0 otherwise."""
        return 1 if random.random() < probability_of_1 else 0
    
    def commit_proc(self, rate: float, range_val: int, env: dict[str, str]) -> None:
        """Creates a random number of empty commits with the given probability and range."""
        if self.random_binary(rate):
            random_number: int = random.randint(1, range_val)
            for i in range(random_number):
                subprocess.run(["git", "commit", "-m", f"Commit {i+1}", "--allow-empty"], env=env)

    def push_to_remote(self) -> None:
        """Pushes the current branch to the remote repository."""
        if self.remote_url:
            subprocess.run(["git", "push", "-fu", self.remote_url, self.branch_name])
                
    @staticmethod
    def day_of_week_index(year: int, month: int, day: int) -> int:
        """Returns the day of the week index for a given date using Zeller's Congruence.
        
        Returns 0 for Saturday, 1 for Sunday, ..., 6 for Friday.
        """
        if month < 3:
            month += 12
            year -= 1
        k: int = year % 100
        j: int = year // 100
        h: int = (day + (13*(month + 1)) // 5 + k + k//4 + j//4 + 5*j) % 7
        return h

    def create_local_repo(self, start_date: datetime | None = None, num_days: int = 365) -> None:
        """Creates a local Git repository, initializes it, and populates with commits."""
        self.original_dir = os.getcwd()  # Save original directory
        os.makedirs(self.repo_path, exist_ok=True)
        os.chdir(self.repo_path)
        subprocess.run(["git", "init"])
        subprocess.run(["git", "checkout", "-b", self.branch_name])
        if self.remote_url:
            subprocess.run(["git", "remote", "add", "origin", self.remote_url])
        
        
    def create_local_commits(self, start_date: datetime | None = None, num_days: int = 365) -> None:
        """Creates a series of local commits over the specified number of days, simulating activity."""
        if start_date is None:
            start: datetime = datetime(2026, 1, 1, 12, 0, 0)
        else:
            start: datetime = start_date

        for i in range(num_days):
            current: datetime = start + timedelta(days=i)
            date_str: str = current.strftime("%Y-%m-%d %H:%M:%S")
            if self.day_of_week_index(current.year, current.month, current.day) in [0, 1]:
                self.commit_proc(0.2, 3, self.configure_git_user(self.username, self.useremail, date_str))
                continue
            
            self.commit_proc(0.8, 9, self.configure_git_user(self.username, self.useremail, date_str))
            if current.day == 1:
                self.push_to_remote()
        self.push_to_remote()
    
    def create_matrix_commits(self, filename: str = "date_data.json") -> None:
        """Creates commits based on marked dates from date_data.json."""
        filepath = os.path.join(self.original_dir, filename) if hasattr(self, 'original_dir') else filename
        if not os.path.exists(filepath):
            print(f"File {filepath} not found.")
            return

        try:
            with open(filepath, 'r') as f:
                dates = json.load(f)
        except Exception:
            print(f"Error reading {filepath}")
            return

        dates.sort()
        for date_index, date_str in enumerate(dates, start=1):
            try:
                dt = datetime.fromisoformat(date_str)
                formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
                env = self.configure_git_user(self.username, self.useremail, formatted)
                num_commits = 4
                for i in range(num_commits):
                    subprocess.run(["git", "commit", "-m", f"Commit {date_index}", "--allow-empty"], env=env)
            except Exception:
                pass

if __name__ == "__main__":
    workspace = "workspace"
    remote_url = "git@github.com:bachnn92/helloworld-2020.git"
    branch_name = "master"
    username = "Bach Nguyen Ngoc"
    useremail = "bachnn92@gmail.com"
    start = datetime(2020, 11, 18, 12, 0, 0)
    end = datetime(2020, 12, 31, 12, 0, 0)
    # end: datetime = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    days: int = (end - start).days + 1
    
    original_dir = os.getcwd()
    shutil.rmtree(workspace, ignore_errors=True)
    tm = TimeMachine(repo_path=workspace, remote_url=remote_url, branch_name=branch_name, username=username, useremail=useremail)
    tm.create_local_repo(start, days)
    # tm.create_local_commits(start, days)
    tm.create_matrix_commits()
    tm.push_to_remote()

