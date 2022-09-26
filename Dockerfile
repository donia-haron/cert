# Python image to use.
FROM python:3.9
RUN apt-get update
RUN apt-get -f install

RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation  libnss3 lsb-release xdg-utils libgbm1

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

ENV PYTHONUNBUFFERED True

## Set the working directory to /app
#WORKDIR /app

# copy the requirements file used for dependencies
#COPY requirements.txt .

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./


# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN pip install gunicorn

# Copy the rest of the working directory contents into the container at /app
#COPY . .

# Run app.py when the container launches
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
