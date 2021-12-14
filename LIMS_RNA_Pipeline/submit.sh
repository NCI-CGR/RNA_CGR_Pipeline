#!/bin/bash

. /etc/profile.d/modules.sh; module load miniconda/3
unset module

mkdir -p logs

qsub -V -cwd -S /bin/bash -j y -o logs wrapper.sh

