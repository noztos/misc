#!/bin/sh
base=`pwd | sed "s;.*/\(where/to/path/*\);\1;"`
echo "--- svn update $base --- sleeping 10sec"
sleep 10

for dname in `svn ls http://confsrv/svn/$base`
do
  echo
  echo
  
  while true
  do
    echo "=== $dname (re)start ==="
    svn update $dname
    if [ $? -eq 0 ]; then
      break
    fi
    echo "svn cleanup"
    svn cleanup $dname
  done
  echo
  echo
done
