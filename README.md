# Barcodez

_The z is for Zint._

Barcode server using the [Zint](http://www.zint.org.uk/) project via Python.

Uses [Falcon](https://falcon.readthedocs.io) and [uWSGI](https://uwsgi-docs.readthedocs.io) to serve barcode images generated in-memory.

## Run it

In development, using gunicorn:

    pipenv run gunicorn wsgi:application

or uWSGI:

    pipenv run uwsgi --wsgi-disable-file-wrapper -c uwsgi_dev.ini

Or in the Docker container, with:

    docker run -p 8000:8000 barcodez





