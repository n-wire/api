# syntax=docker/dockerfile:1
FROM node as builder

ARG API_SERVER = localhost
RUN apt update
RUN apt install -y git
WORKDIR /app1
RUN git clone https://github.com/n-wire/dashboard.git
WORKDIR /app1/dashboard
ENV REACT_APP_API_SERVER=${API_SERVER}
ENV REACT_APP_API_SERVER_PORT=5001
RUN npm install
RUN npm run build

FROM python:3.8-slim-buster
WORKDIR /app
RUN pip3 install sanic sanic_cors pymongo pyjwt motor nodewire==2.0.0
COPY . .
COPY --from=builder /app1/dashboard/build/ ./frontend/
CMD [ "python3", "app.py"]
