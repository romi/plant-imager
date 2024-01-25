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
ENV USER_NAME="romi"
ENV USER_ID=1010
# Required by `pip`:
ENV PATH="${PATH}:/home/${USER_NAME}/.local/bin"
# Required by `romi_run_task`:
ENV ROMI_DB="/myapp/db"
# Required by `nvidia-container-runtime`
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
# Add Blender install path to PATH:
ENV PATH="/opt/blender:${PATH}"
# Defines URL to download blender from:
ENV BLENDER_URL="https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.93/blender-2.93.16-linux-x64.tar.xz"

# Expose the port to communicate with the blender server:
EXPOSE 9001

# Change Shell to 'bash', default is 'sh'
SHELL [ "/bin/bash", "-c" ]

RUN apt-get update && \
    # Install system dependencies:
    apt-get install -y --no-install-recommends \
    libgl1-mesa-dev libxi6 libc++-dev \
    emacs-nox && \
    # Clean cache:
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create a non-root user and give it rights over its "home" folder:
    adduser --disabled-password --gecos '' --uid ${USER_ID} ${USER_NAME} && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    # Create the folder used to mount the database:
    mkdir -p ${ROMI_DB} && \
    # Allow user to call conda:
    chown -R ${USER_NAME}: /opt/conda/ && \
    # Download Blender and move it to `/opt/blender`: \
    echo "Downloading Blender from '${BLENDER_URL}'..." && \
    wget --progress=bar ${BLENDER_URL} && \
    echo "Installing Blender in '/opt/blender'..." && \
    tar -xJf blender-2.93.16-linux-x64.tar.xz && \
    mv blender-2.93.16-linux-x64 /opt/blender && \
    rm blender-2.93.16-linux-x64.tar.xz && \
    echo "Installing Python dependencies for Blender..." && \
    /opt/blender/2.93/python/bin/python3.9 -m ensurepip && \
    /opt/blender/2.93/python/bin/python3.9 -m pip install markupsafe flask itsdangerous click werkzeug jinja2 imageio

ENV LD_LIBRARY_PATH="/opt/blender/lib"

# Change to non-root user:
USER ${USER_NAME}
# Change working directory:
WORKDIR /home/${USER_NAME}

# Copy the source files (repository):
COPY --chown=${USER_NAME} ./ plant-imager/

# Create the appropriate conda environment:
RUN conda install -y -n base conda-libmamba-solver && \
    conda config --set solver libmamba && \
    ## Create the `lpyEnv` environment:
    conda env create -y -n lpyEnv -f plant-imager/conda/lpy.yaml && \
    ## Clean conda cache:
    conda clean -y --all

# Activate conda usage from bash:
# https://pythonspeed.com/articles/activate-conda-dockerfile/
RUN conda init bash
SHELL [ "conda", "run", "-n", "lpyEnv", "/bin/bash", "-c" ]

# Install `plant-imager` dependencies (`plantdb` & `romitask`) & sources:
RUN cd plant-imager/ && \
    ## Install `plantdb` from sources:
    python3 -m pip install ./plantdb/ --no-cache-dir && \
    ## Install `romitask` from sources:
    python3 -m pip install -r ./romitask/requirements.txt --no-cache-dir && \
    python3 -m pip install ./romitask/ --no-cache-dir && \
    ## Install `plant-imager` from sources:
    python3 -m pip install . --no-cache-dir && \
    # Clean pip cache:
    python3 -m pip cache purge && \
    # Activate 'lpyEnv' conda env for interactive shell:
    echo "conda activate lpyEnv" >> ~/.bashrc && \
    # Activate 'lpyEnv' conda env for login shell:
    # This is used by 'docker/*/run.sh' when passing a command as argument
    echo "conda activate lpyEnv" >> ~/.profile && \
    # Add blender to executables:
    echo "export PATH=\$PATH:/opt/blender" >> ~/.profile && \
    # Make blender library accessible by python path:
    echo "export LD_LIBRARY_PATH=/opt/blender/lib" >> ~/.profile
