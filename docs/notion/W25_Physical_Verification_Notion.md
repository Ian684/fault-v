# ASIC 實體驗證與投片前檢查

繞線完成後，晶片已經有實際的金屬和 vias，但還要逐項確認：
- 版圖符合製程規則；
- 版圖和電路網表一致；
- 實際走線下的時序與電氣仍然正確；
- 供電足夠可靠。

另外還要對測試（DFT）、腳位與靜電防護（pad／ESD）提出需求。所有檢查都在同一個最終版本上完成，不拿不同試跑的通過結果拼成最終結論。

## 1．驗證架構

| 檢查 | 目的 | 做法 |
| --- | --- | --- |
| 繞線 DRC | 確認 router 產生的金屬沒有 short／spacing 問題 | 原生 router 檢查；全晶片與完整鄰域重查 |
| 版圖 DRC | 確認完整 GDS 符合製程幾何規則 | KLayout 開源 deck：FEOL、BEOL、offgrid、floating metal；SRAM 不排除 |
| LVS | 確認版圖連接和網表一致 | Magic 從 GDS 抽取電路，Netgen 比對；18 顆 SRAM 以 125-pin 介面 blackbox 參與比對 |
| Antenna | 防止製造時長導線累積電荷打壞 gate | 上層金屬 antenna 檢查；SRAM 接腳使用由 GDS 補齊的 gate／diffusion 面積 |
| 連通與供電幾何 | 確認每條網路真的連通，電源和地沒有碰在一起 | 41,337 條多端訊號／時脈網路的幾何連通檢查；VPWR／VGND 的面、邊、點接觸檢查 |
| STA | 確認實際走線下的時序與電氣 | OpenSTA；從最終版圖重新萃取 nom／min／max 三種 RC；TT 25°C／1.8V；propagated clock |
| Reset／CDC | 確認重置和非同步輸入的處理正確 | 約束審查加四態數位模擬 |
| 切換活動 | 為功耗與 IR 提供真實活動 | 在最終網表上執行 4 個工作負載並產生 VCD，對應到每條 routed net |
| Fill／密度 | 符合製程的金屬密度要求 | 從最終 GDS 重新產生 dummy fill，用滑動視窗檢查各層密度 |
| IR／EM | 確認供電壓降與平均電流密度 | 靜態 IR 使用實際活動；平均 EM 和 techLEF 的電流限制比較 |
| DFT／pad／ESD | 為後續投片定義需求 | 審查並列出需求，這一階段不插入硬體 |

```text
最終繞線 OpenDB
      │
      ├── 繞線 DRC、網路連通 ──────────────┐
      ▼                                    │
加入 standard-cell filler                   │
      │                                    │
      ▼                                    │
完整 GDS ── KLayout DRC、antenna             │
      │     核心 LVS（含正／負對照）           │
      │     SRAM／元件／via 幾何核對          │
      ▼                                    │
重新萃取三種 RC ── STA                       │
      │                                    │
      ├── 功能／reset／CDC 模擬 → 切換活動 ──┤
      ▼                                    ▼
靜態 IR／平均 EM                    同一版本的結論
      │
      ▼
dummy metal fill ── 密度與 fill 後規則互動
```

## 2．驗證原則

| 原則 | 做法 |
| --- | --- |
| 同一版本 | 所有檢查使用同一個最終網表、版圖和 SPEF；任何改動都要重新跑受影響的檢查 |
| 改動後重新萃取 | 版圖或元件一改，就重新萃取 RC 再做 STA，不沿用修改前的寄生參數 |
| 正／負對照 | LVS 正常版本必須 0 error；刻意把一顆 SRAM 的 pin 移開，必須被抓到（44 個 error）。密度檢查也有已知會失敗的負對照 |
| 不把空結果當通過 | 只有抽象 SRAM 的 GDS、工具內部未初始化的計數、只看 exit code，都不能當作通過 |
| 專用版圖分開 | LVS 專用的介面版圖不能拿去做製造、DRC、密度或 RC 萃取 |
| 不修改公開 PDK | 違規只能改設計來修，不能改規則或 macro LEF 讓它消失 |

## 3．修復設計

| 問題 | 修復方式 | 設計重點 |
| --- | --- | --- |
| 最大 RC 下的 slew／cap 超限 | 替換 51 個 driver，每個都核對過布林等價 | 只改驅動能力，不改邏輯；改完重新萃取 RC |
| LI1 支線自身間距 | 五條支線改在接腳內用 LI1，再經 M1／M2 接出；四顆新增二極體搬到合法 row | 保留原接線關係，只改局部幾何 |
| 上層 antenna | 新增 20 顆被動二極體，加上兩段經驗證的局部金屬橋 | 二極體會增加負載，插入後重查時序與電氣 |
| 電源 via 平均電流 | 181 個單切孔 via4 換成多切孔陣列（共 1,430 個 cut），另加一組三切孔的 M1–M3 row feed；重驗幾何、LVS 與 IR／EM | 單一切孔的平均電流超過 techLEF 限制，改用多個切孔分攤電流；陣列大小要避開 M5 間距違規 |
| Well／body 連續性 | 補滿 standard-cell filler | 只補空位；原元件位置、接線和電源幾何都不變 |
| 金屬密度 | 從最終核心 GDS 重新產生 dummy fill，修正 FOM／LI 後再檢查 | fill 不能改到原有幾何；fill 後重查互動規則 |

## 4．時序約束與 reset／CDC

| 項目 | 設計 |
| --- | --- |
| 時脈 | 單一主時脈 `core_clk`，40 ns／25 MHz；2,925 顆 FF 和 18 顆 SRAM 都在同一個時脈域 |
| Reset 例外 | 原本從 reset_n 出發的大範圍 false path，縮小到 3 個非同步置位腳（SET_B） |
| 非同步輸入 | UART RX 與兩個 GPIO 只對第一級取樣 FF 設例外，並用端點數量檢查防止套錯網表；第一級到第二級仍正常檢查時序 |
| Reset 介面需求 | 電源和時脈穩定後，reset_n 至少維持兩個完整週期（80 ns）；建議使用外部 reset supervisor |
| GPIO 介面需求 | 兩個輸入各自獨立同步；變化後要保持到兩級都能看到；多位元資料需要另外做握手 |
| 數位驗證 | 8 種 reset 解除相位、97 個週期，檢查非同步置位、三級解除與兩級取樣順序 |

同步器只是設計假設，不代表 recovery／removal 或 MTBF 已通過；缺少同步器的 tau／T0 等資料，所以沒有計算 MTBF。

## 5．最終檢查結果

| 檢查 | 結果 |
| --- | --- |
| 繞線 DRC／版圖 DRC | 0／0（加入 filler 後仍為 0） |
| 核心 LVS | 0 error；18 顆 SRAM 各有完整 125 個介面端點 |
| 上層 antenna | 違規 net 0、pin 0 |
| 網路連通 | 41,337 條網路全部連通；VPWR／VGND 無接觸 |
| STA（TT，三種 RC） | setup／hold／slew／cap 違規全部 0 |
| Reset／CDC 與工作負載 | 全部通過；4 個工作負載的 routed net 對應 100% |
| Fill／密度 | 7 個有數值門檻的層，每層 1,053 個視窗通過；fill 後的規則互動 0 |
| 靜態 IR／平均 EM | 四組情境都通過研究預算 |

| RC 條件（TT 25°C／1.8V） | Setup 最差 slack | Hold 最差 slack |
| --- | ---: | ---: |
| min | 8.431 ns | 0.197 ns |
| nom | 6.674 ns | 0.198 ns |
| max | 5.693 ns | 0.152 ns |

| SRAM 功耗假設（每顆） | VPWR 最大壓降 | VGND 最大抬升 | 合併 | 最大平均 EM 使用率 |
| --- | ---: | ---: | ---: | ---: |
| 14 mW | 15.7 mV | 14.5 mV | 30.2 mV | 47% |
| 28 mW | 29.7 mV | 27.3 mV | 57.0 mV | 88% |

- IR 研究預算是 1.8 V 的 5%（90 mV），是本專案自訂的篩檢門檻，不是 foundry 限值。
- 供電假設為核心外緣的理想電源，沒有封裝與 bond wire 的阻抗。
- 14 mW 約等於 SRAM 模型的動態功耗，28 mW 是兩倍的保守情境。

## 6．DFT 與 pad／ESD 需求

| 項目 | 需求 |
| --- | --- |
| Scan | 預留 scan_in、scan_out、scan_enable、test_mode；正常模式下 test_mode 必須固定為 0。元件庫已有 19 種 scan FF 候選，替換後需驗證等價、chain 連接、shift／capture 約束與 ATPG |
| SRAM MBIST | 18 個 bank、36 KiB；涵蓋位址、資料、四個 byte mask 與 bank 選擇；失敗時要記錄 bank、位址、期望值與實際值，並能透過測試端點或 UART 讀出 |
| 模式隔離 | Functional／scan shift／capture／MBIST 的 clock、reset、SRAM 控制分別約束，避免 scan 時破壞 SRAM 內容 |
| 電壓與 I/O | 核心 1.8 V；I/O 候選為 3.3 V wrapped I/O（`sky130_ef_io__gpiov2_pad_wrapped`） |
| 接點預算 | 48 接點 wire-bond：clk／reset 2、UART 2、GPIO 6、狀態 2、DFT 4、電源／地 12、預留 20 |
| 腳位縮減 | 現有 108 個訊號端點中，96 個是 debug 位元；要放進 48 接點，必須改成透過 UART 讀回診斷資訊 |
| ESD | 核心與 I/O 電源分域，建立所有訊號與電源域的放電路徑；HBM 2 kV／CDM 250 V 是待核定的目標，不是額定 |
| 晶片尺寸 | I/O ring 約 211 µm 深，加入後要重新規劃 die、corner、供電與 bond pitch |

這一階段只完成審查與需求。scan chain、MBIST、pad ring 與 UART 診斷都還沒有實作；之後若要加入，會改變網表，必須重新實作與驗證。

## 7．模型與規則範圍

| 項目 | 已涵蓋 | 未涵蓋 |
| --- | --- | --- |
| 工具與規則 | 固定版本的 LibreLane、OpenROAD、OpenSTA 3.1、Magic、Netgen、KLayout 與同一份 SKY130A PDK | 開源 deck 不等於 foundry 核可的規則 |
| SRAM | 18 × 2 KiB；GDS／LEF／TT Liberty 有來源紀錄；只移除沒有接點的孤立 M2 線段並去除重複子實例，39 層幾何保持一致 | 只有 TT 模型；沒有合格的 SS／FF、內部 DRC／LVS／antenna |
| LVS | 標準元件與完整繞線；SRAM 介面 | SRAM 內部是 blackbox，沒有電晶體層級的 LVS |
| RC 萃取 | 最終版圖的三種 RC | 不支援 dummy fill 的寄生效應（fill-aware PEX） |
| PVT | TT 25°C／1.8V 下的三種 RC | 沒有 SS／FF、溫度與電壓變化 |
| IR／EM | 靜態 IR、平均 EM，使用實際活動 | 沒有動態壓降、封裝、熱、RMS／peak 電流與 SRAM 內部 |
| Reset／CDC | 數位功能與同步器之間的時序 | 沒有 SDF、類比 recovery／removal、MTBF 與獨立 CDC／RDC 簽核 |

這些檢查完成的是研究範圍的投片前驗證。SRAM 多 PVT 模型、fill-aware PEX、foundry 規則、封裝與可靠度仍是實際製造前的阻擋項，所以這一版不能直接送廠。

流程名詞可對照 [OpenROAD 文件](https://openroad.readthedocs.io/en/latest/)、[KLayout 文件](https://www.klayout.de/doc.html) 與 [SKY130 PDK 文件](https://skywater-pdk.readthedocs.io/en/main/)。
