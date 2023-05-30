FROM continuumio/miniconda3
LABEL maintainer="Jonathan LEGRAND <jonathan.legrand@ens-lyon.fr>"
LABEL corresponding_author="Peter Hanappe <peter@romi-project.eu>"
LABEL project="Robotics for microfarms"
LABEL homepage="https://docs.romi-project.eu/documentation/"
LABEL repository="https://github.com/romi/plant-imager"
LABEL license="LGPL-3.0-or-later"
LABEL description="Virtual Plant Imager"

ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV USER_NAME="myuser"
ENV USER_ID=1000
# Required by `pip`:
ENV PATH="${PATH}:/home/${USER_NAME}/.local/bin"
# Required by `romi_run_task`:
ENV DB_LOCATION="/myapp/db"
# Required by `nvidia-container-runtime`
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
# Add Blender install path to PATH:
ENV PATH="/opt/blender:${PATH}"
# Defines URL to download blender from:
ENV BLENDER_URL="https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.93/blender-2.93.16-linux-x64.tar.xz"

# Change Shell to 'bash', default is 'sh'
SHELL [ "/bin/bash", "-c" ]

RUN apt-get update && \
    # Install dependencies
    apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libxi6 \
    libc++-dev \
    emacs-nox \
    gcc \
    python3.9-dev && \
    # Clean apt and its cache
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create a non-root user and give it rights over its "home" folder:
    adduser --disabled-password --gecos '' --uid ${USER_ID} ${USER_NAME} && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    # Create the folder used to mount the database:
    mkdir -p ${DB_LOCATION} && \
    # Allow user to call conda:
    chown -R ${USER_NAME}: /opt/conda/ && \
    # Download Blender and move it to `/opt/blender`:
    wget --progress=bar ${BLENDER_URL} && \
    tar -xJf blender-2.93.16-linux-x64.tar.xz && \
    mv blender-2.93.16-linux-x64 /opt/blender && \
    rm blender-2.93.16-linux-x64.tar.xz

ENV LD_LIBRARY_PATH="/opt/blender/lib"

# Change to non-root user:
USER ${USER_NAME}
# Change working directory:
WORKDIR /home/${USER_NAME}

# Create the appropriate conda environment:
RUN conda install -y mamba -n base -c conda-forge && \
    conda create -y -n lpyEnv python=3.9 && \
    mamba install -y -n lpyEnv -c conda-forge -c open3d-admin -c fredboudon flask imageio toml openalea.lpy open3d && \
    conda clean -y --all

USER root
# Copy some Python libraries to Blender's Python `site-packages`:
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/markupsafe/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/flask/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/itsdangerous/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/click/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/werkzeug/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/jinja2/ /opt/blender/2.93/python/lib/python3.9/site-packages/ && \
    cp -r /opt/conda/envs/lpyEnv/lib/python3.9/site-packages/imageio/ /opt/blender/2.93/python/lib/python3.9/site-packages/
# TODO: It would be "cleaner" to install these packages by pip with `/opt/blender/2.93/python/bin/python`
# /opt/blender/2.93/python/bin/python -m ensurepip
# /opt/blender/2.93/python/bin/python -m pip install markupsafe flask itsdangerous click werkzeug jinja2 imageio


# Switch back to non-root user
USER ${USER_NAME}
# Activate conda usage from shell:
RUN conda init bash
SHELL [ "conda", "run", "-n", "lpyEnv", "/bin/bash", "-c" ]

# Copy the source files (repository):
COPY --chown=${USER_NAME}:${GROUP_NAME} ./ plant-imager/
# Install plant-imager from host's local source files
RUN cd plant-imager/ && \
    python3 -m pip install -r ./plantdb/requirements.txt --no-cache-dir && \
    python3 -m pip install ./plantdb/ --no-cache-dir && \
    python3 -m pip install -r ./romitask/requirements.txt --no-cache-dir && \
    python3 -m pip install ./romitask/ --no-cache-dir && \
    python3 -m pip install . --no-cache-dir

EXPOSE 9001

# For interactive shell
RUN echo "conda activate lpyEnv" >> ~/.bashrc
# For login shell, used in run.sh when passing a script as argument
RUN echo "conda activate lpyEnv" >> ~/.profile
RUN echo "export PATH=\$PATH:/opt/blender" >> ~/.profile
RUN echo "export LD_LIBRARY_PATH=/opt/blender/lib" >> ~/.profile
