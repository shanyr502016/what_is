"""

Use Profile vars
        tcprofilevars = TCProfilevars()
        tcprofilevars.load()
"""

from corelib.Loggable import Loggable
from corelib.Environment import Environment
from corelib.Process import Process
from corelib.File import File
import os

class TCProfilevars(Loggable):


    STDOUT_TAG = 'EOEENV'

    def __init__(self):

        super().__init__(__name__)


    def load(self):

        environment = Environment()        

        tc_data = environment.get_tc_data()
        tc_profilevars_file = self.get_file()

        process_environment = {}


        try:
            process = Process('. $TC_DATA/tc_profilevars echo -e "\nEOEENV"; env', tc_data)
            process.hide_output()
            process.collect_output()
            process.ignore_errors()
            process.execute()
            
            lines = process.get_out_lines()
            accept_lines = True
            count = 0
            for line in lines:
                line = line.strip()
                if line == self.STDOUT_TAG:
                    # end tag found - start parsing mode
                    accept_lines = True
                    continue

                if not accept_lines:
                    # ignore line as it belongs to the process
                    continue

                env_value = line.split('=', 1)
                if len(env_value) < 2 or len(env_value[0]) < 1:
                    # Might happen if some functions are in the environment (like the spack profile)
                    continue
                process_environment[env_value[0]] = env_value[1]
                count += 1

            self.log.debug('Got ' + str(count) + ' environment variables')
            os.environ.update(process_environment)
            
        except Exception as e:
            self.log.error('Could not read tc_profilevars: ' + str(e))

    def get_file(self):

        "Returns the tc_profilevars file"

        environment = Environment()        

        tc_data = environment.get_tc_data()
        tc_root = environment.get_tc_root()
        
        if tc_root is None:            
            self.log.error('Could not load tc_profilevars: TC_ROOT is not configured')
            exit()
            return

        if tc_data is None:
            self.log.error('Could not load tc_profilevars: TC_DATA is not configured')
            exit()
            return       

        if environment.get_current_os_type() == 'LNX':
            return File(tc_data, 'tc_profilevars')
        return File(tc_data, 'tc_profilevars.bat')


