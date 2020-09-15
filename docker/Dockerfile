FROM continuumio/miniconda3

ARG USER_NAME=scanner
ARG USER_ID=1000
ARG GROUP_ID=1000

# Change shell to 'bash', default is 'sh'
SHELL ["/bin/bash", "-c"]

ENV DB_LOCATION="/home/${USER_NAME}/db"
ENV PATH=$PATH:"/home/${USER_NAME}/.local/bin"
ENV PATH="/opt/blender:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libxi6 \
    gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create a non-root user and give it rights over its "home folder"
    addgroup --gid $GROUP_ID $USER_NAME && \
    adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID $USER_NAME && \
    mkdir $DB_LOCATION && \
    chown -R ${USER_NAME}: /home/${USER_NAME} && \
    chown -R ${USER_NAME}: /opt/conda

ENV BLENDER_URL=https://download.blender.org/release/Blender2.81/blender-2.81a-linux-glibc217-x86_64.tar.bz2
RUN wget --progress=bar $BLENDER_URL && \
    tar -xjf blender-2.81a-linux-glibc217-x86_64.tar.bz2 && \
    mv blender-2.81a-linux-glibc217-x86_64 /opt/blender && \
    rm blender-2.81a-linux-glibc217-x86_64.tar.bz2

# Change to non-root user:
USER ${USER_NAME}

# Change working directory:
WORKDIR /home/${USER_NAME}

COPY romiscanner.yaml romiscanner.yaml
# TODO: To be even faster on conda env creation & setup, write a YAML environment recipe!
RUN conda env create -f romiscanner.yaml && \
    conda clean -a -y

ARG ROMISCAN_BRANCH=dev
ARG ROMIDATA_BRANCH=dev
ARG ROMISCANNER_BRANCH=master

RUN git clone --branch $ROMISCAN_BRANCH https://github.com/romi/romiscan && \
    git clone --branch $ROMIDATA_BRANCH https://github.com/romi/romidata && \
    git clone --branch $ROMISCANNER_BRANCH https://github.com/romi/romiscanner && \
    python -m pip install ./romidata/ --no-cache-dir && \
    python -m pip install ./romiscanner/ --no-cache-dir && \
    python -m pip install ./romiscan/ --no-cache-dir

RUN echo "conda activate lpy" >> ~/.bashrc
