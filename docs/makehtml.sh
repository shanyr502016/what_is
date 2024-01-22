
python3 generate-dita-docs.py

python3 -m sphinx.ext.apidoc -f -o Docs -d 10 Deploy

python3 -m sphinx.ext.apidoc -f -o Docs -d 10 Manage

cd Docs && python3 -m sphinx.cmd.build -b html . _build//html && cd ..
