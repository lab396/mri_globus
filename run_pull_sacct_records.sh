#!/bin/bash

echo "Job starting on `hostname` at `date`"
echo " "
 
module load python/3.11.2

cd /storage/group/pches/default/users/nucci/PCHES_ACCOUNTING
/usr/bin/time -v $PWD/pull_sacct_records.py

echo "Job ending on `hostname` at `date`"
