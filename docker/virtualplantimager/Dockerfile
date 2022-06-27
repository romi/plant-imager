FROM ubuntu:20.04 AS base

LABEL maintainer="Nabil Ait Taleb <mohamednabil.aittaleb@sony.com>"
LABEL corresponding_author="Jonathan LEGRAND <jonathan.legrand@ens-lyon.fr>"
LABEL project="Robotics for microfarming (ROMI)"
LABEL homepage="https://docs.romi-project.eu/documentation/"
LABEL repository="https://github.com/romi/plant-imager"
LABEL license="LGPL-3.0-or-later"
LABEL description="A Blender3D-based virtual plant imager"

ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV USER_NAME=myuser
ENV PATH=$PATH:"/home/${USER_NAME}}/.local/bin"
ENV PATH="/opt/blender:${PATH}"
ENV PATH="/opt/conda/bin:${PATH}"
ENV LD_LIBRARY_PATH "/opt/blender/lib"
ENV DB_LOCATION="/myapp/db"

WORKDIR /myapp

FROM base AS builder

# Update package manager & install requirements
RUN apt-get --allow-releaseinfo-change-suite update --fix-missing && \
    apt-get install -y --no-install-recommends \
    wget bzip2 ca-certificates curl git \
    libgl1-mesa-dev \
    libxrender1 \
    libxi6 \
    libc++-dev \
    emacs-nox \
    gcc \
    python3.7 python3-pip && \
    apt-get clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

# Download and install miniconda3
ENV MINICONDA3_URL=https://repo.anaconda.com/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh
RUN wget --quiet $MINICONDA3_URL -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# Download Blender2.81 and move it to /opt/blender
ENV BLENDER_URL=https://download.blender.org/release/Blender2.81/blender-2.81a-linux-glibc217-x86_64.tar.bz2
RUN wget --progress=bar $BLENDER_URL && \
    tar -xjf blender-2.81a-linux-glibc217-x86_64.tar.bz2 && \
    mv blender-2.81a-linux-glibc217-x86_64 /opt/blender && \
    rm blender-2.81a-linux-glibc217-x86_64.tar.bz2

# Create a non-root user and give it rights over "myapp" folder
RUN adduser --disabled-password --gecos '' ${USER_NAME} && \
    # Give all rights to database location
    mkdir -m 777 -p $DB_LOCATION && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    chown -R ${USER_NAME}: /opt/conda/

# Change to the non-root user
USER ${USER_NAME}

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install poetry

# Change working directory
WORKDIR /home/${USER_NAME}

# Create the appropriate conda python environment
RUN conda create -n lpyEnv python=3.7
RUN conda update -y -n base -c defaults conda

RUN conda install -n lpyEnv -c conda-forge flask imageio toml luigi poetry
RUN conda install -n lpyEnv -c fredboudon -c conda-forge openalea.lpy=3.8.2

# Copy python libraries to the python's blender site-packages
USER root
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/markupsafe/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/flask/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/itsdangerous/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/click/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/werkzeug/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/jinja2/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/imageio/ /opt/blender/2.81/python/lib/python3.7/site-packages/

FROM builder AS final

USER ${USER_NAME}

RUN conda init bash
SHELL [ "conda", "run", "-n", "lpyEnv", "/bin/bash", "-c" ]

# Install plant-imager from host's local source files

COPY --chown=${USER_NAME} ./ plant-imager/

RUN cd plant-imager/ && \
    #poetry install -n --no-dev --no-root
    poetry install

EXPOSE 9001

# For interactive shell
RUN echo "conda activate lpyEnv" >> ~/.bashrc

# For login shell, used in run.sh when passing a script as argument
RUN echo "conda activate lpyEnv" >> ~/.profile
RUN echo "export PATH=\$PATH:/opt/blender" >> ~/.profile
RUN echo "export LD_LIBRARY_PATH=/opt/blender/lib" >> ~/.profile
