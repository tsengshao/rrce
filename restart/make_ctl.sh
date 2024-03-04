#!/bin/bash

expList="RRCE_3km_f00 RRCE_3km_f10 RRCE_3km_f15 RCE_300K_3km_f0 RCE_300K_3km_f05"
expList="RRCE_3km_f20"
for exp in ${expList};do

  rundir="/data/C.shaoyu/rrce/vvm/${exp}"
  ncdir="${rundir}/archive"
  outdir="${rundir}/gs_ctl_files"
  echo ${outdir}
  mkdir -p ${outdir}
  
  declare -A vtab
  vtab[time]='t'
  vtab[lon]='x'
  vtab[lat]='y'
  vtab[lev]='z'
  
  # ----- number of data type and ncheader
  dtype_list=""
  for dum in $(ls ${ncdir}/*000000.nc);do
    dum=$(echo ${dum}|rev|cut -d"/" -f1|rev|cut -d"-" -f1)
    dum0=$(echo ${dum}|rev|cut -d"." -f2|rev)  #L
    dum1=$(echo ${dum}|rev|cut -d"." -f1|rev)  #Thermodynamic
    ncheader=$(echo ${dum}|rev|cut -d"." -f3|rev)  #RRCE_3km_f00
    dtype_list="${dtype_list} ${dum0}.${dum1}"
  done
  
  # ----- dimension
  nt=$(ls ${ncdir}/*.${dum0}.${dum1}-*.nc|wc -l)
  nx=$(grep "zonal_dimension" ${rundir}/vvm.setup|cut -d"'" -f2|cut -d"/" -f3)
  ny=$(grep "merid_dimension" ${rundir}/vvm.setup|cut -d"'" -f2|cut -d"/" -f3)
  nz=$(grep "vert_dimension" ${rundir}/vvm.setup|cut -d"'" -f2|cut -d"/" -f3)

  # get lon/lat
  lat0=$(grep "RLAT=" ${rundir}/vvm.setup|cut -d',' -f1|cut -d'=' -f2)
  lon0=$(grep "RLON=" ${rundir}/vvm.setup|cut -d',' -f2|cut -d'=' -f2|cut -d' ' -f1)
  lat0=0
  lon0=0
  dx=$(grep "DX=" ${rundir}/vvm.setup|cut -d',' -f1|cut -d'=' -f2)
  dy=$(grep "DY" ${rundir}/vvm.setup|cut -d',' -f2|cut -d'=' -f2)
  dlon=$(echo "scale=6;${dx}/111000"|bc)
  dlat=$(echo "scale=6;${dx}/111000"|bc)
  
  # get dt
  outfreq=$(grep "NXSAVG=" ${rundir}/vvm.setup |cut -d"," -f2|cut -d"=" -f2)
  dt=$(grep "DT=" ${rundir}/vvm.setup |cut -d"," -f5|cut -d"=" -f2)
  deltatime=$(echo "scale=0;${outfreq}*${dt}/60"|bc)
  echo ${deltatime} min
  
  # ----- get z level
  dum=$(grep -n "ZT(K)" ${rundir}/fort.98|cut -d":" -f1)
  dum=$(echo ${dum}+${nz}+1|bc)
  table=$(cat ${rundir}/fort.98 |head -n ${dum}|tail -n ${nz})
  zlist=""
  for i in $(seq ${nz});do
    idx=$(echo "3+(${i}-1)*5"|bc)
    dum=$(echo ${table}|cut -d" " -f${idx})
    dum=$(echo "scale=3;(${dum}/1000.)"|bc)
    zlist="${zlist} ${dum}"
  done
  
  for dtype in ${dtype_list};do
    type0=$(echo ${dtype}|cut -d. -f1)
    type1=$(echo ${dtype}|cut -d. -f2)
  
    if [ ${type0} == "L" ];then
      outz=${zlist}
      outnz=${nz}
      outnz1=${nz}
    else
      outz=1000
      outnz=0
      outnz1=1
    fi
  
    # ------ get varables
    table=$(ncdump -h ${ncdir}/${ncheader}.${dtype}-000000.nc|grep "float")
    table=${table// /.}
    table2=$(ncdump -h ${ncdir}/${ncheader}.${dtype}-000000.nc|grep "standard_name")
    table2=${table2// /.}
    varstring=""
    nvar=0
    for dum in ${table};do
      vname=$(echo ${dum}|cut -d. -f2|cut -d"(" -f1)
      if [ "${vname}" == "time" ]; then continue; fi
      
      longname="xxx"
      for dum2 in ${table2};do
        vlname=$(echo ${dum2}|cut -d':' -f1)
        if [ "${vlname}" == "${vname}" ]; then
          longname=$(echo ${dum2}|cut -d'"' -f2)
          break
        fi
      done
      #echo ${vname} ${longname}
  
      nvar=$((${nvar}+1))
      dim=$(echo ${dum}|cut -d"(" -f2|cut -d")" -f1)
      dimstr=""
      for v in ${dim//,./ };do
        dimstr="${dimstr},${vtab[$v]}"
      done
      dimstr=$(echo ${dimstr}|cut -c2-10000)
      varstring="${varstring}\n${vname}=>${vname} ${outnz} ${dimstr} ${longname}"
    done
    echo ${dtype} ${nvar}
    
    string="
    DSET ^../archive/${ncheader}.${dtype}-%tm6.nc\n
    DTYPE netcdf\n
    OPTIONS template\n
    TITLE ${dtype} variables\n
    UNDEF 99999.\n
    CACHESIZE 10000000\n
    XDEF ${nx} LINEAR ${lon0} ${dlon}\n
    YDEF ${ny} LINEAR ${lat0} ${dlat}\n
    ZDEF ${outnz1} LEVELS ${outz}\n
    TDEF ${nt} LINEAR 01JAN1998 ${deltatime}mn\n
    VARS ${nvar}
    ${varstring}\n
    ENDVARS
    "
    echo -e ${string}>${outdir}/${type1}.ctl
  
  done


done ## expList
