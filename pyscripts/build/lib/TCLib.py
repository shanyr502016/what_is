""" TCLib """
import os
from corelib.Loggable import Loggable
from corelib.Constants import Constants
from corelib.GitUtilities import GitUtilities


class TCLib(Loggable):

    def __init__(self, args):
    
        super().__init__(__name__)

        self._arguments = args._arguments

        self.__git_provider = GitUtilities()


    def get_repo_changes(self, repo_path):

        self.__git_provider.set_repo_path(repo_path)

        repo = self.__git_provider.get_repo()

        last_commit_id = repo.head.commit.hexsha  

        self.log.info(f"Last Commit ID: {last_commit_id}")

        last_day_commit_id = self.__git_provider.get_last_day_commit(repo,days=1, hour=17, minute=30)

        if not last_day_commit_id:
            self.log.info("No commits found in the last day.")
            return [], []
        
        self.log.info(f"Changed files between {last_commit_id} and {last_day_commit_id}:")  
                
        file_changes = self.__git_provider.commit_file_changes(repo, last_commit_id, last_day_commit_id)
        
        commit_logs = self.__git_provider.commit_logs(repo, last_day_commit_id).splitlines()

        self.log.info("Retrieve Git Commit Logs...")

        # for commit_log in commit_logs:
        
        #     self.log.info(commit_log)

        # self.log.info('-----------------------------------------------------------------------------')
        
        # for file_change in file_changes:
            
        #     self.log.info(file_change)

        return commit_logs, file_changes

        