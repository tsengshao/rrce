# 補充實作契約

本文件補充 ARCHITECTURE.md；以下是實作時必須處理的程式細節，而非新增科學分析設定。

## case 與實驗組

Python case index 是 config.expList 的零起算位置；不得重新排序或刪除 config.expList 後再傳原 index。GrADS 的時間 index 是一起算，因此時間 t 對應 NetCDF 檔案 index t-1。

axisy_lowlevel_new/axisy_meta.py 的 parse_restart_day() 目前只讀最後一個 underscore token，cluster_f10_d20_HomogRad 會嘗試 float("HomogRad") 並失敗。新解析器應辨識 cluster 名稱中的 d20/d14p986 token，保留完整 experiment name 作為 key；旧 RRCE 名稱仍需相容。解析結果必須寫入 plan 供 review，遇到多個候選或未知格式就要求明確 case_day mapping，不猜日期。

既有 axisy_exp_daily_profiles_origin.nc 的 dataset tag 是 f10_origin；既有 axisy_exp_daily_profiles.nc 是 f20。這是來源對應，不搬移或重新命名既有 NetCDF。新增 f10_HomogRad 使用獨立 output_nc，絕不可寫進 f20 的既有檔名。

整數日/小數日 marker 判斷使用原始 case_day，不能使用可能已四捨五入的 ctrl_day。小數日屬於哪個整數日 ensemble、CTRL 對應使用精確日或共享整數日，必須保留既有科學定義並在 plan 列出；不能因為改 marker 就改 CTRL lookup。

## 時間窗與完整性

cal_axisymmetricity_daily.py 第 0 天平均 index 0..71，第 1 天 72..143；cal_axisy_exp_daily.py 則 day 0 是 snapshot index 0，day 1 平均 1..72，day 2 平均 73..144。這兩種 daily 不是同一產物，不應互相替代。manifest 與輸出 metadata 必須清楚記錄兩套定義。

多個 center、cloud、axisy scripts 會覆寫 config.totalT 為 217 或 2521，部分 daily draw scripts 固定只畫三天。支援任意 config 前，需在 workflow 使用的副本或參數化入口移除這些硬編；不能只修改 shell cases 就宣稱支援任意長度。未滿一天的資料如何處理屬於科學選擇，遇到時列出錯誤，不悄悄截短。

cal_axisy_exp_daily.py 會跳過缺檔 case 後仍成功寫出其他 cases。stage 最後必須比對輸出 exp 集合和本次選取集合完全一致；缺少 case 時退出非零，讓 afterok 阻止下游。大量序列採快速驗證：核對每個預期檔名的數量與連續性，每個 case/產物類型只開啟最後一筆檢查可讀性和必要 variables；這能抓到缺號與尾端失敗，但不保證偵測單一中間檔損壞。

目前缺少產物但可執行為 `run` 的 producer 不會在 render 階段封鎖下游；下游 job 以 `afterok` 等待，producer 的 runtime 產物驗證失敗時自然不會被放行。只有 producer 本身無法執行，例如不完整的 `reuse` 或必要 external input 缺失，才會解析為 `blocked` 並向其依賴分支傳遞。

## stage 資源與退出狀態

GrADS 按最多 112 個單核心程序分批跑完所有 cases 的全部 timestep。逐一保存 PID 並檢查每一個 wait 的退出碼；無參數 wait 或只檢查最後一個 PID 不能保證所有子程序成功。GrADS 還需檢查預期 PNG 存在且非空，必要時檢查 log 中的讀檔錯誤。

center 程式雖匯入 MPI，卻未分配時間給各 rank，而且直接以 write 模式打開同一中心檔。每個 case 只能啟動一個 Python process；並行只允許不同 cases，所有 PID 都要檢查。

cloud/find_cloud.py 每個 MPI rank 的 CloudRetriever 又使用 cores=15。預設配置使用 `ct448`、448 tasks、`mpirun -np 29`，內部最多使用 435 cores；render 必須展示此配置，不能直接改成 448 MPI ranks。亦需處理 cloud/find_cloud.py 的 util_axisymmetric import：該模組位於 axisy/，adapter 要指定可控的 module search paths，避免誤載同名 util_draw.py。

axisy 的 reduce 與 daily 都寫同一 axmean CTL；第一版 combined postprocess 依序完成三種程式，避免同時寫入。postprocess 的 MPI ranks 不得超出申請 tasks。

## 輸出保護、重用與 links

資料保留在目前 config.dataPath 的 experiment 子路徑；圖片保留相應分析目錄下的 experiment/dataset 子路徑。原始 scripts 不覆蓋，必要變更採可 review 副本或新增入口。

保護單位必須是 stage 的精確檔名模式。例如 axisy_convert 寫 axisy-*.nc，reduce 寫 axmean-*.nc；不能因為共用 case 目錄已存在，就誤認下游輸出衝突。禁止刪除整個 case 目錄來重跑其中一個 stage。

同一 stage 允許 case_actions 明列哪些 cases run、哪些 reuse。已完成的實驗經完整驗證後可 reuse；缺檔或部分完成的實驗需人決定重新計算。stage job 只執行 run cases，仍統一產生一個 stage job ID。不得自行跳過既有資料而不記錄。

overwrite 必須額外使用 submit --allow-overwrite，且僅適用 lock plan 中列出的產物。submit 與 job 開始前都重查衝突，使用 stage/experiment 鎖防止兩個 workflow 同時写入。flag 不授權修改不在本次 cases 中的檔案、不授權刪除整個資料根目錄。更改上游後，所有 reuse 下游必須重新驗證來源一致性。

workflow/runs/<run_id>/artifacts/data、ctl、figures 包含明確指向該次使用/產生之資料的 symlinks；另以 artifacts.tsv 記錄來源路徑、producer stage、expected/available/invalid 狀態。links 可以先建立為 dangling，job 完成後驗證目標；不得以 link 存在作為完成判斷。

## CTL

convolve 使用現有 template，依本次 kernel 清單產生 EDEF 1 NAMES 150km，TDEF 使用實際 totalT；horisf 參考 generate_ctl.sh，保留 sf=>msf 的 GrADS 變數名稱對應。不得掃描所有既有實驗再覆寫 CTL。

兩個 template 的 X/Y/Z 都硬編。產生 CTL 前必須核對 NetCDF 維度與垂直座標，不能對不相符的新網格直接複製。horisf 的 TDEF 不可單純用 nc 檔案數，因為檔數相同仍可能缺中間 timestep。

water/wind 另外需要 data/wp/<exp>.ctl，但 cwv/wp.py 只產生 NetCDF。必須補一個 wp_ctl producer 或驗證既有 CTL，DAG 增加 cwv -> wp_ctl -> water/wind。CTL writer 需根據實際 NetCDF 變數、dimensions 與既有 GrADS 座標慣例生成；不能只建立 symlink 假裝已生成。
