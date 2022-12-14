FROM python:3.10

RUN mkdir /inventory_backend
WORKDIR /inventory_backend
COPY . /inventory_backend/
RUN pip install -r requirements.txt
