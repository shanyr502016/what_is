"""CreatePackage"""
import os
from corelib.Loggable import Loggable
from corelib.GitUtilities import GitUtilities

class CreatePackage(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
        """
        Set arguments from CreatePackage
        """         
        self.__arguments = args # Set arguments from DynamicImporter
        
        self.__environment = args._environment # Get the Environment Specific Values from config json
        
        self.__environment_provider = args._environment_provider # Get the Environment Provider method. Reusable method derived
    
        self.__module_name = args._module_name # Module name from user command line (Only Module (classname))
        
        self.__module = args._arguments.module # Module name with submodule from user command line (full name)
        self.__module_label = self.__module # Module label    
        
        self.__git_provider = GitUtilities()
        
        self._workspace = None
        
        self._processes = []
        self._processesResult = []
        
        self.__remote_execution = False
  
        
        
    def delta(self):
        """ Delta Package Creation """

        if 'workspace' in self.__arguments._arguments:
            self._workspace = getattr(self.__arguments._arguments, 'workspace')
            self.log.info(f"Workspace Location: {self._workspace}")
            self._processes.append({'process': 0,'module': self.__module_label, 'label': f""})
        else:
            return False
        
        # Get the Repo path from arguments
        #_repo_path = "/data/lnxBuild/SMO/R1.2"
        
        self.__git_provider.set_repo_path(self._workspace)
        
        repo = self.__git_provider.get_repo()
        
        last_commit_id = repo.head.commit.hexsha        
        self.log.info(f"Last Commit ID: {last_commit_id}")
        
        last_day_commit_id = self.__git_provider.get_last_day_commit(repo,days=1, hour=17, minute=30)       
        
        if not last_day_commit_id:
            print("No commits found in the last day.")
            return

        self.log.info(f"Changed files between {last_commit_id} and {last_day_commit_id}:")  
        
        file_changes = self.__git_provider.commit_file_changes(repo, last_commit_id, last_day_commit_id)
        
        commit_logs = self.__git_provider.commit_logs(repo, last_day_commit_id)
        
        print(commit_logs)
        
        print(file_changes)
        
        return self._processes
        
        