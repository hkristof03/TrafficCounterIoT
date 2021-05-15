ARG TCIoT_REGISTRY
FROM ${TCIoT_REGISTRY}/base_python3:1.0.0

WORKDIR /home/tcadm/

COPY system/ ./system
COPY source/schemas/ ./schemas
COPY source/tclib/ ./tclib
COPY source/traffic_detector/ .

CMD ["python3", "traffic_detector.py"]
