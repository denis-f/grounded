# Grounded


## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation

### Dépendances python
Executez la commande : 
    
```bash
pip install -r requirements.txt
```
### Dépendances logicielles

### _Linux_

>### MicMac
> > Installation des dépendances : `sudo apt-get update && sudo apt-get install make imagemagick libimage-exiftool-perl exiv2 proj-bin qt5-default`
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
> > `sudo apt update && sudo apt install libopencv-dev, libboost-all-dev libopen3-dev`
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

### Avant toute utilisation, veuillez remplacer les informations se trouvant dans le fichier python que vous choisirez d'exécuter


### Avec le fichier grounded :
```commandline
python3 grounded.py path/to/photo_before_excavation path/to/photo_after_excavation
```

### Avec le fichier main :
Il est nécessaire d'entrer les chemins menant aux photos dans les zones indiquées par les commentaires présents dans le code.
```commandline
python3 main.py
```

#### <span style="color:red">⚠️ Cette version est un prototype et son utilisation est vouée à changer au fil du temps.</span>

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
### Auteurs principaux
- Norman FRANÇOIS [GitHub](https://github.com/Norman-Francois) [Linkedin](https://fr.linkedin.com/in/norman-françois)
- Denis FEURER  [Linkedin](https://fr.linkedin.com/in/denis-feurer-87a7084/fr)
- Fabrice VINATIER [Linkedin](https://fr.linkedin.com/in/fabrice-vinatier-2167ba1b5)

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
