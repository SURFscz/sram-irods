FROM python:3

RUN apt-get update
RUN apt-get install -y libxmlsec1-dev

RUN pip3 install zope twisted python3-saml

EXPOSE 80

WORKDIR /app
