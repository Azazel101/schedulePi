#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

apt-get install -y python3-pip git

cd /

git clone https://github.com/Azazel101/schedulePi.git

cd schedulePi

pip3 install -r requirements.txt
python3 run.py
