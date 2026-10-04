# RRCE workflow

這個目錄包含可 review、可修改的 Slurm 工作流實作。完整工程契約仍以 [AGENT_IMPLEMENTATION_PLAN.md](AGENT_IMPLEMENTATION_PLAN.md) 為準。

`stages.py` 是唯一的 DAG、資源與 stage 命令表；`templates/stage.sbatch` 是 Slurm 模板。修改兩者後重新 render，就能在新 run 的 `review.md`、`plan.json`、`jobs/`、`patches/` 檢查所有展開值與差異。submit 會拒絕任何被手動改過的 render 結果。

- [ARCHITECTURE.md](ARCHITECTURE.md)：現有程式的輸入輸出、依賴圖、需要修改之處、預計的 workflow 程式架構，以及尚待確認的問題。
- [manifest.example.toml](manifest.example.toml)：可直接複製修改的 TOML manifest。早期 YAML 僅保留作設計紀錄，CLI 不讀取它。
- [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md)：HomogRad 日數解析、時間窗、CTL、並行退出狀態與產物保護的實作契約。

基本操作：

```bash
python -m workflow.cli plan --manifest workflow/manifest.example.toml --dry-run
python -m workflow.cli render --manifest workflow/my-run.toml
python -m workflow.cli submit --run-dir workflow/runs/RUN_ID --dry-run
python -m workflow.cli submit --run-dir workflow/runs/RUN_ID
python -m workflow.cli status --run-dir workflow/runs/RUN_ID
```

status 預設輸出精簡的人類可讀摘要，包括整體狀態、是否已結束、submit
進度、成功/失敗/執行中/等待中的 job 數量，以及失敗 stage 的 Slurm exit
code 與 log 中可辨識的例外原因。只有 render、尚未 submit 時會明確顯示
RENDERED_NOT_SUBMITTED；完成與部分失敗則分別顯示 COMPLETED、FAILED。
需要程式讀取時使用 --json 取得摘要 JSON；需要完整 submission state 與原始
scheduler 結果時使用 --raw-json。

`plan` 永遠唯讀。`render` 以 exclusive create 建立 run directory，保存 config/source snapshot、SHA-256 lock、展開後的 jobs 和 artifact links，但不提交。`submit` 只接受未被修改的 run directory，依拓樸順序取得真實 job ID，再組合 `afterok`。`run.allow_overwrite = true` 只授權 render 時已存在且列於 plan 的精確 collision；render 後才出現的新檔案仍會拒絕。沒有設定時預設不覆寫。

每個 stage 的 `action` 可設為 `run`、`reuse` 或 `auto`：

- `run` 一定執行；已有預期輸出會列為 collision。
- `reuse` 一定跳過，但只要缺少任何預期輸出，plan 就會報錯。
- `auto` 只依檔名逐一檢查每個 case 的完整預期檔案集合。某 case 的檔名全部存在時只跳過該 case，其他不完整的 case 繼續執行；跨 case 的 aggregate stage 則在全部輸出存在時整個跳過。

只有 subdir 存在不算完整。為縮短大量檔案的 render 時間，驗證採 `count_and_last`：逐一確認每個 case 的全部預期檔名存在，但每種產物只讀取最後一筆，檢查空檔、NetCDF 可讀性與必要 variables、center timestep、PNG signature 或 CTL directives。`axisy_convert` 每個 case 也必須有 `axisy_<exp>.ctl`，所以會分別檢查最後一筆 NetCDF 與該 CTL。這個策略能發現缺號及尾端失敗，但不會開啟中間每一筆來偵測單一損壞檔。

缺少任何預期產物時，`auto` 會把該 case 規劃為重新執行；若同一 case 已有部分產物，它們會列為 collision，只有 `run.allow_overwrite = true`（或 submit 明確傳入 `--allow-overwrite`）才允許覆寫 render 時已列出的精確路徑。

若 render 發現 producer 有 missing/invalid products，但 producer 本身可執行為 `run`，下游仍會產生 job 並以 Slurm `afterok` 等待；producer 執行後若產物驗證失敗，非零退出狀態會阻止下游。只有 producer 本身無法執行，例如指定 `reuse` 卻缺少產物或缺少必要 external input，才解析為 `blocked` 並向它的直接與間接下游傳遞。blocked stage 不產生 sbatch、`submit --dry-run` 與正式 submit 都不會列入；其他無關 DAG 分支仍可執行。`blocked` 是 planner 的解析結果，不是 manifest 可填的 action。

`auto` 已跳過的完整 case 不受 overwrite 影響；若要強制重算，明確改用 `run`。`plan.json` 會記錄 `requested_action`、解析後的 `action`、`skipped_cases`、`missing_products`、`invalid_products` 與 `blocked_by`，`review.md` 也會顯示相同摘要。

耗時的 axisy postprocess 已拆成 `axisy_mean`、`axisy_process`、`axisy_daily` 三個 stage，可各自按 case 判斷並列出跳過項目。舊 manifest 的 `[stages.axisy_postprocess]` 仍可使用，會自動展開到這三個 stage。

`axisy_convert` 保留原本的 224 tasks、217 ranks 與逐 case 執行作為預設。需要跨 case 並行時，可在 manifest 的 `[resources.axisy_convert]` 將 `tasks` 設為 `ranks` 的兩倍以上；runner 會把不同 cases 分成 exclusive Slurm steps，同時執行數為 `tasks // ranks`。例如 `tasks = 434`、`ranks = 217` 會一次處理兩個 cases，case 數為奇數時最後一批只啟動一個 step。`cal_axisy.py` 不需更動。

Slurm job 會執行 `source ~/.bashrc` 與 `conda activate py311` 後才啟動 Python。

直接使用 config 也可以：

```bash
python -m workflow.cli plan --config config.py --dataset-tag f10_HomogRad --cases 0 6 11 --dry-run
python -m workflow.cli render --config config.py --dataset-tag f10_HomogRad --cases 0 6 11 --run-id hrad-review-01
```

直接使用 `--config` 時維持原本的 `run` 且禁止覆寫；建議使用 manifest 明確設定每個 stage 的 `auto`，並以 `run.allow_overwrite = true` 處理 partial collisions。提交時仍可用 `--allow-overwrite` 或 `--no-overwrite` 覆寫 manifest 的選擇。

真實提交前，manifest 的 `inputs.control_profile_nc` 必須指向可讀檔案。每個 stage 必須明確填 `run`、`reuse` 或 `auto`；reuse 與 auto 都會逐項檢查預期檔名。`unknown_submission` 表示程序可能已成功呼叫 sbatch、卻還沒保存 job ID，此狀態不可自動重送，應先用 job name 查 `squeue`/`sacct`。

已確認 dry-run 為不提交、不寫入的預覽；實驗組名稱可明確指定，或從 `config_<name>.py` 推導。完整規格見 ARCHITECTURE.md 第 11 節。整數日實心圓、小數日 ensemble 空心圓已定案。
