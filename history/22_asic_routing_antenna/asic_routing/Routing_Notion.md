# ASIC 金屬繞線與寄生參數

CPU 的 RTL 決定電路功能；Placement 決定元件位置；Routing 則把電路中的連接變成實際金屬導線與 vias。繞線同時要避開 SRAM、電源網路及其他線路，並符合金屬寬度、間距與接點規則。

## 1．繞線架構

| 項目 | 設計 |
| --- | --- |
| 製程／元件庫 | SKY130A／`sky130_fd_sc_hd` |
| 實體骨架 | 保留 Placement／CTS 的核心骨架、18 顆 SRAM、電源網路與外部 signal pins |
| 金屬範圍 | 訊號與 clock 使用 met1～met5；標準元件的 li1 接腳透過合法接點接入 |
| 優先方向 | met1／met3／met5 以水平為主，met2／met4 以垂直為主 |
| Global Routing | 以粗略網格分配走線通道與金屬層，產生 routing guides |
| 容量設定 | Global Routing 使用完整可用容量，不額外預留百分比；實際導線仍須符合詳細繞線規則 |
| Clock 走線規則 | 沿用非反相 CTS 結構；主幹的全域導引範圍為 met4～met5，pin 接入依實際金屬層與合法 vias 完成；長分支可用非反相 buffer 分段 |
| Global RC 修整 | 依導線負載調整一般邏輯的驅動能力與分支，完成電氣／hold 修整後再進入詳細繞線 |
| 接腳存取（Pin Access） | 依 pin 的實際金屬形狀、tracks、vias 與周圍障礙，建立符合規則的接入點 |
| 實體 ECO | 必要時在合法 row／site 挪動一般邏輯元件；保留 SRAM、電源與外部 pins，更新相關 guides、走線及 RC |
| Detailed Routing | 依 guides 建立實際導線與 vias，修正 shorts、spacing 等 routing DRC |
| SRAM 障礙 | SRAM 內部既有金屬視為 obstruction；不能為了繞通而刪除障礙或修改原始 macro LEF |
| 邊角通道 | 依實際金屬與via間距安排通道；必要時共同重繞相鄰網路，保留所有原始技術與macro障礙 |
| 電源 | 保留 VPWR／VGND 的 rings、straps、rails 與 macro 供電連接 |
| CPU 功能 | 保留原本的 ISA、FSM、暫存器與記憶體語意；繞線本身不增加指令 cycle |

## 2．必須保留的電氣條件

| 項目 | 設計 |
| --- | --- |
| Clock | `core_clk`，40 ns／25 MHz |
| Clock tree | 使用 CTS 與局部修整後的實際網路，分析時採 propagated clocks |
| 時脈接點 | 2925 個 FF CLK，加上 18 顆 SRAM 各自的 clk0／clk1 |
| SRAM 局部輸入鏈 | `BUF_4 → INV_16 → INV_16`，兩次反相保持資料極性 |
| 受限 SRAM 輸入 | `addr0` 與 `wmask0`，保留 Liberty 的 40 ps transition 上限 |
| SRAM 讀出隔離 | `dout0` 經局部 BUF_4，再接到較長的讀出網路 |
| 局部修整保護 | 保留 SRAM 附近的固定驅動器及對應網路，避免一般 resizer 拆散局部鏈 |
| 前置 Global RC 修整 | 以 500 µm 作為長導線修整門檻、允許插入 buffer，並採 30% slew／capacitance 修整裕量 |
| 前置 Hold 修整 | 以 0.3 ns 正裕量為規劃目標；繞線後再依實際 clock skew 與導線延遲補償，須符合原始 SDC |
| 驅動尺寸選擇 | 保留原有邏輯功能，依負載選足夠的驅動尺寸並重新合法化；元件已達最大尺寸時，可用非反相 buffer 隔離負載，再確認實際走線後的電氣條件 |
| 繞線後修整 | 依實際 SPEF 找出違規 net，使用功能相同的驅動尺寸、長線分段 buffer 或非反相 hold 延遲元件；重新合法化、更新受影響走線並萃取 RC |
| 修整原則 | 繞線後若電容或延遲超出限制，須修整、重新繞線並重新驗證，不能沿用放置階段的通過結果 |

## 3．RC 與交接資料

| 項目 | 用途 |
| --- | --- |
| OpenDB | 保存元件、接腳、金屬與 vias，是後續實體流程的完整工作資料 |
| DEF | 交換放置、電源與走線資訊 |
| 功能／供電網表 | 描述最終電路連接，供時序、連接比對及 LVS 等流程使用 |
| SDC | 定義時脈、I/O delay、負載與既定例外 |
| SPEF | 保存導線的寄生電阻與電容，提供繞線後時序分析 |
| RC extraction | 依實際金屬與指定製程規則萃取；與 placement-estimated RC 分開記錄 |
| RC corners | nominal／min／max 導線 RC 模型可分別萃取；不代表已完成三種 PVT 時序簽核 |
| Timing corner | 目前 SRAM 模型涵蓋 TT／1.8 V／25°C；完整製程角落需補相應模型 |
| 後續簽核 | 完整 DRC、LVS、antenna、多角落時序、IR／EM 與晶片整合依選定交付要求處理 |

```text
Placement／CTS 的 OpenDB
          │
          ▼
    Global Routing
    分配通道與金屬層
          │
          ▼
    Detailed Routing
    建立導線與 vias
          │
          ▼
    天線檢查與保護
    補齊接腳模型並修復後重繞
          │
          ▼
      RC Extraction
    產生實際走線的 SPEF
          │
          ▼
      繞線後時序分析
          │
          ▼
    後續實體與製程簽核
```

當實際 RC 分析顯示時序或電氣超出限制，回到驅動、延遲或放置修整，更新元件接線與受影響的鄰近走線，再重新萃取與分析。完整來源快照、接線關係與幾何資料要一起保存。

Router 的 DRC 檢查範圍與製程完整簽核不同；實際金屬已產生，也仍須確認 LVS、antenna、模型完整性與其他交付條件。

天線檢查需要可追溯的 gate 與 diffusion 面積。若 SRAM 抽象檔缺少這些欄位，可由相同 GDS 與製程技術檔提取，並以原始 SPICE 的電晶體尺寸與接線交叉核對。保護二極體只增加被動負載，也會改變寄生參數；插入後必須重新檢查佈線、供電、連接、時序及電氣，不能直接沿用修復前的結果。

流程名詞與指令可對照 [OpenROAD Global Routing 文件](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html) 與 [Detailed Routing 文件](https://openroad.readthedocs.io/en/latest/main/src/drt/README.html)。
