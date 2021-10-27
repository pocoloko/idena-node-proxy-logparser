#!/bin/bash
# prepares the idena-node-proxy logfile for further processing by script
# should be executed in same folder as access.log
# usage: ./logparserinit.sh DATE EPOCH
# for example: ./logparserinit.sh 2021-10-11 75

if [[ $# -eq 0 ]] ; then
    echo 'ERROR: You have not supplied the required arguments'
    echo 'USAGE: ./logparserinit.sh DATE EPOCH'
    exit 1
fi

if [[ $# -eq 1 ]] ; then
    echo 'ERROR: You are missing an argument'
    echo 'USAGE: ./logparserinit.sh DATE EPOCH'
    exit 1
fi

cat access.log | grep $1 > validation.epoch.$2.log
cat validation.epoch.$2.log | grep dna_identity > dna_identity.epoch.$2.log
awk '!a[$3]++' dna_identity.epoch.$2.log > dna_identity.epoch.$2.unique.log
echo "Extracted unique dna_identity entries from log file for supplied epoch $2 with date $1, proceeding to process..."
python3 ./logparser.py dna_identity.epoch.$2.unique.log $2
