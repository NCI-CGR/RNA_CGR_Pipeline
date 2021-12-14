#/bin/bash

# subshells do not inherit bash functions, so conda must be initialized again
source /DCEG/Resources/Tools/miniconda/miniconda3/etc/profile.d/conda.sh
source activate /DCEG/Resources/Tools/miniconda/miniconda3/envs/rnaseq_qc

dir=$(pwd)
mkdir -p $dir/logs

# create running flag here
touch RNA.QC.Running

snakemake \
    --cluster "qsub -pe by_node {threads} \
    -V -j y \
    -S /bin/bash \
    -cwd \
    -o ${dir}/logs" \
    --jobs 500 --latency-wait 120 \
    --keep-going \
    --rerun-incomplete \
    --restart-times 5 \
