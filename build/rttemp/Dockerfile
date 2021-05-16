FROM gcc:latest

ENV TZ=Europe/Budapest

WORKDIR /home/tcadm/

RUN \
    # sysadmin settings
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt update -y && \
    apt-get install librdkafka-dev -y

COPY source/rttemp .

RUN make all

CMD ["./rttimer", "real_time_data", "./configs/librdkafka.config"]