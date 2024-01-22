import json
import os
import shutil

DitaDeploy = "Deploy"
DitaManage = "Manage"
DeployTargetPath = f"{os.path.abspath('..')}/.config/Deploy/deploy_targets.json"
ManageConfigPath = f"{os.path.abspath('..')}/pyscripts/config"

################################### Cleaning the Process ####################################################
if os.path.exists(DitaDeploy):
    shutil.rmtree(DitaDeploy)

if os.path.exists(DitaManage):
    shutil.rmtree(DitaManage)

if os.path.exists('Docs'):
    for list in os.listdir('Docs'):
        if list != 'modules.rst' and list != 'index.rst':
            if list.endswith('.rst'):
                os.remove('Docs/'+list)
################################### Reading Configuration Section Start ######################################
# Collect image data

image_data = []
if os.path.exists('images'):
    image_data = os.listdir('images')
    image_data = [i.lower() for i in image_data]


# Load Deploytargets.json

with open(DeployTargetPath) as file:
    Ddata = json.load(file)

# Load Manage.json
Mdata = {}
for manage_data in os.listdir(ManageConfigPath):
    manage_data_file = os.path.join(ManageConfigPath,manage_data)
    with open(manage_data_file) as file:
        man_data = json.load(file)
    for key,node in man_data.items():
        Mdata[key] = node
 
################################### Reading Configuration Section End ########################################


################################### Creating Folders Section End ########################################
if not os.path.exists(DitaDeploy):
    os.makedirs(DitaDeploy)

if not os.path.exists(DitaManage):
    os.makedirs(DitaManage)


################################### Creating Folders Section End ########################################

with open(f"{DitaDeploy}/__init__.py",'w') as D_file:
    pass

with open(f"{DitaManage}/__init__.py",'w') as M_file:
    pass

def str_capitalize(name:str):
    _name = name.split('.')
    if len(_name) > 1:
        _name[1] = _name[1].capitalize()
    return '.'.join(_name)

current_working_dir = os.getcwd().replace('/','//').replace('\\','//')

# Preparing the Config Data and Commands Section for Dita Deploy
for key,value in Ddata.items():
    key_name = str(str_capitalize(key)).replace('.','_')
    if not os.path.exists(f'{DitaDeploy}/{key_name}'):
        os.makedirs(f'{DitaDeploy}/{key_name}')
    data_list = Ddata[key]
    with open(f"{DitaDeploy}/{key_name}/__init__.py",'w') as init_py:
        init_py.writelines(f"""'''
""")
        for i,j in data_list.items():
            if i == 'description':
                init_py.writelines(f"""
``Description :``
------------------              
    {j}
""")

        init_py.writelines(f"""
``Config Data :``
------------------
 """)
        for i,j in data_list.items():
            if i == 'executeTargets':
                init_py.writelines(f"""
    :orange:`{i}` :""")
                j_data = j.split(',')
                for sub_data in j_data:
                    k = str_capitalize(sub_data)
                    init_py.writelines(f"""
         :doc:`Deploy.{k.replace('.','_')}`\n""")
            elif i != 'description':
                init_py.writelines(f"""
    :orange:`{i}` :""")
                init_py.writelines(f"""
         :blue:`{j}`\n""")
                
        init_py.writelines(f"""
''' """)
print("Preparing the Config Data and Commands Section for Dita Deploy")

# Preparing Dita Commands for Dita Deploy
for key,value in Ddata.items():
    key_name = str(str_capitalize(key)).replace('.','_')
    if os.path.exists(f'{DitaDeploy}/{key_name}'):
        with open(f"{DitaDeploy}/{key_name}/__init__.py",'r+') as init_py_1:
            lines = init_py_1.readlines()
            init_py_1.seek(0)
            init_py_1.truncate()
            init_py_1.writelines(lines[:-1])
        image_name = f"{key_name}.PNG".lower()
        if image_name in image_data:
            with open(f"{DitaDeploy}/{key_name}/__init__.py",'a') as init_py_1:    
                init_py_1.writelines(f"""
``Commands:``
----------------

    ./dita_deploy.sh -m {key_name.replace('_','.')} -p $CMN_PACKAGE_ID,$RI_PACKAGE_ID -d

``Screenshot:``
----------------

    .. image::  {current_working_dir}//images//{key_name}.png

    ''' """) 
        else:
            with open(f"{DitaDeploy}/{key_name}/__init__.py",'a') as init_py_1:    
                init_py_1.writelines(f"""
``Commands:``
----------------

    ./dita_deploy.sh -m {key_name.replace('_','.')} -p $CMN_PACKAGE_ID,$RI_PACKAGE_ID -d

    ''' """)                   

                
print("Preparing Dita Commands for Dita Deploy.")

# Preparing the Config Data and Commands Section for Dita Manage
for key,value in Mdata.items():
    if key != 'ENVIRONMENT':
        if not os.path.exists(f"{DitaManage}/{key}"):
            os.makedirs(f"{DitaManage}/{key}")
        if 'INSTANCES' in Mdata[key]:
            data_list = Mdata[key]['INSTANCES']
        else:
            data_list = []
        if 'Description' in Mdata[key]:
            desc_data = Mdata[key]['Description']
        else:
            desc_data = ''
        if data_list != []:
            with open(f"{DitaManage}/{key}/__init__.py",'w') as init_py:
                init_py.writelines(f"""'''
``Description :``
------------------
    {desc_data}
""")            
                init_py.writelines(f"""

``Config Data :``
------------------
 """)
                if isinstance(data_list,str):
                    data_list = data_list.split(',')
                for datas in data_list:
                    if isinstance(datas,str):
                        init_py.writelines(f"""
    :doc:`Manage.{datas.replace(',','')}`\n """)
                    else:
                        for key,value in datas.items():
                            init_py.writelines(f"""
        :orange:`{key}` : :blue:`{value}`\n """)

        else :
            with open(f"{DitaManage}/{key}/__init__.py",'w') as init_py:
                init_py.writelines(f"""'''

""")            
                init_py.writelines(f"""

``Config Data :``
------------------
 """)
                if isinstance(data_list,str):
                    data_list = data_list.split(',')        
                for datas in data_list:
                    if isinstance(datas,str):
                        init_py.writelines(f"""
    :doc:`Manage.{datas.replace(',','')}`\n """)
                    else:
                        for key,value in datas.items():
                            init_py.writelines(f"""
        :orange:`{key}` : :blue:`{value}`\n """)

                
print("Preparing the Config Data and Commands Section for Dita Manage")            

# Preparing Dita Commands for Dita Manage
for key,value in Mdata.items():
    if key != 'ENVIRONMENT':
        if os.path.exists(f"{DitaManage}/{key}"):
            with open(f"{DitaManage}/{key}/__init__.py",'a') as init_py:
                for command_data in ['Status','Start','Stop']:
                    manage_data_name = key
                    image_name = f"{manage_data_name}_{command_data}.PNG".lower()
                    if image_name in image_data:
                       init_py.writelines(f"""

``{command_data} Command:``
----------------------------

        ./dita_manage.sh -m {manage_data_name} -a {command_data} -d

``Screenshot:``
----------------

    .. image:: {current_working_dir}//images//{manage_data_name}_{command_data}.png
   
""")

                    else:
                       init_py.writelines(f"""
``{command_data} Command:``
---------------------------

        ./dita_manage.sh -m {manage_data_name} -a {command_data} -d
 
  """)
                init_py.writelines(f"""
'''  """)                          

print("Preparing Dita Commands for Dita Manage")  
