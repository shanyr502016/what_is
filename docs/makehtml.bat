

python generate-dita-docs.py

sphinx-apidoc -f -o Docs -d 10 Deploy

sphinx-apidoc -f -o Docs -d 10 Manage

cd Docs && sphinx-build . _build//html && cd ..
