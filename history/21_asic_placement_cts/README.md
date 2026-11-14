# Fault-V ASIC Placement / CTS

- `Placement_CTS_Notion.md`：可貼入 Notion 的設計筆記，不含進度紀錄。
- `Verification_Report.md`：實際驗收結果、重跑證據、工具限制與未完成項目。
- `figures/placement_cts.png`、`.svg`：由驗收後 OpenDB 的座標與 clock 連接產生。
- `handoff_state.json`：繞線階段的實際輸入；沒有攜帶過期的估算 SPEF。
- `accepted_summary.json`、`reports/placement_release/`：本次正式交付結果。
- `MANIFEST.sha256.json`：交付檔案完整清單與 SHA-256。

## 讀取交付包

解壓 ZIP 後的頂層為 `placement_cts/`。離線檢查不需要 EDA：

```powershell
python .\placement_cts\scripts\check_delivery.py
```

不要在唯一一份封存交付上直接重跑；重跑會更新狀態與輸出，原有交付 manifest 將不再相符。請保留 ZIP，使用工作副本。

## 完整重現

現行 ASIC 工作區位於 D 槽：
`D:\Codex\WSL\fault-v-asic\placement_cts`。
WSL 的 `~/fault-v-asic` 指向該 D 槽工作區。

需要 Docker、Python 3，以及 `technology_identity.json` 指定的 PDK。PDK 與 Docker image 不含在 ZIP。解壓的 `placement_cts` 必須位於 ASIC 工作根目錄下，並與 `pdk/` 同層。容器固定把工作根目錄掛到 `/work`。

```bash
cd ~/fault-v-asic/placement_cts
chmod +x sta_tool/sta sta_tool/sta.bin
bash scripts/run_all.sh placement_reproduce
```

或從 Windows：

```powershell
wsl -d Ubuntu-22.04 -u <user> --cd <HOME>/fault-v-asic/placement_cts chmod +x sta_tool/sta sta_tool/sta.bin
wsl -d Ubuntu-22.04 -u <user> --cd <HOME>/fault-v-asic/placement_cts bash scripts/run_all.sh placement_reproduce
```

Tag 僅接受英數字與底線；同名 run 已存在時停止，避免把歷史結果誤當新執行。換一個 tag 可再次重現。腳本先驗證原始輸入與 runtime SHA，再重新產生局部驅動器、執行放置／CTS、末次電氣修整、OpenSTA 3.1.0、幾何／供電／連接證明，最後才更新 handoff。執行紀錄位於 ASIC 根目錄 `logs/`。

## 輸入與工具

原始 floorplan ODB 位於 `inputs/fault_v_asic_top.odb`；`inputs/anchored_floorplan.odb` 是可由原始 ODB 與 `anchor_inputs.py` 重新生成的衍生輸入。`input_identity.json` 凍結來源、設定、正式腳本及 STA runtime，`technology_identity.json` 凍結 PDK 關鍵檔案與容器版本。

OpenROAD 內嵌 STA 2.7.0 的混合 threshold 問題由小型負載測試重現；驗收使用隨包的未修改 OpenSTA 3.1.0，以實體工具輸出的估算 SPEF 與 propagated clocks 重新分析。其 loader 僅用於指定容器；見 `sta_tool/README.md`。階段名稱沿用 LibreLane 的 `STAPrePNR` 包裝器，但實際讀入的是 CTS 後網表與估算 SPEF，不是零導線負載分析。

## 繞線交接

讀取 `handoff_state.json` 的 final ODB／網表／SDC，保留 `config.json` 的局部修整保護規則、既有 macro 位置、PG 與 I/O。先做 global routing 再詳細繞線；重新產生寄生參數、確認 SRAM 40 ps 限制及 setup／hold。新修整需要重新檢查幾何、PG、連接與時序。

本包完成的是 TT、放置估算 RC 下的 Placement／CTS 階段驗收。它不包含實際訊號繞線、製程全角落簽核、完整 DRC／LVS、IR／EM 或可直接送廠的完整晶片整合。

ZIP 保留 Unix executable attributes；若用 Windows 解壓，請先執行上述 chmod。交付保留正式 final views 與步驟紀錄，未收錄所有大型中間 ODB；完整重跑從凍結的來源 floorplan 開始。
