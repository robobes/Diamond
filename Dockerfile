FROM python:3.11-slim

# set working directory in container
WORKDIR /usr/src/app

# Copy and install packages
COPY CLOUD/DASH/requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

# Copy app folder to app folder in container
COPY CODE/DASH /usr/src/app/
COPY DATA/SHINY/regime_data.csv /usr/src/app/regime_data.csv

# Changing to non-root user
RUN useradd -m appUser
USER appUser


CMD exec gunicorn --bind :$PORT --log-level info --workers 1 --threads 8 --timeout 0 app:server
