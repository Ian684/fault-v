# Week24 除錯流程檢查

2026-10-28：重新核對實際日誌、保存版圖及原生天線檢查；Week24 尚未完成。

檢查到的問題：

- 低 DRC 與低天線數來自不同版本。已用同一 ODB 的 SHA256 綁定兩項指標，證據在 `coherent_checkpoint_review.json`。7 DRC 版本仍有 139 條天線違規；27 DRC 版本有 2 條；36 DRC 版本有 4 條；另有 110 DRC、零天線版本。
- SRAM 角落有 31 個完全相同的標記，跨三份報告仍未消除。原流程在重複違規上花費多輪計算。
- 原生日誌的 elapsed time 會包含 Docker 暫停時間。診斷工具已分別記錄 CPU 秒數與連續未改善輪數，避免直接把低 CPU/elapsed 比值解讀為效能瓶頸。
- 新分段流程的首次實跑發現重複初始化問題：同一批 110 個實際標記被列成 220 個。已停止該試驗並保存原始碼；相同版圖的原生對照測得 `110 → 220 → pin_access 重置後 110`，每次完整線段、via、元件、連線圖及 PG 幾何都相同。詳見 `router_reset/control.json`。新版本已在重複初始化前重置，且遇到基準不一致時停止調查。

已啟動的改進：

- 從有實際連線與模型證據的零天線版開始，最多四個短階段，針對違規附近修復；不使用全域 ALL 重繞。
- 每階段先用原生 `step_end` 寫回版圖，再測天線，保存獨立 ODB、DRC/天線數與 SHA256。避免把尚未寫回的內部路由狀態當成已保存結果。
- 天線增加、連續兩階段沒有改善、或單次原生試驗超過 1,800 秒時停止該次試驗，保存已完成的階段並恢復備援工作。此時間是試驗上限，不是 Week24 完成預估。
- `test_antenna_checkpoint_pairs.py` 的正例、錯誤版圖雜湊負例及聯合比較測試已通過；實際過早驗收負例也確認不會改動既有交付結果。詳見 `validation.json`。
- 提前的元件、連線圖、PG 與原生擺放檢查已通過；刻意製造的記憶體內二極體重疊被檢查器偵測，原檔未改。詳見 `zero_source_geometry.json`。

查詢目前實際程序與同版指標：

```powershell
wsl -d Ubuntu-D --cd /mnt/e/Codex/Fault_V_W24_Transfer/work/fault-v-asic/routing --exec python3 scripts/check_antenna_progress.py
```

所有原有連線、擺放、PG、寄生萃取、TT 電氣與時序、獨立 DRC 驗收仍須通過，才能接受新版本並製作新版交付檔。

原生幾何寫回順序核對：[固定 OpenROAD 版本的 stepDR / endFR 原始碼](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/TritonRoute.cpp#L662)。
