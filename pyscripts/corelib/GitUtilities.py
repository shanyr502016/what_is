""" GitUtilities """

import os
from datetime import datetime, timedelta
from git import Repo, InvalidGitRepositoryError, NoSuchPathError
from corelib.Loggable import Loggable

"""
GitUtilities supports to maintain git features
"""
class GitUtilities(Loggable):

    def __init__(self):

        super().__init__(__name__)
        
        self._repo_path = None
        
    def set_repo_path(self, repo_path):
        
        self._repo_path = repo_path
        
    def get_repo_path(self, repo_path):
    
        return self._repo_path
        
    def get_repo(self):
        try:
            repo = Repo(self._repo_path)
            # Perform operations on the repository if initialization is successful
            return repo
        except InvalidGitRepositoryError:
            self.log.error(f"Invalid Git repository at {self._repo_path}.")
            # Handle the case where the repository is invalid or doesn't exist
            return 1
        except Exception as e:
            self.log.error(f"An error occurred: {e}")
            # Handle other exceptions or errors that might occur during initialization
            return 1
            
    def get_last_day_commit(self, repo, days=1, hour=0, minute=0, second=0, microsecond=0):
        """ Get last day commit """
    
        try:        
            current_date = datetime.utcnow()
            #last_commit_id = repo.head.commit.hexsha        
            last_day = datetime.utcnow().replace(hour=hour, minute=minute, second=second, microsecond=microsecond) - timedelta(days=days)        
            commits = list(repo.iter_commits(until=current_date, since=last_day))

            last_day_commit_id = None
            
            for commit in commits:                
                last_day_commit_id = commit       
            given_commit = repo.commit(last_day_commit_id)
            if last_day_commit_id:
                if given_commit.parents:
                    previous_commit = given_commit.parents[0]  # Assuming a linear history, accessing the first parent            
                    last_day_commit_id = previous_commit.hexsha
                    self.log.info(f"Last Day Commit ID: {last_day_commit_id}")
                    #self.log.info(f"Changed files between {last_commit_id} and {last_day_commit_id}:")   
                return last_day_commit_id
            else:
                return last_day_commit_id
        except InvalidGitRepositoryError as e:
            self.log.error(f"Invalid Git repository: {e}")
            return 1
        except NoSuchPathError as e:
            self.log.error(f"Repository path not found: {e}")
            return 1
        except Exception as e:
            self.log.error(f"An error occurred: {e}")
            return 1
        
        
    def commit_file_changes(self, repo, last_commit_id, specific_commit_id): 
        """
        Changed files between two specific commits using GitPython, you can utilize the git.diff() method.
        
        The --name-only flag specifies that you want to retrieve only the names of the changed files.
        
        This script uses repo.git.diff() to obtain the list of changed files between the two specified commits. 
        Adjust the commit IDs to match the commits you want to compare in your repository.
        """
    
        # Get the list of changed files between two commits
        commit_changes = repo.git.diff(last_commit_id, specific_commit_id,'--name-only').splitlines()
        
        return commit_changes
        
    def commit_logs(self, repo, specific_commit_id):
        """
        The repo.git.log() method in GitPython allows you to retrieve commit logs within a specific commit range.
        If you want to fetch commit logs from a specific commit to the HEAD (the latest commit on the current branch)
        """        
        # Get the commit log from a specific commit to the last commit
        commit_logs = repo.git.log(f"{specific_commit_id}..HEAD", "--oneline")
        
        return commit_logs
    
        
        
    def git_reset(self, repo_path):
        """repo.git.reset('--hard') performs a hard reset, discarding all changes in the working directory to match the state of the HEAD commit."""
    
        try:
            repo = Repo(repo_path)
            # Reset changes
            repo.git.reset('--hard')  # Resets all changes to match the HEAD commit
            repo.git.clean('-xdf') # Remove untracked files and directories
            
        except InvalidGitRepositoryError as e:
            self.log.error(f"Invalid Git repository: {e}")
        except NoSuchPathError as e:
            self.log.error(f"Repository path not found: {e}")
        except Exception as e:
            self.log.error(f"An error occurred: {e}")
            
    def git_pull(self, repo_path):
        """        
        repo.git.pull() fetches changes from the remote repository and performs a merge into the current branch.
        """    
        try:
            repo = Repo(repo_path)
            # Pull changes from remote
            repo.git.pull()  # Fetches changes from the remote and merges them into the current branch
        except InvalidGitRepositoryError as e:
            self.log.error(f"Invalid Git repository: {e}")
        except NoSuchPathError as e:
            self.log.error(f"Repository path not found: {e}")
        except Exception as e:
            self.log.error(f"An error occurred: {e}")