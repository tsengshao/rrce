# 可行性審查與 agent 實作方案

本文件是後續實作的主要交接規格。若與早期 ARCHITECTURE.md 或 manifest.example.yaml 的草案不同，以本文件及使用者最新決定為準。本次只做靜態 code review 與方案，不實作或提交 jobs。

## 1. 結論與證據範圍

可行，需要「工作流控制 + 有限參數化/副本修正」，不能只改 case loop。
已檢查相關 shell/Python/GrADS 原碼以及 wp、convolve、horimsf CTL 來源。尚未實際執行 MPI、GrADS、Slurm，也未對所有科學資料逐檔驗證；本結論不代表現場端到端已通過。

已確認需求：
- 一個 stage 一個 sbatch job，job 包含明確選取的 cases；一次 workflow submit 建立所有 stage jobs。
- 所有科學運算及繪圖以 Slurm 提交；afterok 表達父 stage 成功後才執行。
- dry-run 不提交、不計算、不建立或修改產物、symlink 或 run state。
- 保留既有資料位置；workflow/runs/<run_id>/artifacts/ 集中放資料/CTL/圖片 symlinks。
- 原始分析程式與 scripts 保留；採新入口及 run 中的可 review 副本。
- 沒有額外 --allow-overwrite 不覆蓋。本旗標只能覆蓋本次 plan 中的精確產物。
- config_<name>.py 可推導組名；config.py 必須明確提供組名。本次 f10_HomogRad。
- 整數 restart day 實心圓，小數日 ensemble 空心圓。一組實驗各一張 DRY、一張 DXX。
- 舊 origin NetCDF 對應 f10_origin，舊無後綴 NetCDF 對應 f20；不改名或搬移舊檔。

## 2. 必須先解決的缺口

| 問題 | 原碼證據 | 實作處理 |
|---|---|---|
| 選擇 config | 各程式 import config 並插入 ../ | snapshot config、注入 sys.modules，受控 sys.path；每個 MPI rank 用同一 snapshot |
| HomogRad 日數 | axisy_meta.parse_restart_day 讀最後 token | cluster 解析唯一 d<number> token，RRCE 舊規則另分支；未知格式要求 mapping |
| 時間硬編 | center/cloud/axisy 常將 totalT 改成 217/2521、dt=20 | 在副本改為 config 時間資料；非支援時間窗 fail closed |
| 缺 CTL stage | wp.py、cal_sf_fft.py、cal_convolve.py 不產生所需 GrADS CTL | 新增 wp_ctl、sf_ctl、convolve_ctl |
| 已有 CTL 來源 | data/wp/generate_ctl.sh、data/horimsf/generate_ctl.sh、data/convolve/convolve.ctl | 參考格式，只為選取實驗產生，不掃整個資料目錄 |
| MPI 資源矛盾 | run2.sh 45 tasks，但 mpirun 72/217 | postprocess 改用 ct448、217 tasks，逐步執行 |
| center 並行 | 每 rank 全時段且共寫一個 txt | 每 case 單程序；第一版 case 依序執行 |
| cloud 內部並行 | 7 MPI ranks、CloudRetriever cores=15 | 先保留既有 ranks/內部 cores；不能變 112 MPI ranks |
| import 衝突 | cloud import util_axisymmetric，而模組位於 axisy/；多個 util_draw | 明確 search path 順序，每次 invocation 新 Python process |
| 背景失敗遺失 | shell 裸 wait 不表示每個程序成功 | 逐 PID wait，累計非零；MPI 命令失敗立刻退出 |
| 部分成功 | cal_axisy_exp_daily 缺 case 會 skip 仍寫 NC | producer exit 前驗證 exp 集合與 expected 完全相等 |
| 重算破壞既有資料 | cal_axisy/cal_process 直接 rm，中心 txt 以 w 開啟 | workflow 副本移除刪除，guard 精確輸出；不得 rm case 目錄 |
| CTL grid 假設 | CTL 寫死 384 grid、38 levels、20mn | 校驗尺寸/levels/dt；先支援現有 grid，未知 grid 拒絕而非猜經緯轉換 |
| 日平均不同 | axisy_daily 用 0..71；lowlevel day1 用 1..72 | 保留兩種定義，各自 metadata/測試，不合併演算法 |
| 共寫 CTL | reduce/daily 呼叫相同 CTL writer | 第一版 combined postprocess 依序跑，避免競寫 |
| 缺來源追溯 | 既有資料沒有 workflow receipt | 明列 legacy reuse，檢查完整性但不宣稱科學版本相同 |

使用者已授權參考 run.sh 和調整 Slurm。資源修正是工程修正，不另要求選擇；walltime 不自行填數字，報告會註明沿用叢集政策。任意新 config 不等於任意 grid/任意 dt 科學模型皆支援。

## 3. 明確的 stage DAG

以下每一列是一個 stage job，覆蓋全部 run cases。reuse cases 不重新計算。完全 reuse 的 stage 不需 sbatch。

| Stage | 直接父節點 | 命令/用途 |
|---|---|---|
| cwv | 無 | wp.py |
| convolve | 無 | cal_convolve.py CASE 150 |
| horisf | 無 | cal_sf_fft.py |
| center_0 | 無 | find_center_domain_mean.py CASE 0km |
| center_150 | convolve | find_center_domain_mean.py CASE 150km |
| center_sf | horisf | find_center_domain_mean_sf.py CASE，不傳假 0km |
| cloud | 無 | find_cloud.py |
| wp_ctl | cwv | 指定 case 的 WP CTL |
| convolve_ctl | convolve | EDEF 1 NAMES 150km |
| sf_ctl | horisf | sf=>msf、指定 case CTL |
| water | wp_ctl, center_0, center_150, center_sf | draw_water.gs 全時間 |
| wind | wp_ctl, center_0, center_150, center_sf | draw_wind.gs 全時間 |
| center_zeta | center_0, center_150, center_sf, convolve_ctl, sf_ctl | draw_zeta.gs 全時間 |
| center_conzeta | 同上 | draw_conzeta.gs 全時間 |
| axisy_convert | cwv, center_0 | cal_axisy.py |
| axisy_postprocess | axisy_convert | reduce -> process -> daily，三程式依序 |
| hov_radial | axisy_postprocess | radial variant |
| hov_tangential | axisy_postprocess | tangential variant |
| tang_daily | axisy_postprocess | draw_tang_wind_one_daily.py |
| radi_daily | axisy_postprocess | draw_radi_wind_one_daily.py |
| mse_ccc_daily | axisy_postprocess, cloud, center_0 | 還直接讀 axmean-000010.nc |
| lowlevel_exp | axisy_postprocess, cwv | 彙整選定 exp 的 NetCDF |
| lowlevel_profiles | lowlevel_exp | 此實驗組 profiles，CTRL 圖另選產品 |
| scatter_dry | lowlevel_exp, external CTRL profile | 單組 DRY |
| scatter_dxx | lowlevel_exp, external CTRL profile | 單組 DXX |

CTRL profile 是明確外部輸入。先不把重算整個 CTRL 的原始資料鏈偷偷加入本次；缺檔僅阻擋 scatter/要求使用者指定來源，其餘 plan 可生成。全部 products submit 前必須補齊必要輸入。

## 4. 目錄與介面：保持小而可維護

建議 Python standard library 控制流程，JSON 作 canonical plan/state。人工 manifest 可用 TOML（Python 3.11 tomllib）；現有 YAML 僅草案，實作時提供對等 TOML 並明確記錄轉換，不隱藏新增 PyYAML 依賴。

workflow/
  cli.py                 plan/render/submit/status
  config_loader.py       config snapshot 與 dataset_tag/case 解析
  stages.py              declarative stage definitions/resources/dependencies
  contracts.py           enumerate inputs/outputs + validators
  render.py              snapshots、patch application、templates、links
  submit.py              Slurm calls/state/reconciliation
  runner.py              guarded runtime entry/config injection/post-check
  ctl.py                 scoped CTL writer
  adapters/              有限 Python/GrADS 改寫與 lowlevel callable wrappers
  patches/               人工可讀 unified diff；不靠廣泛 regex 修改科學程式
  templates/             serial.sbatch、mpi.sbatch、grads.sbatch
  examples/              人工 manifest、f10_origin/f20 的來源對應
  tests/                 fake Slurm + synthetic file fixtures
  runs/<run_id>/          plan.json、review.md、sources/、jobs/、logs/、state/、artifacts/

stage specification 欄位：
id, parents, resource_profile, entrypoint, case_mode(per_case_loop/set_aggregate),
input_contract, output_contract, snapshot_dependencies。
Stage records 全部寫在 stages.py，不能把 DAG 分散於 CLI 或 shell templates。

資源的起始配置（來自現有腳本/本次要求，render 全部展開）：
cwv ct112/72 ranks；convolve ct448/217 ranks；horisf ct112/72 ranks；
center ct112/單程序（可申請原 6 tasks，但依序執行不需 6 ranks）；
cloud ct112/7 MPI ranks、112 allocation tasks、內部 15 workers；
axisy_convert ct448/224 allocation tasks、217 ranks；
postprocess ct448/217 tasks，reduce 72、process 217、daily 3 ranks；
GrADS ct112,cf112/112 個單核心 slots；
無既有 SBATCH 的 serial Python/CTL 使用 ct112,cf112/1 task。
mamba activate py311；account MST114418；OpenGrADS 使用使用者給定絕對路徑。

## 5. 分階段實作任務與完成定義

### P1：純 planner 與 config 契約

新增 cli.py/config_loader.py/stages.py。載入 config 時不匯入科學計算 scripts。
驗證 expList/totalT 長度、索引零起算/非空/不重複、exp label、dt 有效。
保持原 config index，不把選取清單重新編號。名稱不能含路徑分隔符。
dataset_tag 明確值優先；沒有明確值才依 config_<name>.py 推导，config.py 不推測。
相同 exp 名稱跨兩份 config 若指向相同 dataPath，必須視為同一物理產物衝突，不能靠組名區別假裝隔離。

新增 plan --config PATH --cases N N --dataset-tag TAG --dry-run；
加入 --manifest PATH 支援人工維護 resources/product/day/input 設定。
CLI 與 manifest 同欄位若衝突報错。
run_id 只有 render 才必填；dry-run 不要求使用者填假的 run_id。
dry-run 只輸出計畫與未解決項，不寫任何 state、pyc 或 link。

完成：不同 config/非連續 cases/命名/未知資料格式測試，所有錯誤指向明確欄位。
注意任意 Python config 本身可能有副作用；宣告只接受無副作用設定模組，
不能宣稱在任意惡意 config 下 dry-run 也絕對無寫入。

### P2：輸出 inventory、重用與覆蓋

新增 contracts.py。按 stage/case 枚舉精確檔案；不要以整個 axisy/<exp> 目錄作輸出單位。
manifest 支援每 stage 的 case_actions，run/reuse 都由人可見；不自動重算舊實驗。
既有完整輸出可明確 reuse，部分輸出要列 collision，不默默 skip。
render 可產生帶 collision 報告；普通 submit 拒絕 collision；
submit --allow-overwrite 僅允許 plan 內已列且重新驗證相符的目標。
禁止覆蓋未在 cases 的實驗、源檔、config、共享 root。

runtime 每 stage/exp 加 exclusive lock，stage 結束釋放；鎖取得後再次檢查。
一次 overwrite 重跑產生新 receipt；下游 reuse 若 provenance 不符必須報錯。
首次 legacy reuse 只聲明格式/資料完整性通過，附 provenance_unknown。

完成：共享 case 目錄中不同 stages 不誤判衝突；雙提交/鎖競態；
新檔在 render 後出現不被 flag 無限授權；overwrite 不刪掉其他 stage。

### P3：render + snapshot + runtime adapter

新增 render.py/runner.py/templates。snapshot 所需 Python 與 local helper module，
不包括 data/figures；用 whitelist 清單，保留原相對目錄結構。
config.snapshot.py 與 sources 均 hash。job 用 snapshot，不能在排隊期間讀變動的 repo。
sys.path 明確排定 target module dir -> snapshot root ->必要 axisy helper dir；
每次 invocation 獨立程序，防止 util_draw/config module cache 混淆。

對 source 副本套用版本化 unified patches；context 不符停止，產生 patch diff 供 review。
source unchanged 的科學 kernels 對照 hash；不以全域 regex 改 nt/dtime。
對圖片輸出改為明確絕對路徑，不能靠切 cwd 意外寫入 sources。
run dir exclusive create；manifest.lock/plan.json/review.md/jobs 全部記錄 hashes。
artifacts 建 symlink 指向實際輸出；同 run link 同名但異目標時報錯。
手動改 job 或來源後須重新 render 新 run，submit 不接受 hash 不符。

完成：render 出可 bash -n 的 scripts；路徑含空白正確 shell quoting；
所有 MPI ranks 讀同一 snapshot；產物 paths 不指回 source 目錄。

### P4：計算、GrADS 與 CTL 適配

逐項來源修改表：
- center/cloud/axisy scripts：以 snapshot config 的 totalT/dt 取代硬編；
  daily producer 保留原時間窗，未知/不足完整天先拒絕。
- axisy/cal_axisy.py、cal_process_axisymmetricity.py：移除 rm，寫入 guard 管理的精確檔案。
- center scripts：單 rank，參數 kernel 明確；檢查 txt rows=expected。
- wp/horisf/convolve CTL：借用三個現有 templates/generators，檢查逐 index，
  不用 nc 檔案數當時間連續性證明。WP 需 cwv/iwp/lwp。
- 四個 GrADS 副本：替換整個實驗清單區塊為完整 exp/label/dt/totalT；
  保留檔案 open 次序，因為程式使用 .1/.2/.3。
- convolve 的 ensemble name 150km 與 zeta.3(ens=...) 保持一致。
- GrADS Python scheduler/批次 wrapper 最多112子程序，逐 PID 退出+圖片檢查。

run2 combined 執行每個程式所有 cases，前一步全成功才進下一步。
完成：小型 CTL fixture 檢查 DSET/TDEF/EDEF/variable mapping；
短 case 缺 index 報錯；背景程序中間失敗導致 stage 非零。
GrADS helpers/color/xcbar 等是否安裝需 runtime preflight，不只檢查 executable。

### P5：axisy/lowlevel 繪圖

新增顯式 component 入口，Hov radial/tangential 各產物命名。
保留現有色階/科學數值；series 圖現在使用 min(var)：
tangential 要保留 min 還是改 max 不能默改，先標記科學語意待決定。
每日 tang/radi/MSE 圖使用 validated day indices；MSE 額外檢查 axmean-000010 與 ccc。
cal_axisy_exp_daily 的 adapter 明確傳 exp_list，不能偷偷取全部 config。
OUT_FILENAME 改為明確 output_nc，寫暫存後 commit；缺 case 不允許成功。
axisy_meta 支援 HomogRad suffix 與原 RRCE names，單元測試未知/模稜兩可名稱。

plot_inflow_cwv_sep main 用新 adapter 或副本增加 output_dir，
一組資料一次呼叫，不執行原檔 __main__ 中硬編 ctrl+exp 兩次。
scatter 保留 numerical/regression 定義，一個 experiment_nc + explicit control_nc。
使用 case_day 判斷填色，ctrl_day 只負責 CTRL lookup，不因 hollow 改 mapping。
保留現有空心 marker 黑邊風格，除非使用者另外要求邊框著色。
組名 f10_origin/f20/HomogRad 只控制 metadata/路徑，不控制科學計算分支。
不要再保留長串 special_x/special_o 預設清單。
仍使用 plot_io 的 exact CTRL day matching；找不到日數不可插值或 nearest。

完成：人工合成整數/小數 case，驗證兩類圓形；
同一實驗組只一張各類 scatter，輸出包含全部選取的合格 cases；
舊 f10/f20 檔案 hash 不變，HomogRad 新檔名不碰 f20。

### P6：提交、故障與狀態

submit 使用 subprocess argv array，不 shell=True。
拓樸排序、sbatch --parsable --dependency=afterok:ID:ID，
只用真實已取得父 job IDs。已 reuse 的父節點不虛構 ID。
submit --dry-run 列父 stage placeholder，不呼叫 sbatch。
每次 sbatch 前寫 durable submitting intent，收到 ID 後原子記錄 submitted；
解析支援 jobid;cluster，不接受 malformed output。
若程序在 sbatch 成功後、寫 state 前中斷，標為 unknown_submission；
不可自動重送。以 run/stage job name 查 squeue/sacct，再人工處理歧義。
只在明確 never-submitted 的節點做 resume，不能盲目重送整張 DAG。

部分提交失敗停止後續送件，保留已有 jobs，不自動 scancel。
status 區分 Slurm success 與 validated products；不修改 job。
afterok 需科學 producer+postvalidation 都 exit0 才算完成。
所有輸出 receipts 寫在 run state，不污染科學資料目錄。

完成：fake sbatch 驗證多父依賴、partially reused graph、解析錯誤、
送件中斷、重複 submit、dry-run 零次呼叫；不使用真 Slurm 做單元測試。

### P7：驗收與交付

1. 純單元測試：planner/tag/time/parser/output guard/state。
2. integration：synthetic NetCDF/text + fake Slurm，完整 render/submit/status。
3. 原始科學 functions 在小型 fixture 前後數值等价；daily 定義分開比較。
4. 實際 py311 import check、mpirun/grads/help、source input 可讀性，只做低成本檢查。
5. 提供 dry-run/review.md 範例，列出所有 pending/collision，不宣稱 jobs 已執行。
6. 真正科學 case 的 end-to-end smoke run 需使用者提供 config/cases/CTRL path；
   未指定前不得自行選 case 或正式 submit。
7. 更新 README：安裝/CLI、如何改 stage/resources、如何加 dataset、
   reuse/overwrite/復原 unknown_submission、links 如何尋找資料。

## 6. 仍需明確輸入，並非阻止工程實作

- 真正要執行的 config 路徑與 case 清單：目前有 config.py，但沒有授權替使用者挑 cases。
- scatter 的 CTRL NetCDF 實際路徑、要繪製的 day/method；
  可先做 generic CLI 與測試，實際 render 缺值時報錯。
- 未滿完整日/非現有 grid 的科學政策、tangential series min/max：
  此範圍先 fail closed 或保留已明確的現有演算法，不能假定。
- 新 config 是 input path，不必為此次審查建立 config_f10_HomogRad.py 副本。

工程實作可依 P1 到 P7 推進；以上缺少值只阻擋對應的真實運算或未定義科學擴充。
