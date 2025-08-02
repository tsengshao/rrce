#!/usr/bin/env bash
#SBATCH -J shift
#SBATCH -p all
#SBATCH -N 1
#SBATCH --cpus-per-task=10   # 1 task 要 10 顆 CPU
#SBATCH -w mogamd
#SBATCH -o out.%j.out

source ~/.bashrc
conda activate py311
set -euo pipefail
export OMP_NUM_THREADS=1

exp='RRCE_3km_f00'
path="/data/C.shaoyu/rrce/data/shift/${exp}"
outpath="$path/../new_${exp}"
mkdir -p "$outpath"

files=("$path"/*.Thermodynamic*.nc)  # 用陣列
max_jobs=${SLURM_CPUS_PER_TASK:-10}
declare -a pids=()

for f in "${files[@]}"; do
    ts=$(basename "$f" | cut -d'-' -f2 | cut -d'.' -f1)
    ncfiles=("$path"/*"$ts"*.nc)

    # 背景合併
    rm -rf $outpath/new-${ts}.nc
    cdo -f nc4 -z zip_4 merge "${ncfiles[@]}" "$outpath/new-${ts}.nc" &
    pids+=("$!")

    # 若已開滿 10 條，就等任意一條結束
    while (( ${#pids[@]} >= max_jobs )); do
        wait -n           # Bash 4.3+；舊版請告訴我
        # 清掉已完成的 PID
        for i in "${!pids[@]}"; do
            kill -0 "${pids[i]}" 2>/dev/null || unset 'pids[i]'
        done
    done
done

# 收尾
for pid in "${pids[@]}"; do
    wait "$pid"
done
echo "Done."
