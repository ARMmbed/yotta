FROM ubuntu

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
RUN pip install tox

# fix up cmake
RUN apt-get remove -yq cmake
RUN curl -fsSL http://www.cmake.org/files/v3.2/cmake-3.2.3-Linux-i386.sh > /tmp/install-cmake.sh
RUN chmod +x /tmp/install-cmake.sh
RUN /tmp/install-cmake.sh --prefix=/usr/local --exclude-subdir

ENV PYTHONIOENCODING: UTF-8
ENV YOTTA_GITHUB_AUTHTOKEN: 8d1dfa2011f74b1f26504918982e1e2ba154b910

WORKDIR yt_testbuild
ADD . .

RUN bash ci_init.sh
RUN tox --notest

# TODO:
# CMAKE not installed
# Why don't all the pip installs work
# Maybe setup.py isn't working or being invoked correctly [by tox?]
