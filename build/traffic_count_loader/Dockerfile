ARG TCIoT_REGISTRY
FROM ${TCIoT_REGISTRY}/base_python3:1.0.0

WORKDIR /home/tcadm/

COPY system/ ./system
COPY source/schemas/ ./schemas
COPY source/tclib/ ./tclib
COPY source/influx_db_loader/influx_db_helper.py .
COPY source/influx_db_loader/influx_tc_message_loader.py .

CMD ["python3", "influx_tc_message_loader.py"]
