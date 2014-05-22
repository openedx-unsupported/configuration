#!/usr/bin/env bash

function ascii_convert {
  echo $1 | iconv -f utf8 -t ascii//TRANSLIT//IGNORE
}

# remove non-ascii chars from build user vars
BUILD_USER_LAST_NAME=$(ascii_convert $BUILD_USER_LAST_NAME)
BUILD_USER_FIRST_NAME=$(ascii_convert $BUILD_USER_FIRST_NAME)
BUILD_USER_ID=$(ascii_convert $BUILD_USER_ID)
BUILD_USER=$(ascii_convert $BUILD_USER)
