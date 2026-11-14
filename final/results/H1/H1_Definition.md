# H1 定義：縮小晶片

## 唯一變更
- 只改 die、core 與 SRAM 位置。
- SRAM 仍是 3 × 6 方格，排列順序與方向（N）不變，外緣維持 120 µm。
- 只縮小 SRAM 之間的間隔（H0：欄間 96.9 µm、列間 103.5 µm）。

最終尺寸取「global routing 零溢位」中 die 最小的一組：**2470 × 3217 µm（7.946 mm²，−3.7%）**。

- Core：`80.04 81.6 2389.24 3133.44`
- SRAM x：120 / 893 / 1666
- SRAM y：120 / 632 / 1144 / 1656 / 2168 / 2680

## 尺寸選擇
| 方案 | 欄／列間隔 (µm) | Die (µm) | 面積 (mm²) | 相對 H0 | 結果 |
|---|---|---|---|---|---|
| H0 | 96.9 / 103.5 | 2500 × 3300 | 8.250 | — | 零溢位 |
| gap80（`impl/`） | 80.9 / 80.5 | 2452 × 3142 | 7.704 | −6.6% | 不可繞線：溢位 6,047 |
| gap85x88 | 84.9 / 88.5 | 2460 × 3182 | 7.828 | −5.1% | 不可繞線：溢位 7,637 |
| gap88x92 | 87.9 / 92.5 | 2466 × 3202 | 7.896 | −4.3% | 不可繞線：溢位 1,914 |
| **gap90x95（採用，`cand_gap90x95/`）** | 89.9 / 95.5 | 2470 × 3217 | 7.946 | −3.7% | 零溢位：GRT 資源使用率 28.8%，GRT 線長 6.60M µm |

採用的 H1 在 placement 的利用率是 33.1%，低於目標密度 0.40，GPL 不必強迫平均分布。CTS 後清掉 12 條 clock NDR。

- gap80 的溢位約 86% 落在 SRAM 上方容量為 0 的 GCell。通道裝不下的走線被擠到 SRAM 邊緣，以第 4、5 列 SRAM 一帶最嚴重（`impl/diag/congestion_bins.json`）。
- 這個方案的 placement 利用率是 43%，高於目標密度 40%。GPL 因此只能把元件平均攤開，H0 則是 25.7%。
- 依 `floorplan/fp_options.py`，間隔縮到 70 µm 或 60 µm 時，可放置區的標準元件密度會到 65% 或 87%，判斷不可行。
- 放寬後各方案的密度由 `floorplan/fp_relax.py` 計算。

## 與 H0 相同的部分
- 網表：`design/mapped_top.v`（`88b35c08…`），就是 H0 進入實體流程時的網表。
- SRAM 輸入／輸出 buffer 定位：演算法與 H0 `placement_cts/scripts/anchor_inputs.py` 相同，只改了路徑。
- 繞線前清掉 CTS 的 clock NDR，做法與 H0 `routing/scripts/prepare_clock_rules.py` 相同。
- SDC：實作階段用 `design/constraints.sdc`（`b268acd6…`），簽核與功耗用 `week25_signoff/constraints_reviewed.sdc`（`979a8d3f…`），兩者都與 H0 相同。
- 腳位順序：`pin_order.cfg`。
- PDN、halo、placement、CTS、routing 的設定：從 H0 各階段的 config 複製，由 `make_configs.py` 產生。
- SRAM views：與 H0 最終驗收相同，也就是 antenna LEF、TT Liberty 和 orphan_trim_dedup GDS。
- 工具：固定的 LibreLane image，以及同一套 PDK。

## 與 H0 不同、必須在比較時說明的部分
H0 繞線後，曾在 W24／W25 做了多次手動修補：
- 51 個 driver 調整、20 顆被動二極體、局部金屬橋
- PG_G 供電修正
- 重新產生 fill
- 時脈 ECO（eco_clock_remote_a／b）加 3 顆 hold buffer

H1 照 H0 的方法收斂，但細節不同：
- 繞線前修復：與 H0 同一配方、同一組設定（RepairDesignPostGRT + ResizerTimingPostGRT）。唯一偏差是修復時用了最終繞線的 GRT 設定（時脈走 met4／met5）。
- 繞線後：手動局部重繞 3 輪（d1、d2、x1），清除 SRAM 角落的 DRC；用 H0 的 RC 規則做 3 輪 RC ECO（rc1c、rc4r、rc5）；原生補天線 5 輪（f1–f5）。
- 第一次完整簽核（`h1_eco_rf6`）漏掉了繞線前修復，3-RC STA 失敗，結果只留作參考。H1 從還沒插 diode 的 global route 結果開始，照 H0 配方重做（h1b）。
- 電源 via 修補（h1c）：h1b 的平均 EM 失敗（單切孔 via4，28 mW 時最差 5.77 倍）。照 H0 PG_B／PG_C／PG_G 的作法分 6 輪修補（`eco/pg_h1_fix*.py`）：via4 改成 8 切孔、1 × 16、兩欄或三欄的陣列，熱點加 2.8 µm M4 加寬片與 M5／M4 補片。每處都要通過局部原生 DRC 才會接受。
- 結案檢查沿用的 H0 密度腳本把 die 尺寸寫死為 H0 的 2500 × 3300 µm。H1 版改讀實際 die（2470 × 3217 µm，GDS prBoundary 與 DEF DIEAREA 交叉核對），方法與門檻不變（`closure_c/scripts/check_sliding_density_die.py`）。

## 結果
- **h1b（2026-11-13）**：通過與 H0 相同的簽核：原生 DRC／KLayout DRC／antenna 0、3-RC STA 違規全為 0、核心 LVS 乾淨（反向測試 44 個錯誤）、reset／CDC 與四個工作負載通過、活動對應 100%。
- **h1c，最終版本**：
  - 電源 via 修補後重做全晶片 DRC／antenna（0／0）與整套簽核（`signoff/run_signoff_c.sh h1c_pg_r1`），全部通過。PPA 數字在報告精度下與 h1b 相同：只有 11 條訊號網路的耦合電容有微小變化（最多 +1.1%），功耗差 0.000001 mW。
  - H0 W25 結案的實體檢查也全部通過（`closure_c/reports/H1_closure_result.json`，14 項）：
    - 全晶片 DRC 0 個未解決、40,850 條網路全部連通、SRAM／元件／via stream 一致、電源與地無接觸；
    - IR 30.5／57.8 mV、EM 最大利用率 0.518／0.981（14／28 mW）；
    - dummy fill 密度每層 999 個視窗通過、grid／FOM 通過、BEOL 互動 0。
  - 最終 routed ODB 為 `cand_gap90x95/runs/h1c_pg_r1`（`29a706cf…08651`），加 fill 的 ODB `9c06b1b0…dc402`。

H0／H1 正式比較見 `../formal_h1/H0_H1_PPA_Report.md`。
