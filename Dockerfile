# Utilisation de l'image Python 3.12 comme image de base
FROM python:3.12

# Définir le répertoire de travail
WORKDIR /usr/local/app

# Installer les dépendances python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Installer Metashape
RUN curl -L https://download.agisoft.com/Metashape-2.2.0-cp37.cp38.cp39.cp310.cp311-abi3-linux_x86_64.whl -o Metashape-2.2.0-cp37.cp38.cp39.cp310.cp311-abi3-linux_x86_64.whl
RUN pip install Metashape-*.whl

# Installer les dépendances logicielles nécessaires pour MicMac, CCTag et CloudCompare
RUN apt-get update && \
    apt-get install -y \
    make \
    imagemagick \
    libimage-exiftool-perl \
    exiv2 \
    proj-bin \
    qtbase5-dev \
    qt5-qmake \
    libqt5svg5-dev \
    g++ \
    git-all \
    libpng-dev \
    libjpeg-dev \
    libeigen3-dev \
    libboost-all-dev \
    libtbb-dev \
    libopencv-dev \
    cmake \
    build-essential \
    libqt5svg5-dev \
    qttools5-dev \
    qttools5-dev-tools \
    libqt5websockets5-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer CloudCompare depuis les sources
RUN git clone https://github.com/CloudCompare/CloudCompare.git /opt/CloudCompare
WORKDIR /opt/CloudCompare
RUN cd /opt/CloudCompare && \
    git submodule update --init --recursive && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install

# Copier le dépôt MicMac
RUN git clone https://github.com/micmacIGN/micmac.git /opt/micmac
WORKDIR /opt/micmac
RUN mkdir build && cd build && cmake ../ && make install -j$(nproc)

# Copier le dépôt CCTag
RUN git clone https://github.com/alicevision/CCTag.git /opt/CCTag
WORKDIR /opt/CCTag
RUN mkdir build &&  \
    cd build && cmake ../ || (echo "CUDA not found, disabling CUDA" && cmake -DCCTAG_WITH_CUDA:BOOL=OFF ../)  \
    && make install -j$(($(nproc)/2))

# Copier le projet actuel
WORKDIR /usr/local/app
COPY . /usr/local/app/src

# Configurer le fichier de configuration pour la machine (exemple avec le fichier config.yml)
COPY Configuration/config.yml /usr/local/app/Configuration/config.yml

# Lancer l'application
CMD ["python", "src/grounded.py"]
