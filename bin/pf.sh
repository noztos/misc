#!/bin/sh
# usage : ssh-agent pf.sh
PFSH=remoteHostUsr
PFHOST=remoteHost
PFRPORT=remoteHostPort
PFSSHKEY=sshIdentKey
SSH_PATH=/usr/bin
BIN=/bin

${SSH_PATH}/ssh-add SSH_KEY
trap "echo trapped\(INT\) at; date" INT
trap "echo trapped\(TSTP\) at; date" TSTP

sleep 60
while :
do
  #${SSH_PATH}/ssh -R ${PFRPORT}:localhost:22 -N ${PFSH}@${PFHOST}
  ${SSH_PATH}/ssh -R ${PFRPORT}:localhost:22 -o "ServerAliveInterval 100" -N ${PFSH}@${PFHOST}
  echo disconnected at; ${BIN}/date
  ${BIN}/sleep 30
done
