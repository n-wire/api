# syntax=docker/dockerfile:1

ARG APISERVER
FROM node as builder

RUN apt update
RUN apt install -y git
WORKDIR /app1
RUN git clone https://github.com/n-wire/dashboard.git
WORKDIR /app1/dashboard
ENV REACT_APP_API_SERVER=${APISERVER:-localhost}
ENV REACT_APP_API_SERVER_PORT=5001
RUN npm install
RUN npm run build

FROM python:3.9-slim-buster
WORKDIR /app
RUN pip3 install sanic sanic_cors pymongo pyjwt motor aiofiles nodewire==2.0.0
COPY . .
COPY --from=builder /app1/dashboard/build/ ./frontend/
CMD [ "python3", "app.py"]
