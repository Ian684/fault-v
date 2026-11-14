# ASIC PPA：H0／H1 正式比較

H1 是 H0 的縮小晶片版本：網表、SRAM、設定和工具都與 H0 相同，只縮小 SRAM 之間的間隔，die 也因此縮小（定義見 `../h1/H1_Definition.md`）。H1 已通過與 H0 相同的整套檢查：

- 原生繞線 DRC 0、KLayout DRC 0、antenna 0
- 三種 RC 的 STA 違規全部為 0
- 核心 LVS 乾淨，反向測試能抓到錯誤
- reset／CDC 與四個工作負載的功能模擬全部通過
- 活動對應 100%
- W25 結案的同一套實體檢查：全晶片原生 DRC、網路幾何連通、SRAM／標準元件／via stream 審查、VPWR／VGND 接觸、靜態 IR／平均 EM、dummy metal fill 與密度、FOM、post-fill BEOL 互動

因此本報告是兩個已實作、驗證範圍相同的硬體版本的正式比較。兩版都還沒做的項目列在「未涵蓋的檢查」。

## 結論與取捨

| 指標 | H0 | H1 | 差異 |
| --- | ---: | ---: | ---: |
| Die 面積 | 8.250 mm² | 7.946 mm² | **−3.7%** |
| 最差 setup slack（max RC） | 5.693 ns | 11.018 ns | +5.32 ns（不能歸功於縮小，見下文） |
| 最差 hold slack（max RC） | 0.152 ns | 0.245 ns | +0.093 ns |
| 總功耗（mixed） | 33.519 mW | 33.834 mW | +0.94% |
| DOT64 rv32i ÷ custom 能量比 | 21.20× | 21.20× | 不變 |

- **面積是唯一有結構性差異的指標。** SRAM 佔 die 的 62–64%，大小不變；縮小只拿掉 SRAM 之間的通道，所以 die 只少 3.7%，但可放置標準元件的面積少了 13.1%。
- **時序兩版在 25 MHz 都有足夠餘裕**（setup 至少 5.7 ns）。H1 的 setup slack 比較大，但原因是重新擺放後最差的那段邏輯剛好比較集中，不是縮小造成的。換一次擺放，兩版都可能變動好幾 ns，所以不把這項列為 H1 的優點。
- **功耗 H1 多 0.6–0.9%（+0.20–0.32 mW）**。其中 0.20 mW 來自時脈網路：H1 重新做了 CTS，時脈 buffer 較多，主幹 buffer 也加大過。SRAM 功耗兩版相同。
- **代價在實作難度。** H1 通道變窄後，繞線違規集中在 SRAM 角落，需要好幾輪手動局部重繞。第一次完整簽核還因為漏掉 H0 的繞線前修復步驟而失敗。電源網路的平均 EM 一開始也超限（最差 5.77 倍），用 H0 的作法加大 via4 陣列後才通過；EM 餘裕仍比 H0 小（28 mW 時 0.98 對 0.88）。

整體判斷：以面積為主要指標時，H1 較好。功耗差不到 1%；兩版在 25 MHz 下的 setup 餘裕都至少有 5.7 ns，推估最高頻率都在 29 MHz 以上。差距不大，因為兩版的 PPA 都主要由 18 顆 SRAM 決定。

H1 已補完 H0 在 W25 結案時做過的實體檢查（見「W25 結案檢查」），兩版的驗證範圍相同。電源 via 修補只動電源線，修補前後的面積、時序、功耗與能量在本報告的精度下都不變。重新萃取後，40,850 條訊號網路中只有 11 條的總電容有變化，最多 +1.1%，是新電源金屬帶來的耦合電容；功耗只差 0.000001 mW。

## 比較條件

| 項目 | H0 | H1 |
| --- | --- | --- |
| 來源網表 | `design/mapped_top.v`（`88b35c08…`）經 H0 實體流程 | 同一份 `mapped_top.v`，H0 的設定重新跑實體流程 |
| 簽核網表 | `cdbbfc46…0f4175`（W25 最終候選） | `5c11b7c5…f00b8f0` |
| Die／core | 2500 × 3300 µm；core 7,337,230 µm² | 2470 × 3217 µm；core 7,047,310 µm² |
| SRAM 間隔（欄／列） | 96.9 / 103.5 µm | 89.9 / 95.5 µm |
| SDC | `week25_signoff/constraints_reviewed.sdc`（`979a8d3f…6203`） | 同一份 |
| 製程／元件庫／SRAM | SKY130A、sky130_fd_sc_hd、18 × sky130_sram_2kbyte_1rw1r_32x512_8 | 相同 |
| PVT／RC／時脈 | TT 25°C 1.8V；功耗用 nominal RC；25 MHz | 相同 |
| 工具 | OpenSTA 3.1.0、固定 LibreLane image `sha256:02d50f25…0302` | 相同 |
| 活動 | `week25_closure/functional/final_a`，4 個 VCD，各 140,455 pins 標註、0 未標註 | `cand_gap90x95/functional/h1c_a`，在 H1 網表上重跑，各 137,242 pins 標註、0 未標註 |

- 兩版四個工作負載的週期數完全相同：256／1,159／21,708／1,022。
- H1 標註的 pin 少 3,213 個，剛好對應元件數的差異：少了 2,255 顆 antenna diode、495 顆時序修復 buffer、4 顆時脈 inverter，多了 20 顆時脈 buffer。

## H1 檢查結果

| 檢查 | H1 | H0（參考） |
| --- | --- | --- |
| 原生繞線 DRC／antenna | 0／0 | 0／0 |
| KLayout DRC（sky130 core precheck deck） | 0 | 0 |
| Antenna（fill 後重查） | 0 nets／0 pins | 0／0 |
| 3-RC STA：28 項 setup／hold／slew／cap／fanout 違規計數 | 全部 0 | 全部 0 |
| 核心 LVS：8 項計數 | 全部 0 | 全部 0 |
| LVS 反向測試（故意移動 pin） | 44 個錯誤，有抓到 | 44 個錯誤 |
| Reset／CDC | 97 週期、8 個釋放相位通過 | 通過 |
| 四個工作負載 | 全部通過，DOT64 結果皆為 60256 | 全部通過 |
| 活動對應 | 100%（40,850 條 routed net） | 100% |

### W25 結案檢查

方法與 H0 的 `week25_closure` 相同，對象是加 fill 後的 H1 最終 ODB／GDS。腳本的每一處改動都記錄在 `../h1/cand_gap90x95/closure_c/reports/script_provenance.json`：

- 大部分腳本只改了路徑。
- EM 稽核有一個防止電阻網路匯出不完整的門檻：H0 設為電阻數超過 300,000。H1 的電源網路較小（約 267,000 個），所以改為 200,000。另外兩道保護不變：必須讀到 Sinks 區段，而且每一筆 EM 結果都要對到確切的電阻。
- IR 的執行設定與供電點選取是 H1 專用的（`h1_ir_cli.py`、`h1_pdn_boundary.py`）。
- 密度檢查改用讀取實際 die 的版本，見下方說明。

| 檢查 | H1 | H0（W25 結案） |
| --- | --- | --- |
| 全晶片原生 DRC（fill 後） | 0 個未解決；58 個切分邊界假警報，逐一置中重查後消失 | 0 個未解決 |
| 網路幾何連通 | 40,850 條全部連通，5,317 個 diode terminals | 41,337 條全部連通 |
| VPWR／VGND 接觸 | 無面積、邊緣或點接觸 | 無 |
| SRAM 39 層幾何 | 18 顆與選定宏完全一致 | 一致 |
| 標準元件／via stream | 171,309 顆、144 種 master、449,970 個 via 與元件庫／ODB 一致；位移負控制有抓到 | 一致 |
| 靜態 IR（合併 rail，14／28 mW 每顆 SRAM） | 30.5／57.8 mV | 30.2／57.0 mV |
| 平均 EM 最大利用率（14／28 mW） | 0.518／0.981 | 0.466／0.885 |
| Dummy fill 密度（7 個有數值門檻的層） | 每層 999 個視窗全部通過；MET5 最低 0.462（下限 0.45） | 每層 1,053 個視窗通過；MET5 最低 0.454 |
| Dummy 格點、FOM 幾何 | 8 層 5 nm grid 通過；FOM 20 tiles 通過 | 通過 |
| Post-fill BEOL 互動 | 0 標記 | 0 標記 |

- **IR／EM** 使用 H1 自己的 mixed VCD、nominal SPEF 與最終 ODB，三者的雜湊都在執行時核對過。供電點採用 H0 的規則：die 邊緣 100 µm 內既有的 met5 PG 端點。
- **密度視窗數不同**，因為 H1 die 較小（2470 × 3217 µm）。第一次執行沿用了 H0 腳本裡寫死的 2500 × 3300 µm，把 die 外的空白也算進上緣與右緣的視窗，MET5 因此有 51 個視窗低於下限。改成讀取 GDS prBoundary（與 DEF DIEAREA 交叉核對），方法和門檻不變，重跑後全部通過。錯誤範圍的那份報告保留為 `h1_sliding_density_H0die_misscoped.json`。
- **EM 餘裕比 H0 小**：28 mW 時最差是一組 via4（2.44 mA／cut，限值 2.49）。這仍是研究用平均電流篩檢，限制和 H0 相同。

總結腳本的結果是 `all_h1_checks_pass = true`，每一項都是照實讀到的數值，沒有強制改成通過。

## 面積

| 項目（µm²） | H0 | H1 | 差異 |
| --- | ---: | ---: | ---: |
| Die | 8,250,000 | 7,945,990 | −3.7% |
| Core | 7,337,230 | 7,047,310 | −4.0% |
| SRAM macro（18 顆） | 5,121,690 | 5,121,690 | 0 |
| 可放置面積（core − SRAM） | 2,215,540 | 1,925,620 | **−13.1%** |
| 標準元件（含 tap／antenna） | 451,524 | 437,062 | −3.2% |
| 　邏輯（不含 tap／antenna） | 408,166 | 404,922 | −0.8% |
| 　Tap | 24,410 | 18,834 | −22.8% |
| 　Antenna diode | 18,948（7,572 顆） | 13,305（5,317 顆） | −29.8% |
| Filler | 905,807 | 629,077 | −30.6% |
| 總利用率／標準元件利用率 | 75.96%／20.38% | 78.88%／22.70% | |

- **邏輯面積幾乎不變（−0.8%）。**
  - 兩版的組合邏輯與 FF 數量完全相同（23,055／2,925）。
  - 差在時序修復 buffer：H1 有 9,558 顆，H0 有 10,053 顆，少了 2,978 µm²。
  - 時脈 buffer／inverter：H1 是 606／170 顆，H0 是 586／174 顆，多了 496 µm²。
- **Tap 和 filler 跟可放置面積一起變小**：每一列都要放 tap，空位都要補 filler。Tap 減少的比例（−22.8%）比可放置面積（−13.1%）大，可能是通道變窄後 SRAM halo 和列端佔掉的比例變高；本輪沒有逐列核對。
- **Antenna diode 少了 2,255 顆。** diode 數量取決於繞線結果和修補方式，不是縮小的直接效果。

## 時序

| TT RC 條件 | Setup slack H0 | Setup slack H1 | Hold slack H0 | Hold slack H1 | 推估最高頻率 H0 → H1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| min | 8.431 | 13.817 | 0.197 | 0.247 | 31.7 → 38.2 MHz |
| nom | 6.674 | 12.146 | 0.198 | 0.258 | 30.0 → 35.9 MHz |
| max | 5.693 | 11.018 | 0.152 | 0.245 | **29.1 → 34.5 MHz** |

兩版三種 RC 下的 setup、hold、slew、cap、fanout 違規都是 0。最高頻率是用「40 ns − setup slack」換算的推估值，沒有在該頻率重跑 STA。SRAM 時序是解析模型，只有 TT，所以不能當作保證的工作頻率。

### Setup 差異的原因

比對兩版 nominal RC 的最差路徑（`cand_gap90x95/eco/b_crit_path_cmp.sh`，只讀不改）：

| 路徑 | 起點 → 終點 | slack | 路徑上元件 | 長線 buffer（wire*／max_length*） | 沿邏輯元件的曼哈頓長度 |
| --- | --- | ---: | ---: | --- | --- |
| H0 最差 | `_54656_` → `_54039_`（FF → FF） | 6.674 | 91 | 39 顆，共 13.75 ns | H0 擺放 9,029 µm；同一批元件在 H1 擺放 5,284 µm |
| H1 到同一終點 | `_53986_` → `_54039_` | 15.326 | 67 | 9 顆，共 2.89 ns | H1 擺放 7,173 µm |
| H1 最差 | `_53395_` → dmem bank 0 SRAM | 12.146 | 80 | 34 顆，共 12.02 ns | H1 擺放 8,609 µm；同一批元件在 H0 擺放 7,183 µm（H0 這個終點 slack 14.593） |

- **H0 的最差路徑：繞來繞去。** 這段邏輯被放在 dmem bank 0 這顆 SRAM（H0 座標 y 1,160–1,577 µm）上下兩側的通道裡（y≈1,110–1,135 µm 與 y≈1,600 µm），訊號在兩條通道間來回，光前 12 個邏輯元件就跨了 5 次。路徑上將近一半是長線 buffer。
- **同一批元件在 H1 比較集中**：前段集中在一個通道交叉口附近（約 x 730–1,120、y 580–720 µm），整條沿邏輯元件的長度從 9,029 µm 降到 5,284 µm。所以 H1 這個終點的 slack 有 15.3 ns。
- **兩版的最差路徑都被長線主導**，差別只在全域擺放把哪一段邏輯拆得比較散。SRAM 間隔只縮了 7–8 µm，不可能直接造成 5 ns 的差異。因此 setup 改善是這一次擺放的結果，不是縮小帶來的。兩版各只有一次擺放，沒有做多組 seed 比較。
- **Hold：H1 為 0.245 ns，H0 為 0.152 ns（max RC）。** 兩版的 hold 修法不同：
  - H1 用 H0 的繞線前修復流程（ResizerTimingPostGRT），並在 RC ECO 中於 28 個 SRAM din0 端點加了 34 顆 dlygate4sd3_1。
  - H0 在時脈 ECO 之後，用 3 顆 hold buffer 收斂。

## 功耗（25 MHz，TT，nominal RC）

| 工作負載 | H0 總功耗 | H1 總功耗 | 差異 | 其中 Clock | Combinational | Sequential |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 32.369 | 32.569 | +0.200（+0.62%） | +0.201 | −0.001 | +0.001 |
| mixed | 33.519 | 33.834 | +0.315（+0.94%） | +0.201 | +0.101 | +0.014 |
| dot64_rv32i | 33.280 | 33.579 | +0.299（+0.90%） | +0.201 | +0.082 | +0.016 |
| dot64_custom | 33.346 | 33.650 | +0.303（+0.91%） | +0.201 | +0.088 | +0.015 |

（單位 mW。SRAM 兩版都是 25.174 mW，每顆 1.3986 mW；漏電都是 0.319 mW。）

- **時脈 +0.20 mW（+4.8%），四種工作負載相同。**
  - 時脈不做 gating，時脈網路每個週期都在翻轉，所以多出的功耗是固定的。
  - H1 是重新做的 CTS：時脈 buffer 586 → 606 顆。
  - 後段 ECO 把兩條主幹的 buffer 從 clkbuf_8 加大為 clkbuf_16，並加了一顆 clkbuf_16 repeater。
- **組合邏輯在有運算的工作負載多 0.08–0.10 mW（約 +8%），切換功耗約 +5.5%。**
  - 原因不是總線長：H1 繞線總長 6.13 M µm，比 H0 最後一次完整繞線的 6.19 M µm 少 1.0%。
  - 差異來自個別高活動網路的擺放位置不同。本輪沒有逐條追查。
- 相對來說，H1 的邏輯功耗（不含 SRAM）多 2.8–3.8%。但邏輯只佔總功耗約 25%，對總功耗的影響不到 1%。

## 工作負載能量

| 工作負載 | 量測時窗 | H0 總能量 | H1 總能量 | 差異 | H0 邏輯能量 | H1 邏輯能量 | H1 每週期 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 10.24 µs | 331.5 nJ | 333.5 nJ | +0.62% | 73.7 nJ | 75.7 nJ | 1,302.8 pJ |
| mixed | 46.36 µs | 1,553.9 nJ | 1,568.5 nJ | +0.94% | 386.9 nJ | 401.5 nJ | 1,353.4 pJ |
| dot64_rv32i | 868.32 µs | 28,897.9 nJ | 29,157.4 nJ | +0.90% | 7,038.6 nJ | 7,298.2 nJ | 1,343.2 pJ |
| dot64_custom | 40.88 µs | 1,363.2 nJ | 1,375.6 nJ | +0.91% | 334.1 nJ | 346.5 nJ | 1,346.0 pJ |

週期數相同，所以能量差異就等於平均功耗的差異。

DOT64 指令擴充的效益在兩版幾乎一樣：

- 週期比 21.24×，能量比 H0 21.199×、H1 21.196×。
- H1 每次乘加的能量：rv32i 455.6 nJ、custom 21.5 nJ（H0 為 451.5／21.3 nJ）。

## H1 的實作過程

### 第一次完整簽核：失敗，結果僅供參考

2026-11-12 第一次簽核用的是 `h1_eco_rf6`：DRC、antenna、LVS、功能模擬都通過，**但 3-RC STA 失敗**：

| 項目 | nom | min | max |
| --- | ---: | ---: | ---: |
| Hold 最差 slack（ns） | −0.490（54 違規） | −0.342（28） | −0.586（59） |
| Max slew 違規 | 12,910 | 10,358 | 14,711 |
| Max cap 違規 | 1,161 | 913 | 1,316 |

- Hold 違規全部打進 SRAM 的 din0／csb0。
- 最差 slew 為 8.08 ns，限制是 1.5 ns。

**原因：漏掉了 H0 在繞線前做的修復。**

- H0 的繞線流程（`routing/scripts/run_all.sh`）在 global route 和 detailed route 之間跑了 RepairDesignPostGRT 和 ResizerTimingPostGRT，時序修復 buffer 從 785 增加到 8,541，再到 10,032 顆。
- H1 第一次用 Classic flow 從 GlobalRouting 開始跑，這兩步預設是關的，所以只有 746 顆 buffer。
- 另外，H1 沿用了 H0 最終設定中的 `GRT_ANTENNA_REPAIR_ITERS 0`。H0 的輸入當時已經帶著 diode，H1 沒有，於是 diode 只能在 detailed route 之後才插入，造成很長的 DRC／antenna 迴圈。

第一次的數字只當參考，不能拿來比較：

- 標準元件面積 378,334 µm²，diode 10,456 顆。
- 功耗：idle 32.615、mixed 33.758、dot64_rv32i 33.537、dot64_custom 33.599 mW。

**處理方式：重做，而不是事後補。**

- 不採用在繞線後大量 ECO 補救，因為修復方法和 H0 不同，會混淆面積與功耗的比較。
- 改成從還沒插 diode 的 global route 結果開始，照 H0 的修復配方重做，標記為 h1b。
- 唯一記錄在案的偏差：修復時用的是最終繞線的 GRT 設定（時脈走 met4／met5）。

### 第二次（h1b）收斂紀錄

| 階段 | 做法 | 結果 |
| --- | --- | --- |
| 繞線前修復 | H0 配方（RepairDesignPostGRT + ResizerTimingPostGRT） | buffer 746 → 8,089 → 9,522（H0：785 → 8,541 → 10,032）；hold +0.291 ns（H0 +0.286） |
| Detailed route | 原生 DRT | 85,286 → 4 個違規，卡在 SRAM 右上角（x≈1,576 µm 那一欄），停止 |
| 手動 DRC 修補 d1、d2 | H0 作法：d1 清掉違規網路、d2 清掉違規點周圍 8 × 8 µm 窗口內的網路，限次數重繞 | DRC 0（antenna 2,357 條） |
| STA h1b_i2 | | hold −0.501 ns、slew 1,653、cap 165（max RC），和 H0 第一次乾淨繞線時的狀況相同 |
| RC ECO rc1c | H0 規則：最小足夠驅動、留 15% 餘裕；resize 164 顆、新增 36 顆（含 34 顆 dlygate4sd3_1） | hold +0.054、slew 12、cap 1（max RC） |
| 時脈分支試驗 | 見下表 | rc4r 採用：setup／hold／slew／cap 全部乾淨 |
| 補天線 f1、x1、f2、f3、f4 | 原生 diode 修補，搭配一輪角落窗口重繞（x1） | 加 5,311 顆 diode；DRC 0、antenna 0 |
| STA h1b_i9 | | 7 條被補天線重繞的網路出現 slew 53／cap 6（max RC） |
| RC ECO rc5 | H0 規則：7 個 driver 各加大一號，時脈線限定走 met3／met4 | h1b_i10 全部乾淨 |
| 補天線 f5 | 原生修補 | 加 6 顆 diode；DRC 0、antenna 0；h1b_i11 全部乾淨 |
| 完整簽核 | `signoff/run_signoff_b.sh h1b_eco_rf5` | 全部通過（見上） |

時脈分支試驗（都從 rc1c 出發，數字為 max RC）：

| 試驗 | 做法 | Hold 最差 slack | 違規 | 結果 |
| --- | --- | ---: | --- | --- |
| rc2 | 兩顆 clkbuf_16 串接，放在 H0 用過的位置 | −0.574 | hold 100、slew 4 | 否決 |
| rc3 | 一顆 clkbuf_16，放在主幹 driver 旁 | −0.457 | hold 79、slew 4 | 否決 |
| rc3m | 一顆 clkbuf_16，放在 H0 位置 (850, 1110) | −0.257 | hold 38、slew 1 | 否決 |
| rc4 | 不加 repeater，主幹改走 met3–met5 | −0.061 | hold 7、slew 4 | 否決 |
| **rc4r** | 一顆 clkbuf_16 放在 driver 旁，兩條時脈線限定走 met3／met4 | **+0.054** | **0** | **採用** |

試驗中發現兩件事：

- 這個版本的 OpenROAD global route 不會把時脈線保持在上層金屬。要另外做一次「只有時脈」的 global route，才會產生只走 met3／met4 的導引。
- 只限制層別也不夠：rc4 的時脈線雖然比較短，via 卻多到 200 個，延遲反而變大。

### 第三步：電源 via 修補（h1c）

h1b 簽核乾淨後，做 W25 結案檢查時發現平均 EM 失敗：SRAM 供電路徑上的單切孔 via4 電流太大，28 mW 時最差達限值的 5.77 倍。H0 在 W25 也遇過同一個問題（PG_B／PG_C／PG_G），所以照 H0 的作法修：

| 輪次 | 做法 | 結果 |
| --- | --- | --- |
| a | 28 mW 時每切孔超過 1.2 mA 的 via4 換成 8 切孔陣列（2 × 4 或 1 × 8），M4 落點須在同網路 M4 內，與異網路 M5 保持 ≥1.6 µm、M4 ≥0.4 µm | 196 處選中，186 處替換（1,452 個切孔） |
| b | 電流最高的 9 處改成 1 × 16 | 9 處完成 |
| c、d | H0 PG_C 作法：2.8 µm 寬的 M4 加寬片，搭配兩欄陣列 | 12 處完成 |
| e、f | 最後兩個熱點：M5／M4 補片，以及一組 3 × 6 陣列 | 完成 |

- 每一處修改都要先通過局部原生 DRC，不能產生新標記，才會接受。
- 修補後重新做全晶片原生 DRC 與 antenna（0／0），再以 `h1c_pg_r1` 重跑整套簽核（`signoff/run_signoff_c.sh`）與活動對應，全部通過。
- 和修補前的 h1b 比較：
  - 網表相同。四個工作負載的活動分析結果完全相同：40,850 條訊號網路的翻轉數、轉換次數與未知值比例都一樣。VCD 檔案本身只有檔頭日期不同；idle 另外有電源／body 接腳的變數代號編排不同，這是模擬器對常數網路的別名處理，不是訊號活動的差異。
  - SPEF 中 40,850 條訊號網路只有 11 條的總電容改變，最多 +1.1%（nom），來源是新增電源金屬附近的耦合電容。
  - 面積與三種 RC 的最差 setup／hold 完全相同。
  - 功耗只在兩個工作負載差 0.000001 mW，總功耗與能量在本報告的精度下不變。
- h1b 的結果封存在 `reports/archive_h1b_prePG/`。

### 與 H0 修補方法的差異

| | H0 | H1 |
| --- | --- | --- |
| 繞線前修復 | RepairDesignPostGRT + ResizerTimingPostGRT | 同一配方，同一組設定 |
| 繞線後手動修補 | W24／W25：調整 51 個 driver、20 顆被動二極體、局部金屬橋、PG_G 供電修正、重新產生 fill；時脈 ECO 加 eco_clock_remote_a／b 和 3 顆 hold buffer | 手動 DRC 局部重繞 3 輪（d1、d2、x1）；用 H0 的 RC 規則做 3 輪 RC ECO（rc1c、rc4r、rc5）；原生補天線 5 輪（f1–f5），x1 也一併補天線；電源 via4 陣列與 M4／M5 補片 6 輪（a–f） |
| 最終檢查 | DRC／antenna／3-RC STA／LVS／功能，加上 W25 結案的 fill／IR／EM／連通／stream 審查 | 同一套，全部通過 |

兩版的修補細節不同，所以幾百 µm² 的 buffer 面積或 ±0.1 mW 的差異，屬於實作上的正常變動。die 面積才是結構性的差異。

## 未涵蓋的檢查

H0 在 W25 結案（`week25_closure/W25_Closure_Report.md`）做過的實體檢查，H1 都已補做並通過（見「W25 結案檢查」）。DFT／pad／ESD 屬於設計層級的審查與需求，兩版共用，H1 沒有另外重做。

兩版共同沒有涵蓋、因此不能直接投片的項目：

- SRAM 沒有合格的多 PVT 模型，也沒有 SRAM 內部的 DRC／LVS。
- 沒有 fill-aware PEX，也就沒有 post-fill 電氣簽核。
- IR／EM 只做靜態、平均電流篩檢：沒有封裝 RLC、暫態、熱與局部電流擁擠，也沒有 SRAM 內部 IR／EM。
- 沒有 foundry 簽核。

## 限制與可信度

| 項目 | 影響 |
| --- | --- |
| SRAM 功耗模型 | 解析模型，有沒有存取功耗都一樣，佔總功耗 74–78%。兩版相同，相減時會抵消，但總功耗的絕對值主要取決於這個未經驗證的模型。 |
| 擺放變異 | 每版只有一次擺放，沒有做 seed 掃描。setup 差異屬於擺放結果，不能當成縮小的效果；功耗的 ±0.1 mW 也在同一量級。 |
| 未知值（X/Z） | H1 約 5.27–5.29%、H0 約 5.51–5.54% 的網路時間是未知值，都來自沒有被讀取的 SRAM bank 輸出。處理方式和 H0 報告相同，沒有重新驗證。 |
| 零延遲模擬 | 標準元件沒有 SDF，glitch 功耗沒算進去，組合邏輯功耗可能偏低。兩版一致。 |
| PVT | 只有 TT 25°C 1.8V。 |
| 實作方法 | 繞線後修補細節不同（見上表）。 |
| 實體量測 | 沒有晶片、封裝或板端量測。 |

## 證據與重跑

- **機器可讀結果**：`reports/H1_PPA_result.json`、`reports/H0_H1_comparison.json`，由 `scripts/summarize_h1c.py` 產生。腳本會檢查：
  - 0 未標註；
  - 18 顆 SRAM 加總等於 Macro 群組；
  - 時窗長度等於週期 × 40 ns；
  - 功能、活動和功耗都用同一份網表、同一份 ODB；
  - routed ODB 的 SHA256 一致；
  - W25 結案結果與加 fill 後的 ODB 是同一份。
- **H1 身分**：
  - 網表 `5c11b7c5…f00b8f0`
  - nominal SPEF `bad7fcde…d0ea0b`
  - mixed VCD `10caa3ae…db475`
  - 加 fill 後的 ODB `9c06b1b0…dc402`
  - routed ODB `29a706cf…08651`（`h1c_pg_r1`）
  - 核心 GDS `ae8a3f29…a22`；含 dummy fill 的 GDS `168b1621…bed17`
- **功耗**：`scripts/power_h1c.tcl`，由 `scripts/run_power_h1c.sh` 在固定 image 中執行；完整輸出在 `logs/power_h1c.log`，結束碼 0。
- **簽核串接**：`../h1/cand_gap90x95/signoff/run_signoff_c.sh h1c_pg_r1`，紀錄在 `signoff/logs_c/chain.log`。
- **活動對應**：`signoff/run_activity_cov_c.sh`。
- **電源 via 修補**：`../h1/cand_gap90x95/eco/pg_h1_fix.py`、`pg_h1_fix_b.py` 到 `pg_h1_fix_f.py`；修補後的 DRC／antenna 與封裝由 `eco/h1c_driver.sh` 執行。
- **W25 結案檢查**：`../h1/cand_gap90x95/closure_c/run_h1_closure.sh`（紀錄 `closure_c/logs/chain.log`）與 `closure_c/run_density_die.sh`；判定由 `closure_c/scripts/write_h1_closure_result.py` 寫入 `closure_c/reports/H1_closure_result.json`，14 項全部通過。
- **關鍵路徑比對**：`eco/b_crit_path_cmp.sh`，紀錄在 `eco/logs/b_crit_cmp.log`（h1b 與 h1c 時序相同）。
- **完整實作歷程**：`../WORK_STATE.json` 的 `H1.h1b_pass` 與 `H1.w25_closure_gates`。

本輪沒有修改任何 W25 凍結證據（`week25_closure`、`week25_signoff` 只讀取）。
