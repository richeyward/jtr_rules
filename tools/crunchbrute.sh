#!/bin/bash

mkdir -p cracked

if [[ $# -lt 3 ]] ; then
    echo 'Arguments not passed <start_char_count> <finish_char_count> <format>'
    exit 0
fi

if [ $3 == "LM" ]; then
  crunch $1 $2 -f /usr/share/crunch/charset.lst ualpha-numeric-all | ./john --stdin defcon_contest_hashes.txt --format=LM --pot=cracked/LM.pot
else
  crunch $1 $2 -f /usr/share/crunch/charset.lst mixalpha-numeric-all-space | ./john --stdin defcon_contest_hashes.txt --format=$3 --pot=cracked/$3.pot
fi
