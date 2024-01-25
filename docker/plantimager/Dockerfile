FROM continuumio/miniconda3
LABEL maintainer="Jonathan LEGRAND <jonathan.legrand@ens-lyon.fr>"
LABEL corresponding_author="Peter Hanappe <peter@romi-project.eu>"
LABEL project="Robotics for microfarms"
LABEL homepage="https://docs.romi-project.eu/documentation/"
LABEL repository="https://github.com/romi/plant-imager"
LABEL license="LGPL-3.0-or-later"
LABEL description="Plant Imager"

ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV USER_NAME="myuser"
ENV USER_ID=1000
# Required by `pip`:
ENV PATH="${PATH}:/home/${USER_NAME}/.local/bin"
# Required by `romi_run_task`:
ENV ROMI_DB="/myapp/db"

# Change Shell to 'bash', default is 'sh'
SHELL [ "/bin/bash", "-c" ]

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create a non-root user and give it rights over its "home" folder:
    adduser --disabled-password --gecos '' --uid ${USER_ID} ${USER_NAME} && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    # Create the folder used to mount the database:
    mkdir -p ${ROMI_DB} && \
    # Allow user to call conda:
    chown -R ${USER_NAME}: /opt/conda/

# Change to the non-root user
USER ${USER_NAME}
# Change working directory
WORKDIR /home/${USER_NAME}

# Create the appropriate conda python environment
RUN conda create -n plantimager python=3.7

# Activate conda usage from shell:
RUN conda init bash
SHELL [ "conda", "run", "-n", "plantimager", "/bin/bash", "-c" ]

# Copy the source files (repository):
COPY --chown=${USER_NAME}:${GROUP_NAME} ./ plant-imager/
# Install plant-imager from host's local source files
RUN cd plant-imager/ && \
    python3 -m pip install -r ./plantdb/requirements.txt --no-cache-dir && \
    python3 -m pip install ./plantdb/ --no-cache-dir && \
    python3 -m pip install -r ./romitask/requirements.txt --no-cache-dir && \
    python3 -m pip install ./romitask/ --no-cache-dir && \
    python3 -m pip install . --no-cache-dir

# For interactive shell
RUN echo "conda activate plantimager" >> ~/.bashrc

# For login shell, used in run.sh when passing a script as argument
RUN echo "conda activate plantimager" >> ~/.profile
