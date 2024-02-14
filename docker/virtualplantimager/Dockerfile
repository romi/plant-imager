FROM continuumio/miniconda3
LABEL maintainer="Jonathan LEGRAND <jonathan.legrand@ens-lyon.fr>"
LABEL corresponding_author="Peter Hanappe <peter@romi-project.eu>"
LABEL project="Robotics for microfarms"
LABEL homepage="https://docs.romi-project.eu/"
LABEL repository="https://github.com/romi/plant-imager"
LABEL license="LGPL-3.0-or-later"
LABEL description="Virtual Plant Imager"

ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV USER_NAME="romi"
ENV USER_ID=1010

# Required by `nvidia-container-runtime`
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# Required by `pip`:
ENV PATH="${PATH}:/home/${USER_NAME}/.local/bin"

# Defines URL to download blender from:
ENV BLENDER_URL="https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.93/blender-2.93.16-linux-x64.tar.xz"
# Defines Blender installation path:
ENV BLENDER_PATH="/opt/blender"
# Add Blender install path to PATH:
ENV PATH="${BLENDER_PATH}:${PATH}"

# Required by `romi_run_task`:
ENV ROMI_DB="/myapp/db"

# Expose the port to communicate with the blender server:
EXPOSE 9001

RUN apt-get update && \
    # Install system dependencies:
    apt-get install -y --no-install-recommends \
      libgl1-mesa-dev \
      libxi6 \
      libc++-dev && \
    # Clean cache:
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create a non-root user and create a "home" folder for it:
    adduser --disabled-password --gecos '' --uid ${USER_ID} ${USER_NAME} && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    # Create the folder used to mount the database:
    mkdir -p ${ROMI_DB} && \
    touch ${ROMI_DB}/romidb && \
    chown -R ${USER_NAME} ${ROMI_DB} && \
    # Allow user to call conda:
    chown -R ${USER_NAME}: /opt/conda/ && \
    # Download Blender and move it to `/opt/blender`: \
    echo "Downloading Blender from '${BLENDER_URL}'..." && \
    wget --progress=bar:force:noscroll ${BLENDER_URL} && \
    echo "Installing Blender in '${BLENDER_PATH}'..." && \
    mkdir -p ${BLENDER_PATH} && \
    tar -xJf blender-2.93.16-linux-x64.tar.xz --directory ${BLENDER_PATH} --strip-components=1 && \
    rm blender-2.93.16-linux-x64.tar.xz && \
    # Give 'r+w' rights over Blender's embedded Python directory to the non-root user:
    chown -R ${USER_NAME} ${BLENDER_PATH}/2.93/python/

# Change to non-root user:
USER ${USER_NAME}
# Change working directory:
WORKDIR /home/${USER_NAME}

# Copy the source files (repository):
COPY --chown=${USER_NAME} ./ plant-imager/

RUN echo "\n\n# Installing dependencies for Blender's embedded Python..." && \
    python3 -m pip \
      --python ${BLENDER_PATH}/2.93/python/bin/python3.9 \
      install --no-cache-dir \
      --prefix ${BLENDER_PATH}/2.93/python/ \
      plant-imager/.[virtual] && \
    conda install -y -n base conda-libmamba-solver && \
    conda config --set solver libmamba && \
    echo "\n\n# Installing LPY dependencies in the 'base' environment..." && \
    conda install -y -n base "python >=3.8,<=3.11" flask imageio toml openalea.lpy -c conda-forge -c fredboudon && \
    ## Clean conda cache:
    conda clean -y --all && \
    echo "\n\n# Installing 'plant-imager' and dependencies..." && \
    echo "\n\n## Installing 'plantdb' from sources..." && \
    python3 -m pip install --no-cache-dir plant-imager/plantdb/ && \
    echo "\n\n## Installing 'romitask' from sources..." && \
    python3 -m pip install --no-cache-dir plant-imager/romitask/ && \
    echo "\n\n## Installing 'plant-imager' from sources..." && \
    python3 -m pip install --no-cache-dir plant-imager/ && \
    # Clean pip cache:
    python3 -m pip cache purge && \
    # Change `umask` to be able to write files and directory with 'r+w' as group rights (else just 'r'):
    echo "umask 002" >> .bashrc
