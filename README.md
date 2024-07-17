# 5gla-automated-orthophotos
All commands were performed as root, so there is no need for the sudo prefix

* * *

## Setup S3 storage:

### Create user for minio

```
useradd -r minio-user -s /sbin/nologin
```

### download minio, create workings directories and set permissions

```
cd /tmp/
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
chown minio-user:minio-user ./minio
mv minio /usr/local/bin/
mkdir /usr/local/share/minio
chown minio-user:minio-user /usr/local/share/minio
mkdir /etc/minio
chown minio-user:minio-user /etc/minio
```

### Install systemd service

```
curl -O https://raw.githubusercontent.com/minio/minio-service/master/linux-systemd/minio.service
mv minio.service /etc/systemd/system
systemctl daemon-reload
systemctl enable minio
```

### create env used by minio.service

```
cat << EOF >/etc/default/minio
MINIO_ACCESS_KEY="REPLACE_ME"
MINIO_SECRET_KEY="REPLACE_ME"
MINIO_VOLUMES="/usr/local/share/minio/"
MINIO_OPTS="-C /etc/minio --address REPLACE_ME"
EOF
```

### start minio

```
systemctl start minio
```
* * *

## Setup ClusterODM and NodeODM 
Docker and docker-compose are required on each VM

### Install Docker-CE

```bash
curl -fsSL https://get.docker.com | sh >> ~/docker-script-install.log 2>&1
```

### Install docker-compose

```bash
VERSION=$(curl --silent https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*\d')
sudo curl -SL https://github.com/docker/compose/releases/download/$VERSION/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

* * *

## Install ClusterODM on a debian 12 VM

```bash
ClusterODM ip address: "IP_ADDRESS_CLUSTER_ODM"
```

### Clone git repo to get docker-compose.yml

```bash
git clone https://github.com/OpenDroneMap/ClusterODM
cd ClusterODM/
```

### Edit docker-compose.yml and add tokens (generate new ones) to all services

```bash
nano docker-compose.yml
```

```docker
version: '2.1'
services:
  nodeodm-1:
    image: opendronemap/nodeodm
    container_name: nodeodm-1
    ports:
      - "3000"
    restart: always
    environment:
      - NODE_ENV=production
      - SECRET_KEY="REPLACE_ME"
      - API_TOKEN="REPLACE_ME"
  clusterodm:
    image: opendronemap/clusterodm
    container_name: clusterodm
    ports:
      - "4000:3000"
      - "8080:8080"
      - "10000:10000"
    volumes:
      - ./docker/data:/var/www/data
    restart: always
    environment:
      - NODE_ENV=production
      - SECRET_KEY="REPLACE_ME"
      - API_TOKEN="REPLACE_ME"

    depends_on:
      - nodeodm-1
```

Don’t delete the “nodeodm-1” service which is necessary to run the whole cluster. Also change the restart line to always.

### Spin everything up

```bash
docker-compose up -d
```

### Create a new nodeodm debian 12 VM

```bash
nodeodm-1 ip address: "IP_ADDRESS_NODE_1"
```

### Create a new docker-compose.yml with the key and token from the ClusterODM VM

```bash
nano docker-compose.yml
```

```docker
version: '2.1'
services:
  nodeodm-1:
    image: opendronemap/nodeodm
    container_name: nodeodm-1
    ports:
      - "3001:3000"
    restart: always
    environment:
      - NODE_ENV=production
      - SECRET_KEY="REPLACE_ME"
      - API_TOKEN="REPLACE_ME"
```

### Spin everything up

```
docker-compose up -d
```

### Back on ClusterODM add the new node to ClusterODM

```bash
telnet localhost 8080
node add "IP_ADDRESS_NODE_1" 3001
node list
quit
```

## Setup NodeOdm Client

### Install Git and Clone repository
```
sudo apt-get install git 
git clone https://github.com/vitrum-connect/5gla-automated-orthophotos.git
```

### Install  Python, PIP and Virtual Environment
```
sudo apt-get install python3 python3-pip python3-venv
```

### Open Port
```
sudo apt-get install ufw
sudo ufw allow 8000/tcp
```

### Setup environment
```
sudo python3 -m venv fivegla_env
source fivegla_env/bin/activate
```
### Install Dependencys
```
pip install fastapi uvicorn
pip install requests
```

### Configure Client
Configure the config.json to set the image directory, the API key and the Nodeodm endpoint URL.

### Start Script
uvicorn main:app --host 0.0.0.0 --port 8000
