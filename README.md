# Grounded


## Description
Grounded is a software that allows to compute 2.5D volumes of soil samples from two series of photogrammetric acquisitions. It requires the use of dedicated scalebars [to be described further]. Image processing can be done either with Micmac, either with Agisoft Metashape. Scale bars can be done either with Circular Coded Targets from Alice Vision, either with Agisoft's implementation of Schneider (1991) coded targets.

*[work on Grounded in progress]*


## Installation

### Dépendances python
Executez la commande : 
    
```bash
pip install -r requirements.txt
```
### Dépendances logicielles

### _Linux_

>### MicMac
> > Installation des dépendances :  
> > `sudo apt-get update && sudo apt-get install make imagemagick libimage-exiftool-perl exiv2 proj-bin`
> >
> > `sudo apt update && sudo apt install qtbase5-dev qt5-qmake`
> 
> > Copier le dépôt github du projet : `git clone https://github.com/micmacIGN/micmac.git`  
>
> > Se déplacer à l'intérieur du projet : `cd micmac`  
>
> > Créer un dossier build et se déplacer à l'intérieur : `mkdir build && cd build`
>
> > Générer les makefiles en utilisant cmake : `cmake ../`
>
> > Effectuer la compilation en remplaçant **{cores number}** par le nombre de cœurs du processeur de la machine : `make install -j{cores number}`
>
>#### Recommandé : 
> 
> > Sortir du projet MicMac : `cd ../..`
> 
> > Déplacer MicMac dans le dossier /opt : `sudo mv micmac/ /opt/`

>### CCTag
>
> > Installation des dépendances :  
> > `sudo apt-get update && sudo apt-get install g++ git-all libpng-dev libjpeg-dev libeigen3-dev libboost-all-dev libtbb-dev`
> > 
> > `sudo apt update && sudo apt install libopencv-dev libboost-all-dev libopen3-dev`
> 
> > Copier le dépôt github du projet : `git clone https://github.com/alicevision/CCTag.git`
> 
> > Se déplacer à l'intérieur du projet : `cd CCTag`  
> 
> > Créer un dossier build et se déplacer à l'intérieur : `mkdir build && cd build`
> 
> > Générer les makefiles en utilisant cmake :
> > > Si vous possédez une carte graphique Nvidia : `cmake ../`
> >
> > > Sinon : `cmake -DCCTAG_WITH_CUDA:BOOL=OFF ../`
> 
> > Effectuer la compilation en remplaçant **{cores number}** par le nombre de cœurs du processeur de la machine : `make install -j{cores number}`
> 
>#### Recommandé :
> > Renommer le fichier nouvellement généré : `mv Linux-* CCTag`
> 
> > Déplacer le fichier CCTag dans le dossier /opt : `sudo mv CCTag/ /opt/`


>### CloudCompare
>```bash
>sudo snap install cloudcompare
>```

## Usage

### Avant toute première utilisation, veuillez remplacer les informations se trouvant dans le fichier `Configuration/config.yml` afin de s'adapter à la configuration de votre machine


### Avec le fichier grounded :
#### Le logiciel grounded utilise un fichier de configuration qui contient pour chaque module les valeurs pas défaut des arguments

Il est possible d'utiliser le logiciel de façon simple avec les paramètres par défaut comme ceci : 
```bash
python3 grounded.py path/to/photo_before_excavation path/to/photo_after_excavation
```

Il est également possible de choisir les modules ainsi que leurs paramètres qui seront utilisés lors de l'analyse de la façon suivante :
```bash
python3 grounded.py -SFM micmac -SFM_arg distorsion_model=FraserBasic -SFM_arg zoom_final=BigMack -Detector detection_cctag path/to/photo_before_excavation path/to/photo_after_excavation
```

À des fins de débuggage, il est possible d'afficher la zone dans laquelle la détection des trous est effectuée en rajoutant la balise `-display_padding` de la façon suivante 
```bash
python3 grounded.py -SFM metashape -SFM_arg downscale=8 -Detector detection_metashape -display_padding path/to/photo_before_excavation path/to/photo_after_excavation
```

Une aide est présente via la commande :
```bash
python3 grounded.py --h
```
ou
```bash
python3 grounded.py -help
```

### Avec le fichier main :
Il est nécessaire d'entrer les chemins menant aux photos dans les zones indiquées par les commentaires présents dans le code.
```commandline
python3 main.py
```

#### <span style="color:red">⚠️ Cette version est un prototype et son utilisation est vouée à changer au fil du temps.</span>

## Authors and acknowledgment
### Auteurs principaux
- Norman FRANÇOIS [GitHub](https://github.com/Norman-Francois) [Linkedin](https://fr.linkedin.com/in/norman-françois)
- Denis FEURER  [Linkedin](https://fr.linkedin.com/in/denis-feurer-87a7084/fr)
- Fabrice VINATIER [Linkedin](https://fr.linkedin.com/in/fabrice-vinatier-2167ba1b5)

## License
Licenced under CC-BY-SA 4.0.

## Project status
Project in development. Repository is private at the moment.
