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
    nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and give it rights over "home folder"
RUN addgroup --gid $GROUP_ID $GROUP_NAME && \
    adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID $USER_NAME && \
    mkdir $DB_LOCATION && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    chown -R ${USER_NAME}: /opt/conda/

# Change to the non-root user
USER ${USER_NAME}

# Change working directory
WORKDIR /home/${USER_NAME}

# Create the appropriate conda python environment
RUN conda create -n plantimager python=3.7

USER ${USER_NAME}

RUN conda init bash
SHELL [ "conda", "run", "-n", "plantimager", "/bin/bash", "-c" ]

# Install plant-imager from host's local source files
COPY --chown=${USER_NAME}:${GROUP_NAME} ./ plant-imager/

RUN cd plant-imager/ && \
    python -m pip install -e ./plantdb/ --no-cache-dir && \
    python -m pip install -e ./romitask/ --no-cache-dir && \
    python -m pip install . --no-cache-dir

# For interactive shell
RUN echo "conda activate plantimager" >> ~/.bashrc

# For login shell, used in run.sh when passing a script as argument
RUN echo "conda activate plantimager" >> ~/.profile
