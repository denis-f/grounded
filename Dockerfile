FROM python:3.12

# Définir le répertoire de travail
WORKDIR /usr/local/app

# Copier le projet dans le conteneur
COPY . /usr/local/app

# Installer les dépendances système et de build en limitant les paquets installés
RUN apt-get update && apt-get install -y --no-install-recommends \
    make imagemagick libimage-exiftool-perl exiv2 proj-bin \
    qtbase5-dev qt5-qmake libqt5svg5-dev g++ git-all \
    libpng-dev libjpeg-dev libeigen3-dev libboost-all-dev \
    libtbb-dev libopencv-dev cmake build-essential \
    qttools5-dev qttools5-dev-tools libqt5websockets5-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -r requirements.txt && \
 # Installation des dépendances
    # CloudCompare
    git clone https://github.com/CloudCompare/CloudCompare.git /opt/CloudCompare && \
    cd /opt/CloudCompare && \
    git submodule update --init --recursive && \
    mkdir build && cd build && \
    cmake .. && \
    make -j"$(nproc)" && \
    make install; \
    \
    # MicMac
    git clone https://github.com/micmacIGN/micmac.git /opt/micmac && \
    cd /opt/micmac && \
    mkdir build && cd build && \
    cmake ../ && \
    make -j"$(nproc)" install; \
    \
    # CCTag (création explicite du dossier build)
    git clone https://github.com/alicevision/CCTag.git /opt/CCTag && \
    cd /opt/CCTag && \
    mkdir build && cd build && \
    (cmake ../ || (echo "CUDA non trouvé, désactivation de CUDA" && cmake -DCCTAG_WITH_CUDA:BOOL=OFF ../)) && \
    make -j"$(( $(nproc) / 2 ))" install

CMD ["/bin/bash"]