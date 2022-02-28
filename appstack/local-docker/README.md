Overview
===

This directory contains the configuration and scripts to run the stack in a Docker installed on the local machine. It can be used for both production
environments and local development/testing (this is determined by the presence of the EXT_DOMAIN environment veriable, see Installation).

When in production mode the stack exposes ports 80 and 443 to serve requests from the Internet. [Caddy 2](https://caddyserver.com/) is used as the
front-facing proxy. It supports zero-configuration automatic HTTPS including obtaining and refreshing certificates. When using this mode please make
sure that ports 80 and 443 are free and open from the Internet.

When in development mode (i.e. without EXT_DOMAIN set) it exposes the services on the local machine at individual ports: 8080 is used for MedCATTrainer,
8081 for Doccano and 8082 for sqlpad.


Prerequisits
===

All configuration tasks must be performed from a Linux machine that has the following:

 - Debian 10 or similar (it can be different but this guide assumes Debian 10).
 - python 3.7 or higher (`apt-get install python3`)
 - make (`apt-get install make`)
 - [Docker Engine](https://docs.docker.com/engine/install/)
 - docker-compose (`apt-get install docker-compose`)

For production mode you need a DNS domain under your control. The following DNS records must be added to the DNS zone:

```
medcattrainer            IN 600 CNAME <this machine's public DNS name>.
doccano                  IN 600 CNAME <this machine's public DNS name>.
sqlpad                   IN 600 CNAME <this machine's public DNS name>.
```

Don't forget the leading dots.

Installation
===

 - Make sure that the current user can manage Docker:

```shell
sudo usermod -aG docker ${USER}
```

Then logout and login again.

 - In the current folder, run `./generate_env.sh`. This will create a skeleton `env` file which contains the required environment variables most of which will
be pre-populated and passwords randomly generated.

 - Review the generated `env` file and fill in the required parameters.

 - Run `build_service_containers.sh`

 - Run `./build_scrapers_containers.sh`

 - Run `./docker_compose_up.sh`. If it fails with `StoreError('Credentials store docker-credential-secretservice exited with "Cannot autolaunch D-Bus without X11 $DISPLAY".')`
remove ~/.docker/config.json and try again.

 - Wait until the services have fully started. They should be available at the corresponding URLs (either the external or internal ones) and you should
be able to log in.

 - Run `./create_projects.sh`. This will Create Doccano and MedCAT projects which will serve as the destination point for the imported documents.

From this point you should be able to run the scrapers. See ../../scrapers/README.md, section 'Running Scrapers' for details.

Starting
===

To start already configured services run `./docker_compose_up.sh`

Stopping
===

To stop the services run `./docker_compose_down.sh`

Connecting to services using SSH port forwarding
===

If the Internet acces has been disabled (by unsetting the EXT_DOMAIN in the `env` file) it's possible to access the services remotely using the SSH port
forwarding:

```shell
ssh -L 8080:localhost:8080 -L 8081:localhost:8081 -L 8082:localhost:8082 -L 8083:localhost:8083 user@host
```

After that the services will become available at localhost as follows:

 - http://localhost:8080 -- MedCATTrainer (if enabled, see `ENABLE_MEDCAT_TRAINER` environment variable)
 - http://localhost:8081 -- Doccano
 - http://localhost:8082 -- sqlpad
 - http://localhost:8083 -- BRAT

Note that these ports are available even when Internet access is enabled.
