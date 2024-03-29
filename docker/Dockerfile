FROM continuumio/miniconda3

ARG USER_NAME=scanner
ARG USER_ID=1000
ARG GROUP_NAME=scanner
ARG GROUP_ID=1000

ENV DB_LOCATION="/home/${USER_NAME}/db"
ENV PATH=$PATH:"/home/${USER_NAME}}/.local/bin"
ENV PATH="/opt/blender:${PATH}"
ENV PATH="/opt/blender:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libxi6 \
    libc++-dev \
    emacs-nox \
    gcc python3.7-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and give it rights over "home folder"
RUN addgroup --gid $GROUP_ID $GROUP_NAME && \
    adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID $USER_NAME && \
    mkdir $DB_LOCATION && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    chown -R ${USER_NAME}: /opt/conda/

# Download Blender2.81 and move it to /opt/blender
ENV BLENDER_URL=https://download.blender.org/release/Blender2.81/blender-2.81a-linux-glibc217-x86_64.tar.bz2
RUN wget --progress=bar $BLENDER_URL && \
    tar -xjf blender-2.81a-linux-glibc217-x86_64.tar.bz2 && \
    mv blender-2.81a-linux-glibc217-x86_64 /opt/blender && \
    rm blender-2.81a-linux-glibc217-x86_64.tar.bz2

ENV LD_LIBRARY_PATH "/opt/blender/lib"

# Change to the non-root user
USER ${USER_NAME}

# Change working directory
WORKDIR /home/${USER_NAME}

# Create the appropriate conda python environment
RUN conda create -n lpyEnv python=3.7

RUN conda install -n lpyEnv -c conda-forge flask imageio toml luigi boost=1.70.0 qhull=2015.2
RUN conda install -n lpyEnv -c conda-forge -c fredboudon openalea.lpy
RUN conda install -n lpyEnv -c open3d-admin open3d=0.10

# Copy python libraries to the python's blender site-packages
USER root
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/markupsafe/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/flask/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/itsdangerous/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/click/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/werkzeug/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/jinja2/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/imageio/ /opt/blender/2.81/python/lib/python3.7/site-packages/

USER ${USER_NAME}

RUN conda init bash
SHELL [ "conda", "run", "-n", "lpyEnv", "/bin/bash", "-c" ]

# Install plant-imager from host's local source files

COPY --chown=${USER_NAME}:${GROUP_NAME} ./ plant-imager/

RUN cd plant-imager/ && \
    python -m pip install -e ./plantdb/ --no-cache-dir && \
    python -m pip install -e ./romitask/ --no-cache-dir && \
    python -m pip install . --no-cache-dir


EXPOSE 9001

# For interactive shell
RUN echo "conda activate lpyEnv" >> ~/.bashrc

# For login shell, used in run.sh when passing a script as argument
RUN echo "conda activate lpyEnv" >> ~/.profile
RUN echo "export PATH=\$PATH:/opt/blender" >> ~/.profile
RUN echo "export LD_LIBRARY_PATH=/opt/blender/lib" >> ~/.profile
