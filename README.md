# 5gla-automated-orthophotos

Aufsetzen S3 speicher:
All commands were performed as root, so there is no need for the sudo prefix

* * *

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
MINIO_ACCESS_KEY="Mso8cQTGAa3CDssBmh8tdWWol2Dy0qsa"
MINIO_SECRET_KEY="YWdOyIc7bgcuRw7XWC4R1u6YPA3DMJGp"
MINIO_VOLUMES="/usr/local/share/minio/"
MINIO_OPTS="-C /etc/minio --address 192.168.2.38:9000"
EOF
```

### start minio

```
systemctl start minio
```
