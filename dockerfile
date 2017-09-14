# This is for generating a docker image to work with whilst developing yotta
# If you want to _run_ yotta in production, use this image instead: mbed/yotta


FROM i686/ubuntu

RUN apt-get -yqq update && apt-get -yqq install  \
 curl \
 git \
 nano \
 ninja-build \
 python \
 python-dev \
 python-distribute \
 python-pip \
&& rm -rf /var/lib/apt/lists/*

RUN python -m pip install -U pip

# install yotta development dependencies
RUN pip install -q \
    tox \
    cython \
    nose \
    pylint \
    coverage \
    green \
    ipython

# fix up cmake
RUN apt-get remove -yq cmake

RUN curl -fsSL http://www.cmake.org/files/v3.2/cmake-3.2.3-Linux-i386.sh > /tmp/install-cmake.sh

# alternatively, this package for use with 64-bit
#RUN curl -fsSL https://cmake.org/files/v3.2/cmake-3.2.3-Linux-x86_64.sh > /tmp/install-cmake.sh

RUN chmod +x /tmp/install-cmake.sh
RUN /tmp/install-cmake.sh --prefix=/usr/local/ --exclude-subdir

ENV PYTHONIOENCODING: UTF-8
ENV YOTTA_GITHUB_AUTHTOKEN: 8d1dfa2011f74b1f26504918982e1e2ba154b910

ENV PATH="/usr/local:${PATH}"

WORKDIR yt_testbuild

# add setup.py &tc (for the dependencies) first, to preserve docker cache
ADD setup.py .
ADD yotta/version.txt yotta/version.txt
ADD pypi_readme.rst .
ADD bin/ bin/

# install yotta dependencies
RUN pip install -q -e .

# prepare tox in the same way as CircleCI
ADD tox.ini .
RUN tox --notest

# metadata
LABEL description="An image for devtesting Yotta in a stable environment. One day it might replace the CircleCI script."
LABEL incantation="docker build -t yotta . && docker run --rm --name yotta -v my_working_copy:/yt_testbuild -it yotta /bin/bash"

ADD . .

RUN ls -lah

RUN bash ci_init.sh

# TODO: volume mount
# You must mount your working directory into the image using the -v command at run time, because:
# "...you can’t mount a host directory from within the Dockerfile.
# The VOLUME instruction does not support specifying a host-dir parameter.
# You must specify the mountpoint when you create or run the container."
# - https://docs.docker.com/engine/reference/builder/#notes-about-specifying-volumes
# i.e. `-v my_working_copy:/yt_testbuild`
