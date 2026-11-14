from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
for p,marker in {
 'tb_mem_arbiter':'ALL 6000 ARBITER TRANSACTIONS PASSED',
 'tb_sram_banks':'ALL 4 SRAM BANK MODES PASSED',
 'tb_asic_boot':'MAXIMUM IMAGE',
 'tb_asic_streams':'ALL STREAM SCENARIO RUNS PASSED',
 'tb_loader_priority':'ALL LOADER ERROR PRIORITY CHECKS PASSED',
 'tb_gate':'ALL MAPPED GATE PROGRAM CHECKS PASSED'}.items():
 s=(R/'logs'/(p+'.log')).read_text(encoding='utf8')
 assert marker in s and not re.search(r'(?i)fatal[: ]',s),p
rows=json.loads((R/'reports/ppa_comparison.json').read_text())
m=rows[-1]
assert m['run']=='tt_delivery_reload'
assert m['design__max_slew_violation__count']==m['design__max_cap_violation__count']==0
for p in ['eco/connectivity_proof.json','reports/threshold_regression.json','reports/opensta_upstream_tests.json']:
 assert json.loads((R/p).read_text())['pass']
table='\n'.join('| '+x['run']+' | '+x['sta_engine']+f" | {x['design__instance__area']:,.4f} | {x['design__instance__count']:,} | +{x['timing__setup__ws']:.6f} | +{x['timing__hold__ws']:.6f} | {x['design__max_slew_violation__count']:,} | {x['design__max_cap_violation__count']} |" for x in rows)
baseline=(R/'history/baseline_Verification_Report.md').read_text(encoding='utf8')
functional=baseline[baseline.index('## 3．已通過的功能驗證'):baseline.index('## 4．Lint 與約束審查')]
functional=functional.replace('本次沒有重新執行所有早期 RV32I directed suite','本次緩衝 ECO 後重新執行最終 mapped 測試；RTL 未變，表內 RTL 測試保留先前通過紀錄，沒有重算為新增測試。本次沒有重新執行所有早期 RV32I directed suite')
lint=baseline[baseline.index('## 4．Lint 與約束審查'):baseline.index('## 5．重現與交付')]
lint=lint.replace('最終 Verilator 0 errors','完整 tt_delivery 重跑的 Verilator 0 errors').replace('配置的 fanout 目標不是已收斂的證明，實際控制網路的高扇出仍須修復。','自訂 SDC 沒有另外宣告 max_fanout；設定值 10 不能解讀成所有 net 的硬性扇出限制。電氣驗收依實際 Liberty slew／cap 限制，非同步 reset 的 false path 沒有因此取消。')
report=f"""# Fault-V ASIC 合成與 pre-PnR STA 驗證報告

## 結論與範圍

完成 SKY130A／sky130_fd_sc_hd 標準元件合成、18 顆 SRAM 整合，以及 **TT、1.8 V、25°C、25 MHz 的 pre-PnR setup／hold／slew／cap 檢查**。最終交付為 `tt_delivery_reload`：從 RTL 完整合成、施加緩衝 ECO，將實際輸出的網表重新讀入 STA，並核對同一檔案的功能模擬結果。

| 最終項目 | 結果 |
| --- | ---: |
| 最差 setup slack | +{m['timing__setup__ws']:.6f} ns |
| 最差 hold slack | +{m['timing__hold__ws']:.6f} ns |
| Setup／hold TNS 與負 slack 路徑數 | 0 |
| Max-slew 違規 | 0 |
| Max-capacitance 違規 | 0 |
| 標準元件面積，不含 SRAM | {m['design__instance__area']:,.4f} µm² |
| Instance，包含 18 SRAM | {m['design__instance__count']:,} |
| Sequential cell | 2,925 |
| 功能網表測試 | 通過所列 UART 與 CPU 案例 |

這是**指定 TT 模型與前佈局假設下的收斂**。沒有放置、CTS、routing、萃取 SPEF、多角落簽核、pad ring 或 foundry sign-off，不能宣稱已可下片。工具介面顯示完整步驟數時，後續實體設計步驟實際上被略過。

## 1．交付設計與來源

| 項目 | 實作與核對 |
| --- | --- |
| 頂層 | fault_v_asic_top，11 ports、108 port bits；核心整合邊界，沒有 pad ring |
| 功能 | 多周期 CPU、12 條自訂指令、DMA、獨立三階段 DOT4 加速器、UART TX、GPIO |
| 記憶體 | 16 KiB 指令＋16 KiB 資料＋4 KiB scratchpad，18×2 KiB SRAM |
| 開機 | UART RX 載入、CRC 檢查、未使用指令區補零，再釋放 CPU |
| 本次 RTL／ISA 改動 | 無；改動為合成設定、正相緩衝網表 ECO 與分析工具版本 |
| 來源核對 | 33 個交付與 Linux 分析輸入雜湊一致；RTL／SDC／Liberty／LEF／GDS 未因電氣修復而修改 |
| 網表身份 | mapped_top.v＝eco/fault_v_asic_top.nl.v＝重新載入 STA 的檔案＝功能模擬的檔案 |
| 證據 | source_identity.json、toolchain_identity.json、reports/identity_check.json、reports/gate_input_identity.json |

`history/` 與舊 run 保存修復前紀錄，不能當作目前交付結果。舊 ZIP 另保存為 Fault_V_ASIC_Synthesis_STA_baseline.zip。

## 2．合成、時序與電氣修復

Clock 40 ns、uncertainty 0.25 ns；輸入 delay max 4/min 0.5 ns、transition 0.2 ns；輸出 delay max 4/min 0.5 ns、負載 0.03 pF。時脈 transition 0.15 ns、理想時脈，沒有繞線寄生。SRAM 的 0.04 ns 腳位 transition 限制沒有放寬。

| Run | OpenSTA | 標準元件面積 µm² | Instance | Setup ns | Hold ns | Slew 違規 | Cap 違規 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
{table}

- 前四個 run 是修復前的 OpenSTA 2.7.0 歷史紀錄；其中有跨 Liberty threshold 轉換錯誤，不能把 4,774→0 全部解讀為硬體改善。
- `tt_sta310` 使用與修復後相同的 OpenSTA 3.1.0，分析啟用 ABC 緩衝的基準網表，仍有 **244 slew、1 cap**；它是電氣 ECO 的比較基準。
- `tt_delivery` 從 RTL 完整重跑合成與結構檢查，再施加 ECO。`tt_delivery_reload` 讀入實際序列化網表，不再重複 ECO，結果一致。
- 最終 Yosys 檢查為 0 unmapped、0 inferred latch、0 synthesis check error；沒有 FPGA DSP48／BRAM primitive。FF 仍為 2,925，並非靠刪除狀態縮小設計。

### 真正的電氣修改

1. 啟用 `SYNTH_ABC_BUFFERING`。原本 AREA 0 未自動對高負載控制訊號建立足夠緩衝。
2. ABC 的 transition 最佳化目標設為 0.03 ns，直接連線 buffer 使用 buf_8。這是合成目標；自訂 SDC 仍沿用原值，沒有用放寬時序要求消除違規。
3. 18 顆 SRAM 的 addr0[8:0]、wmask0[3:0] 合計 234 個輸入，每腳加入 buf_4→buf_16，新增 468 個正相 buffer；另把過載的 _29323_ 由 buf_1 換成 buf_16。
4. 寫出 ECO 網表後重讀 STA。只通過記憶體內的暫時模型而未交付修復網表，不能算驗收。

相對同引擎的緩衝基準，ECO 面積增加約 {m['design__instance__area']-rows[4]['design__instance__area']:,.4f} µm²（{(m['design__instance__area']/rows[4]['design__instance__area']-1)*100:.3f}%），instance 增加 468。新增 buffer 為組合元件，不增加指令 cycle 或暫存器。

`eco/connectivity_proof.json` 將所有正相 buffer 視為直通連接後，比較 **102,975 個非 buffer／頂層接點、27,089 組連通集合**，前後一致；18 個 SRAM、2,925 個 FF 保留。這是限定於 buffer ECO 的結構連接證明，不是 RTL 形式等價。

### OpenSTA threshold 問題與工具核對

原 OpenSTA 2.7.0 對 10–90% 與 20–80% transition 門檻的轉換，會在同網路多個 load 間累積倍率。最小重現用同一 buf_8 驅動 32 個相同 SRAM wmask pin；舊版報告從 0.468540937 到 3498.222900391 ns，新版 32 個腳位皆為 0.468540996 ns。

採用**未修改的官方 OpenSTA 3.1.0**，固定 commit `0f2529d18218b87aa0e82de444395a830d5058a1`，沿用 LibreLane 原本的分析 Tcl、Liberty 與 SDC，只明確替換 STA executable。沒有改 Liberty 數值、刪除路徑或豁免違規。新版仍先報出 244／1 個真實問題，再透過硬體 ECO 修復。

最小案例故意過載，並未通過它的 0.04 ns 限制；它只驗證同網路 threshold 轉換一致性。三個上游 Tcl regression（disable_timing_load_slew、liberty_arcs_one2one_1／2）與官方 golden 相同；沒有執行完整 OpenSTA 測試庫，BUILD_TESTS=OFF 指的是 C++ 測試組態。

證據：verify/threshold_probe.v、scripts/threshold_probe.tcl、reports/threshold_probe*.log、reports/threshold_regression.json、reports/opensta_upstream_tests.json、logs/opensta_fixed_build.log。

### 關鍵路徑與面積範圍

目前最差 setup 路徑為資料 SRAM falling-edge 的 dout0，經 bank selection／讀回邏輯到 rising-edge 回應 FF，仍正確檢查半週期路徑。時序報告的 Fmax 不是實體晶片頻率保證，不能以單一路徑 slack 推定可量產頻率。

SRAM LEF 每顆 683.1×416.54 µm，18 顆合計 **5.121692532 mm²**。標準元件約 **{m['design__instance__area']/1e6:.9f} mm²**，未含通道、電源、利用率留白與 pad，不能直接當 die area。不報實際功耗：未提供代表性活動與萃取寄生參數。

{functional}
{lint}
## 5．重現與交付

官方 LibreLane 3.0.16 Docker digest、PDK、SRAM、OpenSTA／CUDD commits、編譯選項及 binary hash 均在 toolchain_identity.json。使用 WSL2＋Docker；新 STA 在 WSL 建置，透過固定 image 的 runtime 載入，並保留 LibreLane 原分析腳本。

`bash scripts/run_linux.sh <新tag>` 執行合成→ECO→結構核對→序列化網表重讀 STA→驗收；接著 `bash scripts/run_gate_linux.sh` 執行同一 mapped_top.v 的功能模擬。環境建置與 source helpers 詳見 README.md。

MANIFEST.json 記錄交付檔 SHA-256，ZIP 檢查 CRC 與逐檔 hash。封裝前要求實際 PASS log、零電氣違規、正 setup／hold、結構核對與最終網表身份一致。

## 6．後續範圍

| 項目 | 後續需求 |
| --- | --- |
| SRAM 資格 | 目前只有 TT／1.8 V／25°C Liberty；需完整可用角落與正式交付資格，不能借用其他 SRAM 的 SS／FF |
| 實體設計 | Macro floorplan、PDN、placement、CTS、routing、寄生萃取，再做 buffer／driver／hold 修復 |
| 晶片整合 | Pad／ESD、供電、I/O 電壓、clock/reset、DFT／測試存取 |
| 最終簽核 | 多角落、DRC／LVS／antenna、適用的電源／可靠度檢查 |
| 本次未做 | 完整 RTL 形式等價、SDF 功能驗證、完整 ASIC 簽核、實際晶片製造／量測 |

此交付完成合成與指定 TT 的 pre-PnR 時序／電氣驗收，可銜接實體設計；**不代表已具備最終下片資格**。

參考：[官方 OpenSTA](https://github.com/The-OpenROAD-Project/OpenSTA)、[LibreLane 合成設定](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html)。
"""
(R/'Verification_Report.md').write_text(report,encoding='utf8',newline='\n')
print('Generated final measured report with separate historical and current STA evidence.')
