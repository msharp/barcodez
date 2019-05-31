# Using lightweight alpine image
FROM python:3.7-alpine

# install pipenv and create an app user
RUN apk update \
      && apk add --no-cache git openssh-client \
      && pip install pipenv \
      && addgroup -S -g 1001 app \
      && adduser -S -D -h /app -u 1001 -G app app

# install zint
RUN apk add --no-cache alpine-sdk cmake libpng libpng-dev \
			&& mkdir -p /app/zint \
      && cd /app/zint \
			&& git clone https://github.com/woo-j/zint.git . \
			&& mkdir build \
			&& cd build \
			&& cmake .. \
			&& make \
			&& make install

# Pillow dependencies
RUN apk --no-cache add jpeg-dev \
		 zlib-dev \
		 freetype-dev \
		 lcms2-dev \
		 openjpeg-dev \
		 tiff-dev \
		 tk-dev \
		 tcl-dev \
		 harfbuzz-dev \
		 fribidi-dev

# Creating working directory
RUN mkdir /app/src
WORKDIR /app/src
RUN chown -R app.app /app/

# Creating environment
USER app

# ensure libzint is in the path
ENV PATH="/usr/local/lib:${PATH}"

# Copy the Pipfile and Pipfile.lock file across separately into the container at /app
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Installs all packages specified in Pipfile.lock
RUN pipenv sync

# Copy the rest of the app
COPY . .

# the "--wsgi-disable-file-wrapper" option is to allow io.BytesIO objects
# to be served by uwsgi (https://github.com/unbit/uwsgi/issues/1126)
CMD ["pipenv", "run", "uwsgi", "--wsgi-disable-file-wrapper", "-c", "uwsgi.ini"]



