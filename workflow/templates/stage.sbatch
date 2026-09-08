#!/usr/bin/env bash
# Generated from workflow/templates/stage.sbatch. Edit the template or
# workflow/stages.py, then render a new run; do not edit this locked copy.
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --account=MST114418
#SBATCH --cpus-per-task=1
#SBATCH --ntasks={tasks}
#SBATCH --output={log_path}

set -eo pipefail
source ~/.bashrc
conda activate py311
set -u
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH={sources_root}
python -m workflow.runner --run-dir {run_dir} --stage {stage_id}
