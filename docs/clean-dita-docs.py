import os
import shutil

DitaDeploy = "Deploy"
DitaManage = "Manage"


################################### Cleaning the Process ####################################################
if os.path.exists(DitaDeploy):
    shutil.rmtree(DitaDeploy)

if os.path.exists(DitaManage):
    shutil.rmtree(DitaManage)

if os.path.exists('Docs/_build'):
    shutil.rmtree('Docs/_build')

if os.path.exists('Docs'):
    for list in os.listdir('Docs'):
        if list != 'modules.rst' and list != 'index.rst':
            if list.endswith('.rst'):
                os.remove('Docs/'+list)
################################### Cleaning the Process ####################################################