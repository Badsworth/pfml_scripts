#
# Dockerfile for PFML API.
#

FROM python:3.8-slim

COPY container/etc/* /etc/
RUN mkdir /container && chown container /container
USER container
WORKDIR /container/

COPY --chown=container requirements.txt ./
RUN pip3 install --no-cache-dir --requirement=requirements.txt

COPY --chown=container . .
RUN python3 api.py --test-only

CMD [ "python3", "api.py" ]
