# Copied from https://github.com/BretFisher/node-docker-good-defaults/blob/master/Dockerfile

FROM node:10

# Create app directory
RUN mkdir -p /edx/app/gradebook

ARG NODE_ENV=production
ENV NODE_ENV $NODE_ENV

ARG PORT=80
ENV PORT $PORT
EXPOSE $PORT 1994

ENV PATH /edx/app/gradebook/node_modules/.bin:$PATH

RUN npm i npm@latest -g

WORKDIR /edx/app/gradebook
COPY . /edx/app/gradebook

ENTRYPOINT npm install && npm run start
