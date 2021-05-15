FROM ubuntu:18.04

ENV TZ=Europe/Budapest

RUN \
    # sysadmin settings
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    \
    # install some sysadmin stuff
    apt-get update && \
    apt-get install -y vim mc less tzdata && \
    apt-get install -y telnet && \
    apt-get install -y git && \
    apt-get install ffmpeg libsm6 libxext6  -y && \
    \
    # install python stuff
    apt-get install -y python3 python3-pip && \
    pip3 install --upgrade pip && \
    #pip3 install --upgrade setuptools pip && \
    pip3 install pyyaml && \
    pip3 install scikit-build && \
    pip3 install cmake && \
    pip3 install jsonschema && \
    pip3 install apscheduler && \
    pip3 install requests && \
    pip3 install confluent-kafka==1.5.0 && \
    pip3 install python-dateutil && \
    pip3 install influxdb && \
    pip3 install python-firebase && \
    pip3 install imutils && \
    pip3 install numpy && \
    pip3 install opencv-python && \
    pip3 install numba

WORKDIR /home/tcadm