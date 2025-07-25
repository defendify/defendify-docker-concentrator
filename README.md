# Defendify Log Concentrator and Forwarder for MDR

The files in this repository are used to build and create a Docker container running a Rsyslog as a concentrator to forward events to Defendify.

To catch incoming events and apply the right intake key, this image processes each source on a specific TCP/UDP port.

The build is based on Ubuntu 22.04 and will install all the required components.

## Prerequisites
To be able to run the container you need:

* A x86-64 Linux host using one of these templates:
  | Number of assets |  vCPUs |  RAM (GB) | Disk size (GB) | Defendify concentrator settings                |
  |------------------|:------:|:---------:|:--------------:|:-------------------------------------------:|
  | 1000             |    2   |   4       |      200       |  MEMORY_MESSAGES=2000000 / DISK_SPACE=180g  |
  | 10 000           |    4   |   8       |      1000      |  MEMORY_MESSAGES=5000000 / DISK_SPACE=980g  |
  | 50 000           |    6   |   16      |      5000      |  MEMORY_MESSAGES=12000000 / DISK_SPACE=4980g |

> [!IMPORTANT]
> These data are recommendations based on standards and observed averages on Defendify, so they may change depending on use cases.

* Latest version of Git. You will find all the installation processes on the [official website](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).
* Latest version of Docker Engine. You will find all the installation processes on the [official website](https://docs.docker.com/engine/install/).
> [!WARNING]
> Make sure you follow the Docker Linux post-installation steps. 
* INBOUND TCP or UDP flows opened between the systems/applications and the concentrator on the ports of your choice
* OUTBOUND TCP flow opened towards:
  * **USA1** — intake.mdr.defendify.com on port 10514 

## Docker-compose folder
The docker-compose folder contains the two files needed to start the container with docker compose: `docker-compose.yml` and `intakes.yaml`

### intakes.yaml file
The `intakes.yaml` file is used to tell Rsyslog what ports and intake keys to use.
In the `intakes` key, specify:
* a name (it has nothing to do with Defendify, it can be a random value)
* the protocol, tcp or udp
* a port, to process incoming events
* the intake key

**Example**:
```yaml
---
intakes:
- name: TCP-Example-1
  protocol: tcp
  port: 20516
  intake_key: INTAKE_KEY_FOR_TCP-EXAMPLE-1
- name: UDP-Example-1
  protocol: udp
  port: 20517
  intake_key: INTAKE_KEY_FOR_UDP-EXAMPLE-1
- name: TCP-Example-2
  protocol: tcp
  port: 20518
  intake_key: INTAKE_KEY_FOR_TCP-EXAMPLE-2
```

#### Debug 
A debug variable is available in order to debug a specific intake, for example 
```yaml
---
intakes:
- name: TCP-Example-1
  protocol: tcp
  port: 20516
  intake_key: INTAKE_KEY_FOR_TCP-EXAMPLE-1
  debug: true
- name: UDP-Example-1
  protocol: udp
  port: 20517
  intake_key: INTAKE_KEY_FOR_UDP-EXAMPLE-1
- name: TCP-Example-2
  protocol: tcp
  port: 20518
  intake_key: INTAKE_KEY_FOR_TCP-EXAMPLE-2
```

When debug is set to true, the raw event received and the output message will be printed in STDOUT. Each one will be respectively identified using tags: : [Input $INTAKE_KEY] & [Output $INTAKE_KEY]

### Docker-compose file
To ease the deployment, a `docker-compose.yml` file is suggested and a template is given.

#### Environment variables
This image uses two environment variables to customize the container. These variables are used to define a queue for incoming logs in case there is a temporary issue in transmitting events to Defendify. The queue stores messages in memory up to a certain number of events and then store them on disk.

```yaml
environment:
    - MEMORY_MESSAGES=2000000
    - DISK_SPACE=180g
    - REGION=USA1
```
* `MEMORY_MESSAGES=2000000` means the queue is allowed to store up to 2,000,000 messages in memory. If we consider a message size is 1.2KB, then you will use 2,4GB of RAM memory (2000000 * 1.2KB = 2.4GB).
* `DISK_SPACE=180g` means the queue is allowed to store on disk up to 180 gigs of messages.
* `REGION=USA1` is the region where to send the logs. Currently only the `USA1` option is available, but this here for futureproofing.

[Here](#prerequisites) you will find recommendations to set these variables based on the number of assets. You can also define your own values, which should be chosen according to your virtual machine's template.

#### Ports
Ports in Docker are used to perform port forwarding between the host running the container and the container itself.
```yaml
ports:
    - "20516-20518:20516-20518"
```

`20516-20518:20516-20518` means that every packets coming through the TCP port `20516`, `20517` or `20518` to the host will be forwarded to the Rsyslog container on the port `20516`, `20517` or `20518`. Please adapt these values according to the `intakes.yaml` file.

#### Volumes

Volumes are used to share files and folders between the host and the container.

```yaml
volumes:
    - ./intakes.yaml:/intakes.yaml
    - ./disk_queue:/var/spool/rsyslog
```

* `./intakes.yaml:/intakes.yaml` is used to tell Rsyslog what ports and intake keys to use.
* `./disk_queue:/var/spool/rsyslog` is used when the rsyslog queue stores data on disk. The mapping avoids data loss if logs are stored on disk and the container is deleted.

# Installation Process

This is the general process to follow to get the Defendify Log Concentrator and Forwarder installed. Advanced directions are included after.

1. Clone the repo with git and enter the directory:
```bash
git clone https://github.com/defendify/defendify-docker-concentrator.git && cd defendify-docker-concentrator
```
2. Pull the pre-made docker image:
```bash
sudo docker pull ghcr.io/defendify/defendify-docker-concentrator:2.7.1b
```
3. Enter the docker-compose directory:
```bash
cd docker-compose
```
> [!IMPORTANT]  
> Files in this directory will need administrator access to edit. Defendify will work with you to get this set up if you need assistance.

4.  Edit the docker-compose.yml file to fit your specifications:
```bash
sudo nano docker-compose.yml
```
5. Edit the intakes.yaml file to fit your specifications:
```bash
sudo nano intakes.yaml
```
6. Once those files are edited, you can run the image via docker compose:
```bash
sudo docker compose up
```

## Usage
To start (and create if needed) the container to run in the background (a.k.a. detached):
```bash
sudo docker compose up -d
```

To start (and create if needed) the container in interactive mode:
```bash
sudo docker compose up
```

To view container logs when using the Debug variable:
```bash
sudo docker compose logs
```

To view container logs for a specific intake when using the Debug variable:
```bash
sudo docker compose logs | grep "YOUR_INTAKE_KEY"
```

To stop the container:
```bash
sudo docker compose stop
```

To delete the container (container needs to be stopped):
```bash
sudo docker compose rm
```

## Additional configuration options

There are additional options you can tweak in the `docker-compose.yml` file within `/docker-compose`.

```yaml
restart: always
pull_policy: always
```

* `restart: always`: this line indicates to restart the concentrator every time it stops. That means if it crashes, if you restart Docker or if you restart the host, the concentrator will start automatically.
* `pull_policy: always`: docker compose will always try to pull the image from the registry and check if a new version is available for the tag specified.

## Configure TLS for an Intake

Sending logs between the forwarder and Defendify is always encrypted with TLS. However, by default, if you use the `tcp` or `udp` protocol option in your intake configuration, the logs between your devices and the forwarder will not be encrypted. This section shows you how to configure TLS between a source and the forwarder.

### Configuration of the docker-compose.yml

Activating TLS requires setting up an encryption key, a certificate, and a CA certificate. These should be placed in the `./certs` directory within the forwarder's directory.
Therefore it is necessary to mount this volume. Add the following line to the configuration:

```yaml
volumes:
    - ./certs:/certs
    [...]
```

### Creating the Key and Certificate

We will now create the key and certificate that will be used for encryption. In this case, we will create a self-signed certificate, meaning that the server certificate and the CA (Certificate Authority) certificate will be the same. If you have expertise in managing certificates, you can create a certificate signed by a real CA.

**Step one**: Create the directory and navigate to it:

```
mkdir certs && cd certs
```

**Step two**: Install OpenSSL

#### Debian, Ubuntu

```bash
sudo apt update
sudo apt install -y openssl
```

#### Fedora, Red Hat, CentOS (yum)

```bash
sudo yum update
sudo yum install -y openssl
```

#### Fedora, Red Hat, CentOS (dnf)

```bash
sudo dnf update
sudo dnf install -y openssl
```

Step three: Create the key and certificate:

```
openssl req -x509 \
            -sha256 -days 1825 \
            -nodes \
            -newkey rsa:4096 \
            -keyout server.key -out server.crt
```

- `openssl req`: Launches the process to create a Certificate Signing Request (CSR) or a self-signed certificate.
- `-x509`: This option tells OpenSSL to generate a self-signed certificate rather than a CSR.
- `-sha256`: Specifies that the SHA-256 hashing algorithm should be used for the certificate's signature.
- `-days 1825`: Sets the certificate's validity period to 1825 days, which corresponds 5 years.
- `-nodes`: This stands for "no DES" and indicates that the private key should not be encrypted, meaning no password will be required to use the private key.
- `-newkey rsa:4096`: Generates a new RSA key pair of 4096 bits in length, and simultaneously creates a certificate request using this key pair.
- `-keyout server.key`: Specifies the file where the generated private key should be saved. In this case, it will be saved to `server.key`.
- `-out server.crt`: Specifies the file where the generated self-signed certificate should be saved. In this case, it will be saved to `server.crt`.

**Step four**: Change permissions on the files

```
chmod 600 server.key server.crt
```

## OPTIONAL: Build the image
> [!NOTE]  
> If you don't want to use the image available at `ghcr.io/defendify/defendify-docker-concentrator`, you can also build the image on your own.

To build the image:
```bash
docker build . -t defendify-docker-concentrator:latest
```

> [!CAUTION]
> Be sure to adapt the `docker-compose.yml` accordingly and change `image: ghcr.io/defendify/defendify-docker-concentrator:x` to `image: defendify-docker-concentrator:latest` if you use this method.
