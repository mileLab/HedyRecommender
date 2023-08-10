# Base image
FROM python:3.9

# copy requirements file
COPY ./recommender/requirements.txt /source/requirements.txt
COPY ./recommender/requirements.txt /source/requirements_lock.txt

# install requirements
# RUN pip install --no-cache-dir --upgrade -r /source/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /source/requirements_lock.txt

# copy source files
COPY ./recommender /source/recommender
COPY ./common /source/common

# set working directory
WORKDIR /source

# set environment variables
ENV RECOMMENDER_TYPE_DEFINITION="Meta_Fields_Recommender.csv"

# start webserver
CMD ["uvicorn", "recommender.__main__:app", "--host", "0.0.0.0", "--port", "8050"]
