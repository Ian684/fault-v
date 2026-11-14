# Fault-V 運算單元擴充：實際驗證報告

實際執行日期：2026-10-14。平台：Vivado／XSim 2022.2、xc7z020clg400-1、PYNQ-Z2。獨立 Notion 筆記只放設計與驗收規則，本文件保存實際證據。

## 驗證範圍

延伸 A 六個方向均有選定實作：四乘法器 DOT4、DOT4ACC／MAC16、ADD8SAT／SUB8SAT、RQNT8、DOT2SAT、DOT8／DOT4SU。保留原四條編碼，共十二條。

| 實際測試 | 結果 | 證據 |
| --- | --- | --- |
| 執行單元 | 201550 個向量＋26 次 reset 後重跑＝201576 個結果正確；接受201602＝完成201576＋取消26 | logs/tb_custom_exec.log |
| packed 飽和 | ADD／SUB 各65536個byte輸入組合；四lane重複同值，另以隨機資料檢查不同lane及carry隔離 | verify/unit.vec |
| 量化 | 21280個特定極值／shift／zero-point組合，另4096隨機向量；Python用divmod，RTL用幅值加偏置捨入 | generate.py、reference.py、rtl/custom_exec.sv |
| CPU | 1911案例×2種記憶體延遲＝3822；每模式1012個非法funct7/funct3組合 | logs/tb_custom_cpu.log |
| CPU reset | 52位置；含額外讀rd、第一／第二拍、回應、提交前；重跑恰好提交一次 | logs/tb_custom_reset.log |
| 完整自我檢查 | 4輪，每輪159個RAM輸出、302次custom、8UARTbytes；2828words ROM | logs/tb_custom_program.log |
| 失敗路徑 | 4次早期／晚期結果破壞，兩種延遲；正確status=2、LED=F及失敗編號 | logs/tb_custom_program.log |
| 原RV32I／程式 | 1372次，兩模式各40/40指令名稱 | logs/tb_verification_suite.log |
| 周邊 | 16 IO交易、8 fault案例 | logs/tb_fault_v_io.log、logs/tb_io_faults.log |
| 壓力 | 4完整程式、4096 UARTbytes、4次RAM/UART執行中reset | logs/tb_stress.log |
| FPGA wrapper | 3輪、24UARTbytes、run與BTN重置 | logs/tb_payload.log |
| benchmark | 28images×2延遲×2reset重跑＝112次；全部輸出正確，重跑cycle相同 | logs/tb_benchmark.log |
| 單獨共用／並行單元 | 原四指令16398向量；數值相同，DOT4 E4／E1，回應持有與一次取走正確 | logs/tb_unit_comparison.log |

所有benchmark都核對FSM公式：cycles=(IMEM_DELAY+5)×retire+(DMEM_DELAY+3)×loads+(DMEM_DELAY+2)×stores+custom_extra。單拍非累加custom額外2拍；累加類或RQNT8／DOT8額外3拍。兩延遲模式的差值另核對3×retire+6×(loads+stores)。

## 50 MHz RTL效能：預設記憶體延遲

| 工作負載 | RV32I cycles | Custom cycles | RV32I指令 | Custom指令 | RV32I μs | Custom μs | 加速比 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DOT64 | 21671 | 985 | 3526 | 137 | 433.420 | 19.700 | 22.001 |
| FIR8_RAW | 20206 | 3950 | 3269 | 553 | 404.120 | 79.000 | 5.115 |
| FIR8_PACKED | 20782 | 1454 | 3429 | 201 | 415.640 | 29.080 | 14.293 |
| FIR16 | 50518 | 3818 | 8321 | 495 | 1010.360 | 76.360 | 13.232 |
| QNT16 | 1216 | 864 | 184 | 120 | 24.320 | 17.280 | 1.407 |
| SATADD64 | 6614 | 4342 | 985 | 585 | 132.280 | 86.840 | 1.523 |
| DOT4ACC_16 | 21534 | 1410 | 3549 | 187 | 430.680 | 28.200 | 15.272 |
| MAC16_16 | 11544 | 1410 | 1884 | 187 | 230.880 | 28.200 | 8.187 |
| ADD8SAT_16 | 5762 | 1138 | 931 | 155 | 115.240 | 22.760 | 5.063 |
| SUB8SAT_16 | 5726 | 1138 | 925 | 155 | 114.520 | 22.760 | 5.032 |
| RQNT8_16 | 6308 | 1154 | 1022 | 155 | 126.160 | 23.080 | 5.466 |
| DOT2SAT_16 | 22448 | 1138 | 3712 | 155 | 448.960 | 22.760 | 19.726 |
| DOT8_16 | 24194 | 1154 | 4003 | 155 | 483.880 | 23.080 | 20.965 |
| DOT4SU_16 | 23846 | 1138 | 3945 | 155 | 476.920 | 22.760 | 20.954 |

## 50 MHz RTL效能：較長記憶體延遲

| 工作負載 | RV32I cycles | Custom cycles | 加速比 |
| --- | --- | --- | --- |
| DOT64 | 33023 | 1594 | 20.717 |
| FIR8_RAW | 30925 | 6485 | 4.769 |
| FIR8_PACKED | 31405 | 2357 | 13.324 |
| FIR16 | 76393 | 6215 | 12.292 |
| QNT16 | 1960 | 1416 | 1.384 |
| SATADD64 | 10721 | 7249 | 1.479 |
| DOT4ACC_16 | 32565 | 2355 | 13.828 |
| MAC16_16 | 17580 | 2355 | 7.465 |
| ADD8SAT_16 | 8843 | 1891 | 4.676 |
| SUB8SAT_16 | 8789 | 1891 | 4.648 |
| RQNT8_16 | 9662 | 1907 | 5.067 |
| DOT2SAT_16 | 33872 | 1891 | 17.912 |
| DOT8_16 | 36491 | 1907 | 19.135 |
| DOT4SU_16 | 35969 | 1891 | 19.021 |

## 原相同程式：共用版對並行版

| 工作負載 | 延遲模式 | 共用cycles | 並行cycles | 省下cycles | 共用/並行 |
| --- | --- | --- | --- | --- | --- |
| DOT64 | 0 | 1033 | 985 | 48 | 1.049 |
| FIR8_RAW | 0 | 4046 | 3950 | 96 | 1.024 |
| FIR8_PACKED | 0 | 1550 | 1454 | 96 | 1.066 |
| FIR16 | 0 | 3818 | 3818 | 0 | 1.000 |
| QNT16 | 0 | 864 | 864 | 0 | 1.000 |
| SATADD64 | 0 | 4342 | 4342 | 0 | 1.000 |
| DOT64 | 1 | 1642 | 1594 | 48 | 1.030 |
| FIR8_RAW | 1 | 6581 | 6485 | 96 | 1.015 |
| FIR8_PACKED | 1 | 2453 | 2357 | 96 | 1.041 |
| FIR16 | 1 | 6215 | 6215 | 0 | 1.000 |
| QNT16 | 1 | 1416 | 1416 | 0 | 1.000 |
| SATADD64 | 1 | 7249 | 7249 | 0 | 1.000 |

DOT64省48cycles＝16次DOT4×3。兩組FIR8省96cycles＝32次DOT4×3。FIR16／QNT／SATADD的相同程式cycle未改變。原RV32I baseline cycle完全重現。

並行降低單元延遲，仍受取指、Load／Store及FSM影響。RQNT8的軟體benchmark只處理本文件明列的INT32乘積資料；完整48-bit ISA功能由單元與CPU資料驗證。資料初始化／UART不在量測區間；FIR8_RAW打包計入，FIR8_PACKED前處理排除。基準為手寫inline shift/add，不宣稱最佳編譯器結果。

## 資源與時序

| 範圍 | LUT | FF | DSP |
| --- | --- | --- | --- |
| 原四指令共用單元（獨立合成） | 305 | 119 | 1 |
| 原四指令並行單元（獨立合成） | 288 | 103 | 4 |
| 十二指令整合平台（routed） | 3402 | 2811 | 4 |

整合平台另使用 8 BRAM tiles；50 MHz WNS=3.738 ns、WHS=0.03 ns、WPWS=9.02 ns；沒有未約束的內部最大延遲端點，路由錯誤0、Methodology violations0。

DRC保留16個DSP未使用內建pipeline的效能提示：DPIP-1×8、DPOP-1×4、DPOP-2×4；DRC Error／Critical Warning均0，不宣稱zero-warning。BD仍沿用PSU-1／PSU-2負DDR skew(-0.009／-0.033)的PYNQ preset警告，沒有改severity或執行ps7_init；Linux已先SD開機。Power活動推估不能當實測功耗。

獨立四指令單元的資源比較使用相同Vivado合成設定，不包含CPU、IO或RAM，也未為該兩個獨立top做routed timing。並行版省掉lane／累加狀態，故LUT／FF可能下降，DSP由1變4；不可把各種資源混成單一面積數字。

整合平台對原版2760 LUT／2697 FF／8 BRAM／1 DSP增加642 LUT、114 FF、3 DSP；包含八條新增功能及不同ROM，不能全歸因於單獨DOT4並行化。ASIC PPA尚未分析。

## 實板證據

實際上傳並載入本版bit/HWH，ARM讀到50.0 MHz。三輪各8 bytes完全符合DSP OK加CR/LF；錯誤旗標0，FIFO無多餘字元；每輪status=1、halted=1、cause=9。自我檢查每輪核對159個結果。這是功能驗證，benchmark cycle來自RTL模擬；沒有板上cycle counter或功耗量測。

證據：logs/extension_a_fpga_uart.log、logs/board_verification.json、fpga_identity.json。板上結果與本版映像SHA256核對一致。

使用者確認：LD0／LD2亮，LD1／LD3滅；按住BTN0四燈熄滅，放開後LD0／LD2恢復。此為使用者觀察證據。

## 限制與交付

有限測試不是完整輸入空間形式證明；未驗證外接Pmod電氣傳輸、長時間老化、所有工具鏈、跨製程、ASIC版圖或全框架bit-exact量化。沒有加入延伸B應用、延伸C DMA／流水線或ASIC PPA。CPU仍無標準M/V、CSR／中斷／完整machine-mode。

全部RTL、程式、向量、腳本、映像與實際報告以SHA256清單封裝。Notion技術筆記與本報告分開。重現命令見README.md。
