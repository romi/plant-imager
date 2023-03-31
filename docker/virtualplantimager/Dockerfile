FROM continuumio/miniconda3

ARG USER_NAME=scanner
ARG USER_ID=1000
ARG GROUP_NAME=scanner
ARG GROUP_ID=1000

ENV DB_LOCATION="/home/${USER_NAME}/db"
ENV PATH=$PATH:"/home/${USER_NAME}}/.local/bin"
ENV PATH="/opt/blender:${PATH}"
ENV PATH="/opt/blender:${PATH}"
ENV BLENDER_URL=https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.93/blender-2.93.16-linux-x64.tar.xz

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libxi6 \
    libc++-dev \
    emacs-nox \
    gcc python3.9-dev && \
    # Clean apt and its cache
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create a non-root user and give it rights over "home folder"
    addgroup --gid $GROUP_ID $GROUP_NAME && \
    adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID $USER_NAME && \
    mkdir $DB_LOCATION && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    chown -R ${USER_NAME}: /opt/conda/ && \
    # Download Blender 2.93 and move it to /opt/blender
    wget --progress=bar $BLENDER_URL && \
    tar -xJf blender-2.93.16-linux-x64.tar.xz && \
    mv blender-2.93.16-linux-x64 /opt/blender && \
    rm blender-2.93.16-linux-x64.tar.xz

ENV LD_LIBRARY_PATH "/opt/blender/lib"

# Change to the non-root user
USER ${USER_NAME}

# Change working directory
WORKDIR /home/${USER_NAME}

# Create the appropriate conda python environment
RUN conda install -y mamba -n base -c conda-forge && \
    conda create -y -n lpyEnv python=3.9 && \
    mamba install -y -n lpyEnv -c conda-forge -c open3d-admin -c fredboudon flask imageio toml openalea.lpy open3d && \
    conda clean -y --all

# Copy python libraries to the python's blender site-packages
USER root
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/markupsafe/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/flask/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/itsdangerous/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/click/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/werkzeug/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/jinja2/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/imageio/ /opt/blender/2.93/python/lib/python3.9/site-packages/

USER ${USER_NAME}

RUN conda init bash
SHELL [ "conda", "run", "-n", "lpyEnv", "/bin/bash", "-c" ]

# Install plant-imager from host's local source files

COPY --chown=${USER_NAME}:${GROUP_NAME} ./ plant-imager/

RUN cd plant-imager/ && \
    python3 -m pip install -r ./plantdb/requirements.txt --no-cache-dir && \
    python3 -m pip install -e ./plantdb/ --no-cache-dir && \
    python3 -m pip install -r ./romitask/requirements.txt --no-cache-dir && \
    python3 -m pip install -e ./romitask/ --no-cache-dir && \
    python3 -m pip install . --no-cache-dir

EXPOSE 9001

# For interactive shell
RUN echo "conda activate lpyEnv" >> ~/.bashrc

# For login shell, used in run.sh when passing a script as argument
RUN echo "conda activate lpyEnv" >> ~/.profile
RUN echo "export PATH=\$PATH:/opt/blender" >> ~/.profile
RUN echo "export LD_LIBRARY_PATH=/opt/blender/lib" >> ~/.profile
