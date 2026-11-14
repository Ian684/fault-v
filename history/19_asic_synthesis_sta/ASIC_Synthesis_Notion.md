# Fault-V ASIC 核心與合成設計

## 1．整體架構

CPU 延續 32-bit、多周期、單指令依序執行的設計，保留 RV32I 指令功能、12 條 XFaultVDSP 指令、獨立 DOT4 加速器、DMA、UART 與 GPIO。ASIC 版改用標準元件與實體 SRAM macro，並增加不依賴 FPGA 記憶體初始化的 UART 開機載入器。

```text
外部 clk／reset_n
       │
       ├── Reset 同步釋放 ────────────────┐
       │                                │
UART RX → 同步器 → UART 接收器 → 開機載入器
                                  │ CRC 檢查、尾端補零
                                  ├── boot write → 指令 SRAM
                                  └── running → 釋放 CPU reset
                                                      │
      CPU ── 自訂執行單元                               │
       │                                              │
       ├── 指令介面 ───────────────────────→ 指令 SRAM
       │
       └── 資料介面 ─┐
DMA ────────────────┼── Round-robin 仲裁器 ──→ 資料 SRAM／Scratchpad
DOT4 加速器 ────────┘
       │
       └── MMIO：狀態、UART TX、GPIO、DMA／加速器控制
```

| 項目 | 設計 |
| --- | --- |
| ASIC 頂層 | `fault_v_asic_top`，目前為核心整合邊界 |
| 核心 | 32-bit、多周期、FSM 控制，無 Pipeline／Cache／MMU |
| 自訂指令 | DOT4、MUL16、ADDSAT、QNT8、DOT4ACC、MAC16、ADD8SAT、SUB8SAT、RQNT8、DOT2SAT、DOT8、DOT4SU |
| 獨立運算引擎 | 三階段 DOT4 加速器；與 CPU 自訂指令執行單元分開 |
| DMA | 以 word 為單位搬移資料，保留描述子檢查與範圍鎖定 |
| 共用記憶體 | CPU／DMA／加速器三個 master，最多一筆共用記憶體交易 |
| Register File | 32×32-bit，兩讀一寫，x0 固定零；映射為標準元件 |
| 乘法器 | 通用 RTL 映射為標準元件邏輯；ASIC 沒有 FPGA DSP48 |
| 開機方式 | 外部 UART RX 傳入程式，驗證後從 PC＝0 執行 |
| 頂層輸出 | UART TX、4-bit GPIO、running、boot_error、debug_status、fault_pc、fault_addr |
| 晶片周邊邊界 | Pad ring、ESD、封裝、供電與測試存取，需於晶片整合時另行設計 |

## 2．製程、工具與時脈

| 項目 | 選定方式 |
| --- | --- |
| PDK | SKY130A，版本固定於工具與來源清單 |
| 標準元件庫 | `sky130_fd_sc_hd` |
| 核心電壓 | 1.8 V；外部 I/O 電壓由實際 pad／電路板整合決定 |
| 流程 | LibreLane，Yosys＋Slang 合成；STA 使用固定 commit 的官方 OpenSTA 3.1.0，保留 LibreLane 原分析腳本 |
| 執行環境 | WSL2 Ubuntu 22.04＋官方 Docker image，固定 image digest |
| 合成策略 | `AREA 0`，階層展平，保留 SRAM 硬巨集；啟用 ABC 緩衝 |
| 外部時脈 | 單一 25 MHz，週期 40 ns；不加入 PLL |
| 起始分析角落 | TT、1.8 V、25°C，標準元件與 SRAM 使用相符角落 |
| Reset | 外部 `reset_n` 低有效；3 級暫存器非同步置位、同步釋放 |
| CPU reset | 系統 reset 或 `running=0` 時保持有效 |
| GPIO 輸入 | 兩級暫存器同步至核心時脈 |
| UART RX | 接收器內含兩級同步與位元中心取樣 |

25 MHz 是起始設計目標。實際可用頻率需在實體設計、時脈樹與寄生參數分析後確認，不由合成前的理想時脈結果推定。

## 3．SRAM 與位址配置

使用 `sky130_sram_2kbyte_1rw1r_32x512_8`：每顆 512×32-bit＝2 KiB，支援 4 個 byte write mask。共 18 顆，總容量 36 KiB。

| 區域 | 位址 | 容量 | SRAM 數量 | 用途 |
| --- | --- | --- | --- | --- |
| 指令記憶體 | `0x00000000～0x00003FFF` | 16 KiB | 8 | UART 載入後供 CPU 取指；CPU 不可寫入 |
| 資料記憶體 | `0x10000000～0x10003FFF` | 16 KiB | 8 | CPU／DMA／加速器資料 |
| Scratchpad | `0x10010000～0x10010FFF` | 4 KiB | 2 | 運算與搬移暫存區 |
| 程式狀態 | `0x20000000` | MMIO | — | 0 未完成、1 成功，其他非零為失敗碼 |
| UART | `0x20000100` 起 | MMIO | — | CPU UART TX 控制 |
| GPIO | `0x20000200` 起 | MMIO | — | 數位輸入／輸出 |
| DMA | `0x20000300` 起 | MMIO | — | 搬移描述子、啟動及狀態 |
| DOT4 加速器 | `0x20000400` 起 | MMIO | — | 運算描述子、啟動及狀態 |

| SRAM 介面項目 | 規則 |
| --- | --- |
| 使用埠 | Port 0 讀寫；Port 1 關閉，不作為第二條 CPU 通道 |
| Bank 選擇 | word index 高位選 bank，低 9-bit 選 bank 內 word |
| Byte write mask | 4-bit，每一位控制對應 8-bit byte 的寫入 |
| 讀取時序 | 上升緣擷取請求，下降緣後產生讀取結果，下一個上升緣存入 wrapper 的回應暫存器 |
| CPU 請求／回應 | req_valid／req_ready、rsp_valid／rsp_ready；等待期間保留資料與錯誤狀態 |
| Boot 寫入 | 獨立 boot 介面，在 CPU 保持 reset 時寫入 SRAM |
| Reset 行為 | 重置交易與控制狀態；SRAM 內容不因 reset 自動清除 |
| 資料初始化 | 軟體先寫入 DMEM／Scratchpad，再讀取使用 |
| 指令初始化 | 由開機載入器寫入程式，CRC 正確後將未使用尾端補零 |
| FPGA 特性移除 | ASIC 記憶體不依賴 `initial`／`$readmemh` 或 BRAM 初值 |

SRAM wrapper 不把模型的固定模擬延遲當作實際晶片延遲。靜態時序使用 Liberty；功能模擬使用上游 SRAM 行為模型。

## 4．UART 開機協定

UART 設定為 8N1。25 MHz 時每個 bit 使用 217 個 clock，接近 115200 baud。載入器接收程式期間 CPU 保持 reset；載入器與 SRAM 寫入路徑繼續運作。

| 封包順序 | 大小 | 內容 |
| --- | --- | --- |
| Magic／版本 | 4 bytes | `46 56 01 00`：FV、版本 1、保留欄位 0 |
| 程式長度 | 2 bytes | Little-endian word 數量，範圍 1～4096 |
| 程式內容 | N×4 bytes | 每個 32-bit 指令以 little-endian 傳送，從位址 0 依序寫入 |
| CRC | 4 bytes | 程式內容的 CRC-32，以 little-endian 傳送 |

| CRC 參數 | 定義 |
| --- | --- |
| 類型 | CRC-32/ISO-HDLC |
| 反射多項式 | `0xEDB88320` |
| 初始值 | `0xFFFFFFFF` |
| 最後 XOR | `0xFFFFFFFF` |
| 計算範圍 | 只有 payload，不含 magic、長度與 CRC 自身 |
| 軟體對應 | Python `zlib.crc32(payload)` |

| 狀況 | 硬體處理 |
| --- | --- |
| 正常接收 | 每收到完整 4 bytes 就寫入一個指令 word |
| CRC 正確 | 將第 N～4095 個指令 word 補零；完成後 `running=1`，釋放 CPU reset |
| 滿容量程式 | N＝4096，CRC 正確後直接釋放 CPU reset |
| 長度為 0 或超過 4096 | 拒絕封包、設定 `boot_error`，CPU 不啟動 |
| CRC 錯誤／UART framing error | 放棄這次接收、設定 `boot_error`，CPU 不啟動 |
| 接收逾時 | 預設連續 25,000,000 clocks 未收到下一個 byte，放棄封包；同步等待與補零不計入此逾時 |
| 錯誤優先序 | Reset 優先，其次 framing error／逾時；錯誤即使與補零完成同拍，running 仍保持 0 |
| 失敗後重送 | 可從新的 FV header 開始接收；舊的部分寫入不回滾，下一個合法映像重新覆寫並補零 |
| 執行期間 | 不接受新程式；重新載入需外部 reset |
| 補零期間 | 不接受新的封包；補零完成後才允許 CPU 執行 |

CRC 用來偵測傳輸錯誤，不提供程式身分驗證或 secure boot。UART RX 目前供載入器使用，CPU MMIO UART 仍以 TX 為主。

## 5．合成與靜態時序約束

| 項目 | 約束／處理 |
| --- | --- |
| 核心 clock | 40 ns |
| Clock uncertainty | 0.25 ns |
| 起始 clock transition | 0.15 ns；實際 CTS 必須另外滿足 SRAM 與元件庫限制 |
| UART／GPIO 輸入延遲 | max 4.0 ns、min 0.5 ns |
| 輸入 transition | 0.2 ns |
| 輸出延遲 | max 4.0 ns、min 0.5 ns |
| 輸出負載 | 0.03 pF |
| 非同步 reset | 外部 reset_n 設為 false path；完整 reset／CDC 簽核於後續整合處理 |
| 合成最佳化目標 | fanout 設定 10、ABC transition 目標 0.03 ns；不是自訂 SDC 的硬性 fanout／transition 限制 |
| 電氣限制 | 依實際 Liberty 檢查 max slew／cap；SRAM 地址／寫入遮罩輸入的 0.04 ns 限制保留 |
| 直接連線緩衝 | 使用標準元件 buf_8 |
| SRAM 時序 | 必須包含 falling-edge launch 到 rising-edge capture 的半週期路徑 |
| 分析終點 | 合成後、尚未放置的 pre-PnR STA |
| 面積計算 | 標準元件面積與 SRAM macro 面積分開列出 |

目前沒有實際 clock tree、放置繞線寄生參數或完整多角落 SRAM 時序模型。Pre-PnR 分析用來找出需要處理的路徑與負載，不能替代實體設計後的簽核。

## 6．RTL 移植原則

| 部分 | 做法 |
| --- | --- |
| CPU 指令語意 | 延續既有實作；不因 ASIC 移植改變軟體結果 |
| FPGA 專用提示 | 移除 DSP／階層映射提示，讓 ASIC 工具依標準元件庫映射 |
| 記憶體 | 以 SRAM bank wrapper 取代 FPGA 初值記憶體 |
| SRAM bank selector | 寬度明確限制為 bank 數所需位元 |
| 仲裁器組合程序 | 請求選擇與回應控制分開，避免工具產生程序層級的假循環依賴 |
| 寬度 | MMIO 比較常數、UART 計數比較與 debug concat 明確定寬 |
| 開機安全條件 | CRC 與 SRAM 尾端補零都完成，才讓 CPU 開始取指 |
| 可重現性 | 固定工具 image、PDK 與 macro 版本；保留 RTL、SDC、設定與網表雜湊 |

## 7．SRAM 輸入驅動與交付網表

| 部分 | 設計方式 |
| --- | --- |
| 地址輸入 | 每顆 SRAM 的 addr0[8:0] 各用 buf_4→buf_16 驅動 |
| 寫入遮罩 | 每顆 SRAM 的 wmask0[3:0] 各用 buf_4→buf_16 驅動 |
| 數量 | 18×(9＋4)＝234 組，合計 468 個正相 buffer |
| 其他過載驅動器 | 依負載與 Liberty 選擇較大驅動能力的同功能 buffer |
| 時序性質 | 純組合緩衝，不新增 clock、暫存器或指令 cycle |
| 實作位置 | 合成後的網表 ECO；由 scripts/repair_sram_inputs.tcl 重現 |
| 行為保持條件 | 保留所有非 buffer 接點連通關係與 FF／SRAM；buffer 的 A→X 為正相直通 |
| 分析版本 | OpenSTA 3.1.0；固定來源 commit，正確處理不同 Liberty 的 transition threshold |
| 交付網表 | mapped_top.v，包含緩衝 ECO；原始 Yosys 網表另外保留為 eco/base_mapped.v |
| 流程 | RTL 合成→ECO→連接核對→輸出網表→重新讀入 STA→功能模擬→交付 |

標準元件庫與 SRAM 的 slew 量測門檻不同，分析工具必須在同一網路的不同負載間正確轉換，不能把數值轉換問題誤認為實際硬體延遲。也不能靠修改 SRAM Liberty 或豁免路徑來消除驅動問題。

RTL 或合成版本改動後，需要重新合成、定位驅動器、施加 ECO 與檢查。進入實體設計時應使用包含 ECO 的網表；placement／routing 後仍可依實際寄生負載重新調整緩衝。

## 8．實體設計的銜接條件

後續需安排 18 顆 SRAM 的位置與電源連接、標準元件放置、負載與 slew 修復、CTS、routing、寄生參數擷取及重新分析。也需完成可用 SRAM 的角落資格確認、I/O／電源／啟動腳位與 DFT 方案。

只有在指定製程、macro、實體設計與交付規則均滿足要求後，才能判定是否具備下片交付條件。

官方參考：[LibreLane Docker 安裝](https://librelane.readthedocs.io/en/stable/installation/docker_installation/index.html)、[Macro 整合](https://librelane.readthedocs.io/en/stable/usage/using_macros.html)、[SRAM 來源](https://github.com/VLSIDA/sky130_sram_macros)、[OpenSTA](https://github.com/The-OpenROAD-Project/OpenSTA)、[SKY130 PDK 狀態](https://skywater-pdk.readthedocs.io/en/main/status.html)。
