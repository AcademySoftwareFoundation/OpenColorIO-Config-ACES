# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.

# https://hub.docker.com/r/aswf/ci-ocio/tags
FROM aswf/ci-ocio:2021

# Base Plotting and Docs Building Dependencies.
RUN yum install --setopt=tsflags=nodocs -y \
    graphviz-devel \
    perl-Digest-MD5

# OpenColorIO Build
WORKDIR /tmp
ARG OCIO_INSTALL_DIRECTORY=/usr/local
RUN git clone https://github.com/AcademySoftwareFoundation/OpenColorIO \
    && cd OpenColorIO \
    && mkdir build \
    && mkdir -p ${OCIO_INSTALL_DIRECTORY} \
    && cd build \
    && cmake -DOCIO_INSTALL_EXT_PACKAGES=ALL -DCMAKE_INSTALL_PREFIX=${OCIO_INSTALL_DIRECTORY} ../ \
    && make -j8 \
    && make install \
    && cd /tmp \
    && rm -rf OpenColorIO

# LaTeX Dependencies for Sphinx Generated PDF
WORKDIR /tmp
COPY ./utilities/resources/texlive.profile .
RUN wget https://mirrors.rit.edu/CTAN/systems/texlive/tlnet/install-tl-unx.tar.gz \
    && tar -xvf install-tl-unx.tar.gz \
    && cd install-tl-* \
    && perl install-tl --profile ../texlive.profile \
    && tlmgr install \
        capt-of \
        collection-fontsrecommended \
        fncychap \
        fontaxes \
        framed \
        inconsolata \
        latexmk \
        lato \
        needspace \
        tabulary \
        titlesec \
        varwidth \
        wrapfig \
    && tlmgr path add \
    && cd /tmp \
    && rm -rf install-tl* \
    && rm texlive.profile

# Python Requirements
WORKDIR /tmp
COPY ./requirements.txt /tmp
RUN sed -i 's/<cgraph.h>/"cgraph.h"/g' /usr/include/graphviz/types.h
RUN pip install -r requirements.txt \
    && rm /tmp/requirements.txt

# Environment Variables & Working Directory
ARG WORKING_DIRECTORY=/home/aswf/OpenColorIO-Config-ACES
ENV PYTHONPATH=${WORKING_DIRECTORY}:${PYTHONPATH}
WORKDIR ${WORKING_DIRECTORY}
