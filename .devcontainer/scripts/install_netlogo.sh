#!/bin/bash

# Define variables
NETLOGO_VERSION="6.1.0"
NETLOGO_TAR="NetLogo-$NETLOGO_VERSION-64.tgz"
NETLOGO_URL="https://ccl.northwestern.edu/netlogo/$NETLOGO_VERSION/$NETLOGO_TAR"
INSTALL_DIR="/opt/netlogo"

# Set up netlogo 'home' aka path, and version, as env vars, to use with pyNetLogo
echo "export NETLOGO_HOME=$INSTALL_DIR" >> ~/.bashrc
echo "export NETLOGO_VERSION=6.1" >> ~/.bashrc

# Install openjdk-8-jdk (Netlogo is supposed to have Java included but...)
DEBIAN_FRONTEND=noninteractive
apt-get update
ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime
apt-get install -y tzdata
dpkg-reconfigure --frontend noninteractive tzdata
apt-get install -y openjdk-8-jdk
echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" >> ~/.bashrc

# Download and extract NetLogo
echo "Downloading and extracting NetLogo..."
mkdir -p $INSTALL_DIR
wget -qO $NETLOGO_TAR $NETLOGO_URL
tar -xz -C $INSTALL_DIR --strip-components=1 -f $NETLOGO_TAR
rm $NETLOGO_TAR

# Set env var for JAVA_HOME - should prob happen automatically but not so

# Add to PATH, so we can simply call with `netlogo`
echo "export PATH=\$PATH:$INSTALL_DIR" >> ~/.bashrc

# Echo a happy response
echo "NetLogo installation completed successfully!"