FROM ubuntu:latest

MAINTAINER Graham Williams "Graham.Williams@microsoft.com"

RUN apt-get update && apt-get install --yes wajig
RUN wajig install --yes xterm
RUN wajig install --yes python3-pip python3-requests python3-yaml
RUN wajig install --yes r-recommended
RUN pip3 install mlhub

CMD ["bash"]
