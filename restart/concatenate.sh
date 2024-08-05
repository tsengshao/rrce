#!/bin/bash

vvmPath="/data/mog/VVM/DATA/"
#/data/mog/VVM/DATA/RRCE_3km_f10_1

outVvmPath="/data/C.shaoyu/rrce/vvm/"

typeList="C.Surface L.Diag L.Dynamic L.Radiation L.Thermodynamic"
#expList="RRCE_3km_f00 RRCE_3km_f05 RRCE_3km_f10 RRCE_3km_f15 RCE_300K_3km_f0 RCE_300K_3km_f05"
expList="RRCE_3km_f00_20"
expList="RRCE_3km_f00_26 RRCE_3km_f00_27 RRCE_3km_f00_28 RRCE_3km_f00_29"
expList="RRCE_3km_f00 RRCE_3km_f10"


for exp in ${expList};do
  echo "----- ${exp} -----"

  dir="${vvmPath}/${exp}/"
  if [ ! -d ${dir} ];then
    echo "can't found the case '${exp}' ... skip"
    continue
  fi
  out="${outVvmPath}/${exp}/"
  rm -rf ${out}

  mkdir -p ${out}
  ln -sf ${dir}/TOPO.nc      ${out}/
  ln -sf ${dir}/fort.98      ${out}/
  ln -sf ${dir}/vvm.setup    ${out}/
  ln -sf ${dir}/INPUT        ${out}/

  n=$(ls -d ${vvmPath}/${exp}_*|wc -l)
  if [ ${n} -le 0 ]; then
    ln -sf ${dir}/archive     ${out}/
    echo "no restart folder ..."
    continue
  fi

  echo "There are ${n} folder to be merged ..."
  mkdir ${out}/archive
  ln -sf ${dir}/archive/*.nc ${out}/archive/
  for i in $(seq 1 ${n}) ;do
    echo "process the restart_${i} ..."
    dir="${vvmPath}/${exp}_${i}/"
    if [ ! -d ${dir} ];then
      echo "can't found the restart folder: ${dir} ..."
      echo "please check the rule of the restart folder ... skip"
      break
    fi

    if [ ${i} -eq 1 ]; then
      pre_exp=${exp}
    else
      i0=$(echo ${i}-1|bc)
      pre_exp=${exp}_${i0}
    fi

    idx0="notfound"
    if [ -f ${dir}/restart.log ];then
      cp -r "${dir}/restart.log" ${out}/restart_${i}.log
      idx0=$(head -n 1 ${dir}/restart.log|rev|cut -d" " -f1|rev)
    else
      idx0=$(grep "${pre_exp}.L.Thermodynamic" \
            ${vvmPath}/${exp}_${i}/CODE/ini_3d_module.F|\
            rev|cut -d"-" -f1|rev|cut -c1-6)
      echo "restart timestep ... ${idx0} 
            from ${vvmPath}/${exp}_${i}/CODE/ini_3d_module.F" > ${out}/restart_${i}.log
    fi

    if [ "${idx0}" == "notfound" ]; then
      echo "can't found the restart timestep ... skip"
      break
    fi
   
    if [ ${i} -eq 1 ]; then
      lastnum=${idx0}
    else
      dum=$(ls ${vvmPath}/${pre_exp}/archive/${pre_exp}.C.Surface*.nc|wc -l)
      lastnum=$(echo "${lastnum}-(${dum}-1-${idx0})"|bc)
    fi
 
    nfile=$(ls ${dir}/archive/${exp}_${i}.C.Surface*.nc|wc -l)
    nfile=$(echo ${nfile}-1|bc)
    echo "restart init_timestep is ${idx0} and the total number is ${nfile}"
    for inc in $(seq 1 ${nfile});do
      inc=$(printf "%06d" ${inc})
      idx=$(echo ${lastnum}+${inc}|bc)
      idx=$(printf "%06d" ${idx})
      #echo "${inc}-->${idx}"
      for vtype in ${typeList};do
        #echo ${dir}/archive/${exp}_${i}.${vtype}-${inc}.nc
        ln -sf ${dir}/archive/${exp}_${i}.${vtype}-${inc}.nc \
               ${out}/archive/${exp}.${vtype}-${idx}.nc
      done
    done # inc
    lastnum=${lastnum}+${nfile}

  done # restart folder (i)

done #exp
