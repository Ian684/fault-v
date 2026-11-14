# Reset／CDC 與 DFT 審查結論

本輪採使用者確認範圍：完成核心檢查；DFT、pad、ESD 完成審查與需求。未插入 scan／MBIST，未改 RTL 或既有核心接線。修復後 ODB 與原網表的身分對照見 `../week25_front/reports/fill_identity.json`；同一份網表用於本輪時序與數位回歸。

## Reset 與非同步入口

2,925 顆 FF 與 18 個 SRAM 共 2,961 個 clock pin 均屬主時鐘。外部 reset_n 僅經 input3 buffer 接到 `_54687_`、`_54688_`、`_54689_` 的 SET_B。UART RX 和兩個 GPIO 各只接其第一級取樣 FF，第一級只送對應第二級，未發現繞過同步器的資料入口。這些結果沿用已凍結的原生圖形稽核，filler 修復另已逐一證明原 instance、master、位置、方向、ITerm 接線不變。

新增 `constraints_reviewed.sdc` 把原本由 reset_n 出發的全面 false path 縮到三個 SET_B；另逐一列出 UART／GPIO 至第一級 D 的非同步例外，並以 endpoint 數量 assert 防止套錯網表。第一級至後級沒有 false path，仍檢查 setup／hold。完整時序結果另見主報告；nom／min／max 是 RC 變動，三者全部使用 TT 25°C／1.8V，不能當作 SS／FF。

數位回歸通過 97 cycles、8 種 reset 解除相位；每次低脈波至少 117ns。檢查非同步置位、三階解除、GPIO／UART 兩階取樣順序。採四態 FUNCTIONAL standard-cell 和行為 SRAM，沒有 SDF、類比亞穩態或電源變動。原先 81-cycle 測試也保留在預檢目錄。

外部整合需求定為：供電與主時鐘穩定時 reset_n 持續有效至少兩個完整 40ns 週期；短脈波不是支援介面。GPIO 是兩個獨立穩態輸入，改變後應保持到兩級可觀察；不能據此保證多位原子傳輸或任意短事件。多位資料／事件須另做握手。這是介面需求；97-cycle 測試驗證其部分合法相位，沒有宣稱所有類比波形皆已窮舉。

TT `dfstp_2/SET_B` Liberty 含 recovery、removal、min_pulse_width，最小脈寬表在其 0.01～1.5ns transition 範圍內最大為 2.5ns；完整原文保存於 `reports/review_inventory.json`。外部脈寬要求有餘裕，但 leaf pin 的實際 reset 波形、多 PVT 與電源上升仍未簽核。原先固定 clock phase 0 的診斷 removal 約 −2.693ns，僅表示該假設不滿足非同步控制時序，不能當作任意相位的量產通過證據。

例外是同步器的設計假設，並非 recovery／removal 或 MTBF 已通過。缺少同步器 tau／T0、輸入變動率與可靠度目標；不計算虛構 MTBF。RTL 缺 ASYNC_REG／保存標記，現版的鏈結構與階間路徑已明確稽核；後續重新綜合須加入保存與圖形檢查，重新確認位置、解析時間及 reset mux 邏輯。尚無獨立商用 CDC／RDC 簽核。

## DFT 完成的審查與實作需求

實際 FF：2,890 顆 dfxtp_2、32 顆 dfxtp_4、3 顆 dfstp_2；實際 scan FF 為 0。已核對同一份 TT library 具有 sdfxtp_2／4 與 sdfstp_2 等候選，完整 19 種 scan cell 與 pin 清單列於 `reports/review_inventory.json`。存在候選不等於已驗證 mapping、替換等價或 chain stitching。

| 項目 | 已完成審查／定義的需求 | 後續實作驗收 |
| --- | --- | --- |
| Scan | 預留 scan_in、scan_out、scan_enable、test_mode；先共用外部 clk；normal mode 的 test_mode 必須確定為 0 | 替換等價、chain connectivity、shift／capture SDC、ATPG 與 fault simulation；coverage 由實際結果填寫 |
| SRAM MBIST | 18 banks、36KiB、1RW1R；現版只用 port0，port1 csb1=1；覆蓋 address、data、四個 byte mask、bank selection | March 演算法與故障模型先定義；驗證 read latency、byte write 與 fail injection；未使用 port 依 IP 規範處理 |
| 觀察能力 | 必須記錄 fail bank／address／expected／actual、pass／fail、timeout | 經測試端點或 UART 可讀，不能只靠原 loader 推定 MBIST coverage |
| 模式隔離 | Functional／scan shift／capture／MBIST 的 clock、reset、SRAM control 分別約束 | 正常上電、模式切換及非法組合有確定行為，避免 scan 時破壞 SRAM |

本輪交付為已完成的 DFT 審查與需求。沒有製造故障 coverage 百分比、JTAG、scan chain 或 MBIST 硬體；這些實作若啟動，會改網表，必須重新實作和驗證。
