# Fault-V ASIC Floorplan and Power Plan

正式工作區：`D:\Codex\WSL\fault-v-asic\floorplan`。
Linux 同一位置：`~/fault-v-asic/floorplan`；資料實際位於 D 槽。

設計筆記請讀 Floorplan_Power_Notion.md；測試與限制另放 Verification_Report.md。設計筆記不記錄週次或進度。

## 已提供

- 已驗收合成網表、SDC、頂層 JSON header 與 SRAM LEF／GDS／TT Liberty。
- 固定 macro locations、pin order、單一電源域及核心 PDN 設定。
- Floorplan／tap／endcap／PDN／pin placement 的 ODB、DEF、netlists。
- 實際資料庫檢查器、幾何圖、完整採用 run 的執行紀錄及重現紀錄。
- input_identity.json、technology_identity.json、MANIFEST.json。

## 在現有 D 槽工作區重現

```bash
cd ~/fault-v-asic/floorplan
bash scripts/run_floorplan.sh floorplan_new_run
```

使用未存在的新 tag。腳本失敗會以非零碼結束；檢查紀錄在父層 logs，結果 JSON 在 reports/<tag>。

預期結尾：

```text
ALL FLOORPLAN GEOMETRY / POWER CONNECTION / FUNCTIONAL CONNECTIVITY CHECKS PASSED
```

原始 flow 與自動檢查的 stdout／stderr 都會寫入 log；不在終端逐行刷出。

只重看既有採用 ODB：

```bash
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(cd .. && pwd):/work" -w /work/floorplan \
  ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302 \
  openroad -exit -python scripts/check_floorplan.py
```

繪圖在具備 matplotlib 的 Python 執行：

```text
python scripts/render_floorplan.py
```

## 交付檔案自檢

```text
python scripts/check_delivery.py
```

此命令驗證交付 manifest、鎖定輸入與兩份檢查報告，不代替重新執行 EDA。

## 解壓與工具需求

ZIP 的頂層資料夾為 floorplan。若在其他位置恢復，使用新的父資料夾，將本包放為 <root>/floorplan，同層準備 <root>/pdk。需要 Linux／WSL、Docker、指定映像及相同 revision 的 Ciel SKY130 PDK。

本包包含這個核心的 floorplan 輸入與結果；沒有重複封裝整套 PDK、Docker 映像或 Ubuntu。PDK 取得與使用須符合其授權及交付條件。technology_identity.json 提供本次使用的關鍵檔案 hash。

所有容器內絕對路徑使用 /work/floorplan 和 /work/pdk，由 run_floorplan.sh 的 bind mount 提供，不指向舊 C 槽。

實體交接以 runs/floorplan_accepted/final/odb/fault_v_asic_top.odb 為主，配合原設定、巨集 views 與 SDC。handoff_state.json 的所有 views 都指向交付包內的 final 檔案，供下一階段讀取，不依賴省略的中間 ODB。此包未包含 placement、CTS、routing 後的簽核資料。
