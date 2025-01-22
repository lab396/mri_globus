#!/bin/bash

#SBATCH --job-name=move_2_arch_UP      # Job name
#SBATCH --output=move_2_arch_UP_%j.out # Std output and error
#SBATCH --nodes=1                      # Run all processes on a single node
#SBATCH --ntasks=1                     # Run a single task
#SBATCH --cpus-per-task=1              # Number of cpus to use per task
#SBATCH --time=48:00:00                # Job time limit
#SBATCH --mem=8gb                      # Job memory required
#SBATCH --partition=open               # Use open allocation
#SBATCH --mail-type=ALL,TIME_LIMIT_80  # Send e-mail start/end/err/80 pct
#SBATCH --mail-user=nucci@psu.edu      # e-mail to use

echo "Job starting on `hostname` at `date`"
echo " "

cd /storage/work/$USER/prod
#cd /storage/work/$USER/dev

echo "Working directory set to $PWD"
echo " "

module load anaconda/2021.11
echo "The following modules are in use"
echo " "
module list

today=$(date --utc +"%Y%m%d")

# Set working directories

export TMPDIR=/tmp
#export WORKDIR=/storage/work/other_d666f751616c41/prod
export WORKDIR=/storage/work/other_d666f751616c41/dev

# Call the script. Hope for the best

$WORKDIR/archive_CQI_files_as_zip.sh --data_location=University_Park --data_age=60
local_rc=$?

echo " "
echo "Archive script exited with rc $local_rc"
echo ""

/bin/Mail -s "Job log for CQI UP archive for $today"  l-cqi-data-administrators@lists.psu.edu < $HOME/CQI-arch-UP-$SLURM_JOBID.out
local_rc=$?
echo "Mail command returned with code $local_rc"

cp $HOME/CQI-arch-UP-$SLURM_JOBID.out /storage/group/oom5021/default/JOBLOGS/CQI-arch-UP-$SLURM_JOBID.$today.out

sleep 30 # Need to give the mail command time to process

echo "Job ending on `hostname` at `date`"
