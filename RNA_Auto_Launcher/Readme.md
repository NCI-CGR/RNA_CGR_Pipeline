## RNA Auto Launcher
### Description
RNA Auto Launcher program (run by crontab) can auto-trigger [RNA QC pipeline](git@10.133.130.114:lxwgcool/LIMS_RNA_Pipeline.git).

 - Frequency: hourly
 - Target: RNA flowcell
 - Input
    - Flowcell data folder
 - Output
    - RNA QC pipeline analysis result
    - Working List
    - Done List

### Highlight
 - The flowcell should be processed by peimary pipeline
 - Only handle RNA flowcell
 - Maintain two file list, including working/done file list
 - Send 6 types of email notifications to handle different states of analysis, including starting, ending and hanging.

### Details
 - The mechanism of automation
    - Auto scan the whole processed flowcell (primary pipeline)
    - Auto collect RNA flowcell
    - Auto check if the primary analysis of RNA flowcell has already been finished
    - Auto check if RNA QC pipeline is new/processing/procesed
    - Auto grab the RNA QC pipeline code from github
    - Auto launch RNA QC pipeline for new finished(primary pipeline) RNA flowcell
    -  Auto email notification when analysis start/end/error/zombie
 - Six types of email notification
    - New flowcell been launched
    - Flowcell do not contain standard dir (e.g. missing dir "logs")
    - Flowcell is all set
    - Flowcell log file contains error (e.g. Exiting because a job execution failed)
    - Flowcell contains long time no update log (zombie jobs)
    - Flowcell contains abnormal flags (e.g. no running flag, or contains both done and running flag)
 - Dependences
    - python3
 - Key threshold
    - Zombie log: 12 hours
    - Crontab frequency: hourly
    - RNA flowcell definition: capture kit contains the keyword "RNA"
    - Support sequencing platform: HiSeq, MiSeq and NextSeq
 - Key Directory: 
    - Working/Done File list: /DCEG/Projects/Exome/SequencingData/DAATeam/Log/RNAPipeline
    - Real dataset for testing: /scratch/lix33/CGR/Pipeline/Primary_Pipeline/Data/Illumina/HiSeq/PostRun_Analysis/Data
    - Testing Script: /scratch/lix33/CGR/Pipeline/Primary_Pipeline/JobScript/test/RNA_Auto_Launcher
 - Key Gitlab Repo:
    - RNA QC Pipeline: http://10.133.130.114/lxwgcool/LIMS_RNA_Pipeline

    
### Example (How to run the program)
  - python3 ${AutoLuncher} $

### Deploy "RNA_Auto_Launcher" in HPC cluster 
Please check the issue #1