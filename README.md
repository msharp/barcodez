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

## Deployment

The application container is hosted on AWS [App Runner](https://aws.amazon.com/apprunner/). Internally a service is run on the AWS ECS/FARGATE container infrastructure. 
App Runner adds an application load balancer as the entrypoint to access a service. 

In order to deploy a new application version, following steps are actioned:
- Build Docker image
- Tag and push Docker image to ECR
- Invoke an App Runner service update with new image version

Run `./deploy.sh` locally and select your deployment environment, or push to remote staging for invoking a deployment on Github Actions. 