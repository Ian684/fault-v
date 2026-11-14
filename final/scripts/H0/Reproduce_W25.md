# W25 證據驗證與重跑入口

最終結果由 `reports/W25_closure_result.json` 與 `W25_Closure_Report.md` 定義。只在四個同版 gate（post、core、IR、fill）全部通過後產生；不存在這些檔案就表示尚未結案。正式 PPA、W26 及完整 foundry signoff 另行追蹤。

## 驗證現有證據

在 Windows 的本目錄使用 Python 3.13：

```powershell
python scripts/seal_w25_evidence.py verify
```

此命令逐一重新讀取 manifest 內的檔案，核對 byte 數與 SHA256，不改任何凍結證據。gate 的實際數值門檻見 `controls/final_acceptance_criteria.json`；不能只根據 shell exit code 判定通過。

## 工具與路徑

使用 Ubuntu-D／Docker，根工作區掛載為 `/work`。固定 image 為：

```text
ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302
```

PDK 固定為 `pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A`，標準元件為 `sky130_fd_sc_hd`。OpenSTA 使用 `routing/sta_tool/sta`（3.1），其 CLI 為 `routing/scripts/sta310_cli.py`。SDC 為 `week25_signoff/constraints_reviewed.sdc`。完整核心 GDS 使用 `macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim_dedup.gds`；LVS-only view 不可替代它。

E 槽為保存位置。`/var/tmp/faultv-w25-closure-20261101`、`/var/tmp/faultv-w25-finalprep` 和 `/var/tmp/faultv-w25-native-runs` 只是原生檔案系統計算副本，必須以 E 槽原件 SHA 核對。每個 flow 的 `native_archive_manifest.json` 記錄原生與 E 槽 byte-exact 對照。

## 同版重跑依賴順序

保留現有結果；重跑須在另一個 E 槽工作副本及新的原生 scratch 根目錄中使用新的 run tag。腳本會拒絕覆寫已存在的 config、native alias 或 run 目錄。W26 可將這些入口整理成乾淨交付包；目前不提供會刪除既有結果的清理命令。

1. 起點 `inputs/native_group_w.odb`：51 個等價 driver、PG_G、20 個新增二極體、五條重接支線，其中四顆新增被動二極體經合法 row 搬移。`reports/native_group_w/result.json` 記錄幾何差異與放置證據。全部原邏輯元件、網路及供電幾何仍受 invariants 檢查。
2. `scripts/run_native_candidate_checks.sh`：獨立全晶片／完整鄰域 DRC、全部 41,337 條多端網路幾何連通、原生確切匯出及 binding；不得以未初始化 router 的內部計數替代。
3. `scripts/run_final_selected_w.sh`：驗證上述結果後，stage 不可變的 final_route_c，檢查原元件／接線／PG 不變及四顆允許的被動二極體差異。之後執行 filler、完整 GDS、DRC、antenna、fresh RCX 及三 RC TT STA。
4. `scripts/verify_final_post.py`：逐檔驗證 archive、實際 DRC RDB／metrics、antenna 及 setup／hold／slew／cap，核對新網表和三份不同 SPEF。
5. `scripts/run_final_core_lvs.sh`、`scripts/run_final_stream_audits.sh`、`scripts/run_final_functional.sh`：同版核心介面 LVS、原宏／標準元件／via stream audit、PG 接觸、填入 filler 後 DRC／連通、reset／CDC 及四個活動工作負載。`scripts/verify_final_core_results.py` 嚴格核對來源。
6. `scripts/run_final_ir.sh`：fresh nominal SPEF、最終 mixed VCD、14／28mW 每 SRAM 的 VPWR／VGND 四種平均電流分析。`scripts/audit_pg_em.py` 用實際 resistor 值推得合併 cut 數與有效線寬，沒有統一除以八。`scripts/verify_final_ir_results.py` 核對逐檔來源及預先記錄的研究 IR budget。
7. `scripts/run_final_fill_parallel.sh`：從實際最終核心 GDS 重新產生 20 tiles fill，修復 FOM／LI、檢查 1,053 個滑動視窗、5nm grid、FOM 幾何、原幾何不變及 post-fill BEOL 互動。10GiB BEOL job 等 IR 結束後執行。`scripts/verify_final_fill_result.py` 核對實際來源與既有六層負控制。
8. `scripts/build_w25_closure_report.py` 只在全部 gate 通過後產生研究範圍結案報告。`scripts/seal_w25_evidence.py create` 建立證據 manifest，再執行 `verify` 才更新專案狀態。

核心介面 LVS 正控制及刻意移開一個 SRAM pin 的 44-error 負控制保留在 `reports/core_lvs_method_verified.json`。填充六層寬度負控制、實際 deck 與 GDS 的 hash 保留在 `reports/dense_b_verified.json`。活動解析器 self-check、四態未知時間與 SRAM 輸入覆蓋都必須保留。

上述路徑與參數為已執行的驗證入口；重跑時保留所有 scope 限制。研究版通過不等於合格 SRAM 內部、foundry、多 PVT、fill-aware PEX、類比 CDC/reset 或完整封裝可靠度通過。
