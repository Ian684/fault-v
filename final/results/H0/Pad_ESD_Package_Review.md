# Pad／ESD／封裝審查結論與需求

依使用者確認，本輪完成審查和需求，沒有要求本輪插入 pad ring、下單封裝或付費投片。核心固定 1.8V、25MHz 外部時鐘；後續獨立原型暫以 3.3V wrapped I/O、48 接點 wire-bond 級別作需求預算。這些是待實際投片計畫核定的規劃，並非現有晶片的電壓／封裝額定。

目前核心有 108 個訊號端點與 VPWR／VGND；其中 debug_status、fault_pc、fault_addr 共 96 位。若全數引出，再加 4 個 DFT、12 個電源／地，至少 124 接點；須另評估至少 144 接點級別。48 接點方向必須將這 96 位轉成 UART 診斷讀回；現版 loader 沒有該功能，不能直接包裝成 48-pin 晶片。

| 項目 | 接點預算 | 需求 |
| --- | ---: | --- |
| clk、reset_n | 2 | 時鐘、供電穩定後才解除 reset；reset 最低有效時間見 reset 審查 |
| UART | 2 | 載入與未來診斷讀回 |
| GPIO | 6 | 2 input、4 output；輸入各自同步 |
| running、boot_error | 2 | 狀態觀察 |
| DFT | 4 | scan_in／out／enable、test_mode；尚未實作 |
| 電源／地 | 12 | core／IO／必要輔助域與回流；數量須由電流、bond wire、IR、ESD 確認 |
| 預留 | 20 | 不能直接視為可用 GPIO |

已確認本地 PDK 有 `sky130_ef_io__gpiov2_pad_wrapped` 的 GDS、LEF 與 TT 1.8V／3.3V 模型，LEF 80×210.965µm；候選 clamped supply pad 75×197.965µm、corner 200×204µm。來源與 hash 沿用 `../signoff_precheck/reports/rules_models_inventory.json`。不能把 core standard cell 直接當 bond-pad driver。現有 2.5×3.3mm die 是核心研究邊界，加入約 211µm 深 I/O ring 後須重做 die／corner／keepout／bond pitch／供電規劃。

完成的電源與 ESD 審查要求如下：

- 優先使用未來投片計畫認可的完整 wrapper／pad ring，核對 signal、clamped supply、corner、filler 和 domain connection cells 的配套。
- 核心 VCCD/VSSD 1.8V 與候選 VDDIO/VSSIO 3.3V 分域；VDDA/VSSA、VCCHIB、quiet rails、amux、unused control 一律依選定 cell 的真實 pin contract 接線，不能憑名稱短接。
- 對訊號、各供電域及跨域建立可追溯放電路徑；檢查 clamp、回灌、斷電輸入、供電順序、latch-up 與 bond-wire 回流。核心 antenna diode 不提供整顆晶片的 I/O ESD 額定。
- reset 須在電源、pad control、時鐘穩定前維持有效；先用外部 reset supervisor，新增片上 POR 須另驗證。
- HBM 2kV／CDM 250V 僅為待核定原型目標，沒有通過額定或實測證據。實際供應商／shuttle 規範優先。
- 本輪 IR 使用既有核心外緣 PG 端點的理想供電，沒有 package／bond-wire RLC；原 SDC 0.03pF 也不是 pad／PCB 負載。完整 chip timing、transient IR、ESD／EM 必須隨實際 wrapper／封裝重查。

審查已完成，必要的介面縮減、UART 診斷、pad ring 與 ESD 實作未宣稱完成。最終 package 型號、bond map、approved deck／waiver 及 ESD 額定需在有實際投片計畫時核定。
