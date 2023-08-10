#
FROM continuumio/miniconda3:4.12.0

# update environment
COPY ./extractor/environment.yml /source/environment.yml
COPY ./extractor/environment.yml /source/environment_lock.yml

# RUN conda env create -f /source/environment.yml
RUN conda env create -f /source/environment_lock.yml
RUN conda clean -ay

# dependencies for OCC
RUN apt-get update
RUN apt-get install --no-install-recommends -y \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Add bullseye backport repo
RUN printf "# /etc/apt/sources.list.d/bullseye-backports.list \n deb http://deb.debian.org/debian bullseye-backports main contrib non-free \n" >> /etc/apt/sources.list
RUN apt update
RUN apt install --no-install-recommends -t bullseye-backports -y kicad && rm -rf /var/lib/apt/lists/*

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "extractor", "/bin/bash", "-c"]

# remove libraries which are not needed but have a GPL license
RUN conda remove --force ffmpeg freetype

# remove libraries to save some memory
RUN conda remove --force vtk

# copy files
COPY ./extractor/ /source/extractor
COPY ./common /source/common

# remove debug output files
RUN rm -rf /source/extractor/plots
RUN rm -rf /source/extractor/plotting

# set working directory
WORKDIR /source

# environment variables
ENV KICAD_PYTHON_EXEC="/opt/conda/bin/python3.9"
ENV PYTHONPATH="/usr/lib/python3/dist-packages/"

# start uvicorn
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "extractor", "uvicorn","extractor.__main__:app",\
"--host", "0.0.0.0", "--port", "8080"]

