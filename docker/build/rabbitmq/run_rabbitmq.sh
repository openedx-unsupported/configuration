#!/bin/bash

ulimit -n 1024
exec rabbitmq-server $@