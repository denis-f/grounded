# Comment compiler la documentation ?

## Installation des dépendances
```bash
sudo apt-get install python3-sphinx
```
```bash
pip install sphinx-rtd-theme
```

Pour documenter le code, il est nécessaire de posséder toutes les dépendances python. Cela inclu le module Metashape,
cela fonctionne même sans licence.

## Mettre à jour la documentation

En premier lieu, il est nécessaire de se déplacer à la racine du projet avant de passer à la suite

* Génération de l'arborescence de la documentation : `sphinx-apidoc -e -E -o docs .`
* Se déplacer dans le répertoire de la documentation : `cd docs`
* Génération de la documentation au format web : `make html`
* Accéder à la documentation dans le répertoire `docs/_build/html`