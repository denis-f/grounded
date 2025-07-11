FROM ubuntu:22.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    make imagemagick libimage-exiftool-perl exiv2 proj-bin \
    qtbase5-dev qt5-qmake libqt5svg5-dev g++ git-all \
    libpng-dev libjpeg-dev libeigen3-dev libboost-all-dev \
    libtbb-dev libopencv-dev cmake build-essential \
    qttools5-dev qttools5-dev-tools libqt5websockets5-dev libqt5opengl5-dev libcgal-dev gdal-bin libgdal-dev libgmp-dev libmpfr-dev

# Compilation de MicMac
RUN git clone --branch v1.1.1 --single-branch --depth 1 https://github.com/micmacIGN/micmac.git /opt/micmac && \
    cd /opt/micmac && \
    mkdir build && cd build && \
    cmake ../ && \
    make -j"$(nproc)" && \
    make install

# Compilaton de CCTag
RUN git clone --branch v1.0.4  --single-branch --depth 1 https://github.com/alicevision/CCTag.git ./cctag && \
    cd ./cctag && \
    mkdir build && cd build && \
    (cmake -DCMAKE_BUILD_TYPE=Release ../ || (echo "CUDA non trouvé, désactivation de CUDA" && cmake -DCMAKE_BUILD_TYPE=Release -DCCTAG_WITH_CUDA:BOOL=OFF ../)) && \
    make -j"$(( $(nproc) / 2 ))" && \
    make install && \
    mv Linux-* /opt/CCTag

# Compilation de CloudCompare
RUN git clone --branch v2.13.2  --single-branch --depth 1 --recursive https://github.com/CloudCompare/CloudCompare.git /opt/CloudCompare && \
    cd /opt/CloudCompare && \
    mkdir build && cd build && \
    cmake -DCCCORELIB_USE_CGAL=ON -DOPTION_USE_GDAL=ON -DCMAKE_BUILD_TYPE=Release  -DPLUGIN_STANDARD_QCSF=ON .. && \
    make -j"$(nproc)" && \
    make install;


#--------------------------------------------------------------------------------------------
FROM ubuntu:22.04 AS final

WORKDIR /app

COPY . /opt/grounded

RUN apt-get update && apt-get install -y pip \
    # Dépendances minimales de CloudCompare
    libqt5printsupport5 libqt5opengl5 libgomp1 libqt5concurrent5 \
    # Dépendances minimales de MicMac
    imagemagick libimage-exiftool-perl exiv2 proj-bin make \
    # Dépendances minimales de CCTag
    libtbb12 libopencv-highgui4.5d libboost-filesystem1.74.0 libboost-program-options1.74.0 libboost-timer1.74.0 libboost-serialization1.74.0 libopencv-videoio4.5d

# Configuration du fichier yaml
RUN sed -i 's/^\([[:space:]]*path_cloud_compare:[[:space:]]*\).*/\1"CloudCompare"/' /opt/grounded/Configuration/config.yml && \
    sed -i 's/^\([[:space:]]*path_mm3d:[[:space:]]*\).*/\1"\/opt\/micmac\/bin\/mm3d"/' /opt/grounded/Configuration/config.yml && \
    sed -i 's/^\([[:space:]]*path_cctag_directory:[[:space:]]*\).*/\1"\/opt\/CCTag\/"/' /opt/grounded/Configuration/config.yml && \
    sed -i 's/^\([[:space:]]*path_cctag_directory:[[:space:]]*\).*/\1"\/opt\/CCTag\/"/' /opt/grounded/Configuration/config.yml

RUN pip install --progress-bar off --no-cache-dir -e /opt/grounded

# Copie du build de CloudCompare
COPY --from=builder /usr/local/bin/CloudCompare /usr/local/bin/CloudCompare
COPY --from=builder /usr/local/lib/cloudcompare /usr/local/lib/cloudcompare
COPY --from=builder /usr/local/lib/cloudcompare/plugins /usr/local/lib/cloudcompare/plugins
COPY --from=builder /usr/local/share/cloudcompare /usr/local/share/cloudcompare

# Copie du build de MicMac
COPY --from=builder /opt/micmac/bin /opt/micmac/bin
COPY --from=builder /opt/micmac/include /opt/micmac/include

# Copie du build de CCTag
COPY --from=builder /opt/CCTag /opt/CCTag


ENV PATH="/usr/local/bin:${PATH}"
ENV QT_QPA_PLATFORM=offscreen
