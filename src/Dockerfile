###########
ARG PYTHON_IMAGE=python:3.10-slim
# pull official base image
FROM ${PYTHON_IMAGE}

# create the appropriate directories
ENV APP_HOME=/usr/src/app

# set work directory
WORKDIR $APP_HOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc
RUN apt-get install -y libcurl4-openssl-dev libssl-dev python3-dev
RUN apt-get install -y netcat-traditional

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# ssh
#ENV SSH_PASSWD "root:Docker!"
#RUN apt-get update \
#        && apt-get install -y --no-install-recommends dialog \
#        && apt-get update \
#	&& apt-get install -y --no-install-recommends openssh-server \
#	&& echo "$SSH_PASSWD" | chpasswd 

#COPY sshd_config /etc/ssh/

# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .

RUN chmod u+x /usr/src/app/entrypoint.sh
EXPOSE 8000 2222

# run entrypoint.azure.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]