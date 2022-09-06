#!/bin/bash

echo 'Running its time bot'

blacklisted () {
  case $1 in
    PWD|OLDPWD|SHELL|STORAGE|-*) return 0 ;;
    *) return 1 ;;
  esac
}

eval '
  export() {
    blacklisted "${1%%=*}" || unset -v "${1%%=*}"
  }
  '"$(export -p)"
export() {
  blacklisted "${1%%=*}" || command export "$@"
}
. /enironment
unset -f export

cd /its-time-bot
python3 -u main.py