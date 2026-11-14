# Fault-V：ASIC 前置選型

主方案採 **SKY130A＋HD 標準元件庫＋LibreLane**。先完成 SoC 核心的實體設計，再整合完整晶片外殼。本文記錄選型與設計要求，不代表已完成 ASIC 合成或簽核。

## 1．製程、工具與實作目標

| 項目 | 選型決定 | 說明 |
| --- | --- | --- |
| 製程／PDK | **SkyWater SKY130，`sky130A`** | 使用130 nm開放PDK的研究／原型流程；整個設計採同一變體 |
| 標準元件庫 | **`sky130_fd_sc_hd`** | CPU、控制器、DMA與加速器邏輯映射至HD元件庫 |
| 核心電源 | **標稱1.8 V，單一核心電源域** | 不加入多電壓核心或power gating；I/O電源依pad要求另接 |
| 主流程 | **LibreLane 3.0系列穩定版** | 核心用Classic流程；整晶片用Chip流程；安裝驗證後固定release tag／commit及Nix lock |
| SystemVerilog前端 | **Slang＋Yosys，啟用`USE_SLANG`** | 保留package、enum等語法，先驗證整個設計能正確elaborate |
| 邏輯合成 | **Yosys＋ABC** | 產生映射到指定標準元件庫的閘級網表 |
| 實體設計 | **OpenROAD** | Floorplan、PDN、Placement、CTS、Routing與寄生參數萃取 |
| 時序／版圖驗證 | **OpenSTA、Magic／KLayout、Netgen** | STA、DRC、版圖檢視、萃取與LVS；最終檢查集合依交付規則固定 |
| 執行環境 | **Windows＋WSL2 Ubuntu 22.04，x86-64** | ASIC工作目錄放WSL Linux檔案系統；Windows保存交付資料 |
| 版本管理 | **Nix＋LibreLane指定的Open PDKs revision** | 依流程相容的Ciel／PDK管理方式取得資料；固定工具、PDK與巨集雜湊 |
| Clock | **外部單一clock；初始目標25 MHz／40 ns** | 不加入PLL；50 MHz列為後續評估點，實際可用頻率依ASIC STA決定 |
| 實作層次 | **SoC核心 → 整晶片外殼** | 核心GDS是中間產物；整晶片仍需pad ring、電源／地與測試整合 |

PDK、HD庫與管理方式依 [LibreLane PDK文件](https://librelane.readthedocs.io/en/stable/usage/about_pdks.html)；Classic／Chip分工依 [內建流程文件](https://librelane.readthedocs.io/en/stable/reference/flows.html)；Slang選項見 [合成設定文件](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html)。WSL2／Nix路線見 [Windows安裝文件](https://librelane.readthedocs.io/en/latest/installation/nix_installation/installation_win.html)。

## 2．記憶體與運算硬體

維持 **16 KiB指令記憶體＋16 KiB資料RAM＋4 KiB scratchpad**，CPU可見容量與地址配置不變。

| 項目 | 選型決定 | 實作規則 |
| --- | --- | --- |
| SRAM候選 | **VLSIDA／OpenRAM：`sky130_sram_2kbyte_1rw1r_32x512_8`** | 每顆512×32-bit＝2 KiB；先做整合驗證，符合交付要求後才能定為正式巨集 |
| 指令記憶體 | **16 KiB SRAM，8個bank** | `0x00000000～0x00003FFF`；載入模式可寫，CPU執行時唯讀；Reset PC＝0 |
| 資料記憶體 | **16 KiB SRAM，8個bank** | `0x10000000～0x10003FFF`；保留CPU／DMA／加速器仲裁與buffer所有權規則 |
| Scratchpad | **4 KiB SRAM，2個bank** | `0x10010000～0x10010FFF`；保留byte／halfword／word存取 |
| SRAM總量 | **36 KiB，共18顆2 KiB巨集** | 一次啟用所需bank；請求接受時保存bank選擇，直到回應完成 |
| SRAM埠／mask | **使用Port 0讀寫、4個byte mask** | 支援SB／SH／SW；關閉不用的Port 1片選，其他輸入接合法值 |
| 記憶體wrapper | **保留req／rsp握手，允許等待** | 配合候選巨集上升緣取樣、下降緣讀出的時序；資料有效後才回應 |
| Register File | **標準元件正反器＋讀取MUX** | 維持32×32、兩讀一寫、x0固定0、同步reset；不硬套主記憶體SRAM |
| CPU／自訂指令 | **沿用多周期核心與12條XFaultVDSP指令** | 保留指令語意、signed、飽和、量化與溢位規則 |
| 乘法／獨立加速器 | **RTL乘法映射到標準元件邏輯** | 保留原定運算結構；ASIC組態移除FPGA專用`use_dsp`及不必要的`keep_hierarchy`；面積與頻率重新量測 |

巨集來源見 [候選目錄](https://github.com/VLSIDA/sky130_sram_macros/tree/main/sky130_sram_2kbyte_1rw1r_32x512_8)、[功能模型](https://raw.githubusercontent.com/VLSIDA/sky130_sram_macros/main/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8.v)與 [TT Liberty](https://raw.githubusercontent.com/VLSIDA/sky130_sram_macros/main/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib)。

**這顆巨集目前查到的目錄只列TT 1.8 V／25°C Liberty。**SS／FF等要求的角落資料須補齊，或換用有完整資料的巨集；不得把TT庫當成其他PVT角落。功能模型中的固定delay也不能替代Liberty時序分析。

候選 [LEF](https://raw.githubusercontent.com/VLSIDA/sky130_sram_macros/main/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8.lef)列出每顆尺寸683.1×416.54 µm。18顆巨集合計約 **5.12 mm²**，尚未包含邏輯、繞線通道、halo、PDN與pad ring；不能把它直接當作晶片總面積。

## 3．啟動、晶片介面與交付要求

| 項目 | 選型決定 | 必須滿足的條件 |
| --- | --- | --- |
| ASIC Top | **獨立ASIC wrapper** | 整合SoC、SRAM、載入控制、reset與測試；不包含Z2的PS7／AXI控制平台 |
| 程式載入 | **硬體UART RX載入控制器** | CPU保持reset時寫入指令SRAM；確認長度、地址及CRC後才允許執行，不依賴預先存在的boot code |
| UART | **115200 baud、8N1；RX載入、TX回報** | 明確區分載入／執行模式；依ASIC clock重設除頻 |
| 上電／reset | **外部reset，內部同步釋放** | CPU內部仍採高有效同步reset；移除靠宣告初值／initial建立控制狀態的假設；SRAM不因reset清零 |
| RAM初始化 | **由載入器／啟動程式明確完成** | 不假設SRAM上電為0；準備所需輸入與未使用指令區；`$readmemh`只用於模擬／FPGA路線 |
| 晶片I/O | **`sky130_fd_io`作為pad庫候選** | 核心1.8 V、外部I/O初步採3.3 V方向；具體pad模式、電源與平台規則需驗證；核心金屬pin不等同封裝pad |
| 測試存取 | **保留UART讀回、記憶體測試與邏輯測試控制** | scan／ATPG及SRAM測試方案在整晶片floorplan前確定；UART自檢不等同製造測試覆蓋率 |
| 合成前檢查 | **SV解析、功能回歸、元件映射與結構檢查** | 無未處理的FPGA primitive、latch、浮接或非預期巨大FF記憶體；SRAM數量、容量與mask正確 |
| SRAM資料驗收 | **Verilog、LEF、GDS、LVS用SPICE、所需corner的Liberty** | 名稱、埠、尺寸、電源與讀寫語意一致，並符合PDK及交付規則；不能只用無時序black box |
| STA驗收 | **先TT整合，再做要求的完整PVT／RC組合** | Setup／Hold、slew、capacitance與例外路徑完整；缺角落資料時不能宣稱多角落簽核完成 |
| 實體驗收 | **DRC、LVS、Antenna、連接、寄生與適用電源檢查** | 包含SRAM、pad、PDN及實體輔助元件；豁免須有交付規則接受的依據 |
| 交付身分 | **固定版本與檔案雜湊** | 交付GDS、網表、LEF、約束、寄生與報告；能追溯工具、PDK、各元件庫、RTL及設定 |

I/O候選來源見 [SkyWater I/O庫](https://skywater-pdk.readthedocs.io/en/main/contents/libraries/sky130_fd_io/README.html)；巨集各種view與時序資料的用途見 [LibreLane Macro文件](https://librelane.readthedocs.io/en/stable/usage/using_macros.html)。載入器、ASIC wrapper、SRAM接法與測試介面是選定的實作要求，尚未因本文件而完成RTL或驗證。

**專案不實際送廠。**SkyWater官方仍將開放PDK標為experimental preview／alpha。這套選型用於研究與原型實作；要宣稱符合可下片交付，仍須對應具體平台接受的PDK、巨集、I/O與驗收規則。產出GDS本身不構成該結論。[PDK官方狀態](https://skywater-pdk.readthedocs.io/en/main/status.html)
