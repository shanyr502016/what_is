import os
import sys

path = os.path.abspath('.')
list_dir = os.listdir(path)

# Configuration file for the Sphinx documentation builder.
for i in list_dir:
    if i.endswith('.rst'):
        package_list = i.rsplit('.')
        if len(package_list) == 3:
            package_name = package_list[-2]
            with open(f'{path}/{str(i)}','r+') as file:
                lines = file.readlines()
                lines[0] = f"""``{package_name}``\n"""
                lines[1] = int(len(package_name)+5)*'='
                lines[3] = " \n \n"
                lines[4] = " \n \n"
                file.seek(0)
                file.truncate()
                file.writelines(lines)


with open("index.rst",'w') as init_py:
                    init_py.writelines(f"""
Welcome to Dita documentation!
==================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Deploy
   Manage

    """)
                    
with open('Deploy.rst','r+') as file:
    lines = file.readlines()
    lines[3] = f"Modules \n"
    file.seek(0)
    file.truncate()
    file.writelines(lines)
    
with open('Deploy.rst', 'r+') as file:
    file_contents = file.read()
    new_contents = file_contents.replace('Module contents', '')
    file.seek(0)
    file.write(new_contents)
    file.truncate()

with open('Manage.rst','r+') as file:
    lines = file.readlines()
    lines[0] = f"""Manage Environment\n"""
    lines[1] = "========================"
    lines[3] = f"Modules \n"
    file.seek(0)
    file.truncate()
    file.writelines(lines)

with open('Manage.rst', 'r+') as file:
    file_contents = file.read()
    new_contents = file_contents.replace('Module contents', '')
    file.seek(0)
    file.write(new_contents)
    file.truncate()

sys.path.insert(0,os.path.abspath('..'))

project = 'Dita Documentation'
copyright = '2023, Siemens'
author = 'Siemens'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.napoleon','sphinx.ext.todo','sphinx.ext.viewcode','sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

rst_prolog = """

.. include:: <s5defs.txt>

"""
autodoc_mock_imports = ['generate']

rst_prolog = """
.. include:: <s5defs.txt>

"""

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# furo
html_theme = 'sphinx_rtd_theme'
html_title = project
html_static_path = ['_static']
html_css_files = ["furo.css","colors.css"]
