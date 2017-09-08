FROM i686/ubuntu

RUN apt-get update && apt-get install -yq \
 git \
 curl \
 ninja-build \
 python \
 python-dev \
 python-distribute \
 python-pip \
&& rm -rf /var/lib/apt/lists/*

RUN python -m pip install -U pip

# install yotta development dependencies
RUN pip install \
    tox \
    cython \
    nose \
    pylint \
    coverage \
    green \
    ipython

# fix up cmake
RUN apt-get remove -yq cmake

# FIXME: 64 or 32?
RUN curl -fsSL http://www.cmake.org/files/v3.2/cmake-3.2.3-Linux-i386.sh > /tmp/install-cmake.sh
#RUN curl -fsSL https://cmake.org/files/v3.2/cmake-3.2.3-Linux-x86_64.sh > /tmp/install-cmake.sh

RUN chmod +x /tmp/install-cmake.sh
RUN /tmp/install-cmake.sh --prefix=/usr/local/ --exclude-subdir

ENV PYTHONIOENCODING: UTF-8
ENV YOTTA_GITHUB_AUTHTOKEN: 8d1dfa2011f74b1f26504918982e1e2ba154b910

# FIXME: "CMAKE not installed" Maybe a difference between Ubuntu and CircleCI?
ENV PATH="/usr/local:${PATH}"

WORKDIR yt_testbuild

# add setup.py &tc (for the dependencies) first, to preserve docker cache
ADD setup.py .
ADD yotta/version.txt yotta/version.txt
ADD pypi_readme.rst .
ADD bin/ bin/

# install yotta dependencies
RUN pip install -e .

# prepare tox in the same way as CircleCI
ADD tox.ini .
RUN tox --notest

# metadata
LABEL description="An image for devtesting Yotta in a stable environment. One day it might replace the CircleCI script."
LABEL incantation="docker build -t yotta . && docker run --rm --name yotta -it yotta /bin/bash"

# development workflow
# TODO: volume mount
ADD . .

RUN bash ci_init.sh
