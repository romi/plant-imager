FROM continuumio/anaconda3

RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libxi6

RUN wget https://download.blender.org/release/Blender2.81/blender-2.81a-linux-glibc217-x86_64.tar.bz2 && \
    tar -xvjf blender-2.81a-linux-glibc217-x86_64.tar.bz2 && \
    mv blender-2.81a-linux-glibc217-x86_64 /opt/blender

ENV PATH="/opt/blender:${PATH}"

RUN conda create -n lpyEnv python=3.7
RUN conda install -n lpyEnv -c conda-forge -c fredboudon openalea.lpy
RUN conda install -n lpyEnv -c conda-forge flask imageio

RUN git clone https://github.com/romi/romiscanner.git && \
    cd romiscanner/ && \
    python -m pip install .

RUN echo "conda activate lpyEnv" >> ~/.bashrc

CMD ["bin/bash", "-c"]
