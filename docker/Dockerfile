FROM continuumio/miniconda3


RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libxi6 \
    gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN conda create -n lpyEnv python=3.7
SHELL [ "conda", "run", "-n", "lpyEnv", "/bin/bash", "-c" ]

RUN conda install -n lpyEnv -c conda-forge -c fredboudon openalea.lpy
RUN conda install -n lpyEnv -c conda-forge flask imageio

RUN conda install -c conda-forge toml
RUN conda install -c conda-forge luigi

ENV BLENDER_URL=https://download.blender.org/release/Blender2.81/blender-2.81a-linux-glibc217-x86_64.tar.bz2
RUN wget --progress=bar $BLENDER_URL && \
    tar -xjf blender-2.81a-linux-glibc217-x86_64.tar.bz2 && \
    mv blender-2.81a-linux-glibc217-x86_64 /opt/blender && \
    rm blender-2.81a-linux-glibc217-x86_64.tar.bz2

WORKDIR /home/data/

ENV PATH="/opt/blender:${PATH}"
ENV LD_LIBRARY_PATH "/opt/blender/lib"

ARG ROMISCAN_BRANCH=dev
ARG ROMIDATA_BRANCH=dev
ARG ROMISCANNER_BRANCH=master

RUN git clone --branch $ROMISCAN_BRANCH https://github.com/romi/romiscan && \
    git clone --branch $ROMIDATA_BRANCH https://github.com/romi/romidata && \
    git clone --branch $ROMISCANNER_BRANCH https://github.com/romi/romiscanner && \
    python -m pip install ./romidata/ --no-cache-dir && \
    python -m pip install ./romiscanner/ --no-cache-dir && \
    python -m pip install ./romiscan/ --no-cache-dir

RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/markupsafe/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/flask/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/itsdangerous/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/click/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/werkzeug/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/jinja2/ /opt/blender/2.81/python/lib/python3.7/site-packages/
RUN cp -r /opt/conda/envs/lpyEnv/lib/python3.7/site-packages/imageio/ /opt/blender/2.81/python/lib/python3.7/site-packages/

EXPOSE 9001

RUN echo "conda activate lpyEnv" >> ~/.bashrc

CMD ["bin/bash", "-c"]
