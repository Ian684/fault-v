# Fault-V 應用擴充：實際驗證報告

實際執行日期：2026-10-14；Vivado／XSim 2022.2、xc7z020clg400-1、PYNQ-Z2。依原流程完成應用階段；優化、創意及新問題研究留到A／B／C完成後。

## 完成範圍與設計身分

INT8 Conv1D、24→4全連接層、Conv→量化／ReLU→FC→量化／argmax串接，另有Q15 FIR8、IIR1、FFT16。16個CPU／SoC RTL檔案全部SHA256與已驗證XFaultVDSP v1.1基準一致；更換的是應用ROM與平台wrapper的ROM檔名。

卷積6乘積視窗使用DOT4ACC，FC用六組DOT4ACC，量化RQNT8；FIR/IIR用MAC16；FFT複數乘法使用四次MUL16。未新增ISA、DMA、scratchpad或pipeline。

## 實際功能驗證

| 項目 | 結果 | 證據 |
| --- | --- | --- |
| 直接參考 | 34資料集；卷積／FC／串接各6、FIR5、IIR4、FFT7 | application_models.py、programs/application_datasets.json |
| 機器碼模型 | 68個RV32I／custom image全部輸出正確；實際指令、Load、Store、custom數用於RTL交叉檢查 | binary_model.py、programs/application_manifest.json |
| RTL完整應用 | 68images×2延遲×3重跑＝408次；所有INT32、packed INT8、argmax、Q15／複數輸出正確，來源資料不改動 | logs/tb_applications.log |
| 中途reset | 每image／延遲模式1次，共136次；pending RAM交易中reset，保留RAM再跑，結果與cycle一致 | logs/tb_applications.log |
| 示範ROM | 4輪；每輪132項結果、548次custom、8UARTbytes；2359words，未超過4096word IMEM | logs/tb_application_demo.log |
| 失敗路徑 | 4次；兩模式各早期／FFT晚期破壞，失敗編號1／101，status=2、GPIO=F、EBREAK | logs/tb_application_demo.log |
| FPGA wrapper | 3輪、24UARTbytes，run與BTN reset通過 | logs/tb_payload.log |
| 原自訂單元 | 201576個結果、26次取消；握手與數值回歸通過 | logs/tb_custom_exec.log |
| 原RV32I／程式 | 1372次，兩模式各40/40指令名稱 | logs/tb_verification_suite.log |
| 原IO／fault | 16交易、8錯誤案例 | logs/tb_fault_v_io.log、logs/tb_io_faults.log |
| 原stress | 4完整程式、4096UARTbytes、4次RAM/UART執行中reset | logs/tb_stress.log |

三次完整執行包含兩次重新載入RAM及一次中斷後保留RAM重啟。每次動態指令／交易數都與獨立機器碼模型一致。Cycle逐筆核對：(IMEM_DELAY+5)×instructions＋(DMEM_DELAY+3)×loads＋(DMEM_DELAY+2)×stores＋custom_extra。兩延遲模式差值另核對3×instructions＋6×(loads+stores)。

第一輪遇到的是測試平台逾時誤報：較快模式完成後仍計時，等待較慢模式時超過每程式限制。修正done gating後全部重跑通過。FC named輸入也補正為實際零／正／負／交錯極值資料；展示ROM的內容SHA保持不變。第一輪log留存供追溯，不作成功證據。

## 效能：所有資料集加總比較

下表每個資料集只取一次完整執行，不把重跑當新樣本。加總RV32I cycles／加總custom cycles是加權加速比，不是各加速比的平均；每組詳細資料另在results.csv。

| 應用 | 延遲模式 | 資料集 | RV32I總cycles | Custom總cycles | 加權加速比 | 最小 | 最大 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CONV1D_INT8 | 0 | 6 | 265062 | 57774 | 4.5879 | 4.3989 | 4.7195 |
| FC_INT8 | 0 | 6 | 163524 | 11610 | 14.0848 | 13.8927 | 14.3427 |
| CHAIN_INT8 | 0 | 6 | 427056 | 69300 | 6.1624 | 6.0222 | 6.3048 |
| FIR8_Q15 | 0 | 5 | 751666 | 85234 | 8.8189 | 8.4899 | 9.4629 |
| IIR1_Q15 | 0 | 4 | 164000 | 17312 | 9.4732 | 9.4288 | 9.5203 |
| FFT16_Q15 | 0 | 7 | 492230 | 106674 | 4.6143 | 4.5988 | 4.6358 |
| CONV1D_INT8 | 1 | 6 | 406953 | 95373 | 4.2670 | 4.0938 | 4.3850 |
| FC_INT8 | 1 | 6 | 250425 | 18846 | 13.2880 | 13.1082 | 13.5193 |
| CHAIN_INT8 | 1 | 6 | 655083 | 114093 | 5.7417 | 5.6126 | 5.8692 |
| FIR8_Q15 | 1 | 5 | 1138459 | 136891 | 8.3165 | 8.0073 | 8.9158 |
| IIR1_Q15 | 1 | 4 | 247088 | 26672 | 9.2639 | 9.2208 | 9.3098 |
| FFT16_Q15 | 1 | 7 | 749657 | 170427 | 4.3987 | 4.3840 | 4.4188 |

## 個別資料集：預設延遲模式

| 應用 | 資料 | RV32I cycles | Custom cycles | RV32I指令 | Custom指令 | 加速比 |
| --- | --- | --- | --- | --- | --- | --- |
| CONV1D_INT8 | zeros | 44646 | 9630 | 7193 | 1321 | 4.6361 |
| FC_INT8 | zeros | 27417 | 1941 | 4429 | 265 | 14.1252 |
| CHAIN_INT8 | zeros | 72027 | 11559 | 11616 | 1584 | 6.2312 |
| CONV1D_INT8 | positive | 42150 | 9582 | 6777 | 1313 | 4.3989 |
| FC_INT8 | positive | 27219 | 1953 | 4396 | 267 | 13.9370 |
| CHAIN_INT8 | positive | 69321 | 11511 | 11165 | 1576 | 6.0222 |
| CONV1D_INT8 | negative | 43734 | 9678 | 7041 | 1329 | 4.5189 |
| FC_INT8 | negative | 27447 | 1929 | 4434 | 263 | 14.2286 |
| CHAIN_INT8 | negative | 70569 | 11607 | 11373 | 1592 | 6.0799 |
| CONV1D_INT8 | alternating_extremes | 45222 | 9582 | 7289 | 1313 | 4.7195 |
| FC_INT8 | alternating_extremes | 27495 | 1917 | 4442 | 261 | 14.3427 |
| CHAIN_INT8 | alternating_extremes | 72423 | 11487 | 11682 | 1572 | 6.3048 |
| CONV1D_INT8 | random_a | 44394 | 9654 | 7151 | 1325 | 4.5985 |
| FC_INT8 | random_a | 27147 | 1941 | 4384 | 265 | 13.9861 |
| CHAIN_INT8 | random_a | 71325 | 11583 | 11499 | 1588 | 6.1577 |
| CONV1D_INT8 | random_b | 44916 | 9648 | 7238 | 1324 | 4.6555 |
| FC_INT8 | random_b | 26799 | 1929 | 4326 | 263 | 13.8927 |
| CHAIN_INT8 | random_b | 71391 | 11553 | 11510 | 1583 | 6.1794 |
| FIR8_Q15 | impulse | 144074 | 16970 | 23655 | 2343 | 8.4899 |
| FIR8_Q15 | step | 144074 | 16970 | 23655 | 2343 | 8.4899 |
| FIR8_Q15 | random | 145034 | 16970 | 23815 | 2343 | 8.5465 |
| FIR8_Q15 | positive_saturation | 157898 | 17354 | 25959 | 2407 | 9.0987 |
| FIR8_Q15 | negative_saturation | 160586 | 16970 | 26407 | 2343 | 9.4629 |
| IIR1_Q15 | impulse | 40808 | 4328 | 6764 | 652 | 9.4288 |
| IIR1_Q15 | step | 40808 | 4328 | 6764 | 652 | 9.4288 |
| IIR1_Q15 | alternating | 41180 | 4328 | 6826 | 652 | 9.5148 |
| IIR1_Q15 | random | 41204 | 4328 | 6830 | 652 | 9.5203 |
| FFT16_Q15 | zeros | 70058 | 15234 | 11447 | 2267 | 4.5988 |
| FFT16_Q15 | impulse | 70058 | 15234 | 11447 | 2267 | 4.5988 |
| FFT16_Q15 | dc | 70058 | 15234 | 11447 | 2267 | 4.5988 |
| FFT16_Q15 | real_tone | 70334 | 15234 | 11493 | 2267 | 4.6169 |
| FFT16_Q15 | complex_tone | 70538 | 15234 | 11527 | 2267 | 4.6303 |
| FFT16_Q15 | random | 70622 | 15234 | 11541 | 2267 | 4.6358 |
| FFT16_Q15 | fullscale_saturation | 70562 | 15270 | 11531 | 2273 | 4.6210 |

Cycle來自RTL；μs按50MHz換算。包含指標／迴圈初始化、原始輸入Load、卷積CPU打包、bias、量化／ReLU、argmax、串接資料搬移、FFT bit-reversal／twiddle／工作RAM及所有單元等待；排除testbench資料載入、reset、完成回報、EBREAK、UART。兩種程式都在相同擴充CPU上執行，RV32I版本不含custom/M；不是不同面積CPU的比較。

RV32I使用可提早結束的inline signed shift/add，不宣稱最佳編譯器實作。量化資料限定比例乘積可放INT32；完整RQNT8指令48-bit語意沿用基準。加速依資料與控制路徑而異。

## 固定點精度與飽和

LSB是原始Q15整數單位，實數誤差等於下列值／32768。FIR對已限制INT16的理想浮點結果比較；IIR對無逐步取整的浮點回授；FFT對直接O(N²)正向DFT／16。

| 應用 | 資料 | 最大誤差LSB | 限制次數 |
| --- | --- | --- | --- |
| FIR8_Q15 | impulse | 0.0000 | 0 |
| FIR8_Q15 | step | 0.0000 | 0 |
| FIR8_Q15 | random | 0.9062 | 0 |
| FIR8_Q15 | positive_saturation | 0 | 32 |
| FIR8_Q15 | negative_saturation | 0 | 32 |
| IIR1_Q15 | impulse | 2.2195 | 0 |
| IIR1_Q15 | step | 1.9955 | 0 |
| IIR1_Q15 | alternating | 2.3501 | 0 |
| IIR1_Q15 | random | 1.9620 | 0 |
| FFT16_Q15 | zeros | 0.0000 | 0 |
| FFT16_Q15 | impulse | 0.0000 | 0 |
| FFT16_Q15 | dc | 4.0000 | 0 |
| FFT16_Q15 | real_tone | 1.9861 | 0 |
| FFT16_Q15 | complex_tone | 1.0000 | 0 |
| FFT16_Q15 | random | 1.5625 | 0 |
| FFT16_Q15 | fullscale_saturation | 8416.3367 | 3 |

非飽和FFT六案例最大誤差4LSB，檢查門檻12LSB；IIR最大約2.3501LSB，門檻4LSB；FIR非飽和誤差小於1LSB。Full-scale FFT案例有3個stage/component限制，對未限制浮點DFT的誤差約8416.34LSB，屬已知飽和失真；整數RTL符合逐階段限制的golden，不宣稱此案例有低失真精度。

圖表：figures/DSP_Precision.png與.pdf。Twiddle +1量化為32767，每階段算術右移1，最後比例1/16；逐階段取整不能等同於最後一次取整。

## FPGA與實板

整合平台：3402 LUT、2811 FF、8 BRAM tiles、4 DSP。50 MHz WNS=3.738 ns、WHS=0.03 ns、WPWS=9.02 ns；無未約束內部最大延遲端點，route errors=0、Methodology violations=0。

DRC Error／Critical Warning=0，保留16個DSP pipeline效能建議：DPIP-1×8、DPOP-1×4、DPOP-2×4。PYNQ PS preset沿用PSU-1／PSU-2負DDR skew(-0.009／-0.033) critical warnings，沒有改severity、修改這些參數或執行ps7_init；板子先SD開機Linux。不宣稱所有建置訊息無warning，也不把vectorless power推估當實測功耗。

實際載入配對bit/HWH，ARM讀到50.0MHz，三次每次8bytes完全符合APP OK＋CR/LF，errors=0、FIFO無多餘字元、status=1、halted=1、cause=9。每輪CPU自行比較132項結果。板上資料與fpga_identity的映像SHA一致，證據為logs/extension_b_fpga_uart.log、logs/board_verification.json。

使用者確認：LD0／LD2亮、LD1／LD3滅；按住BTN0四燈熄滅，放開後LD0／LD2恢復。這是使用者觀察證據。

## 範圍限制與交付

未量測板上benchmark cycle、實際功耗或外部Pmod電氣傳輸；未做訓練／真實資料集分類準確率、所有模型尺寸、所有係數、完整輸入空間形式證明、DMA／pipeline／ASIC PPA。有限案例的精度不保證任意資料同樣表現。

卷積kernel定義為不反轉權重的sum input[n+k,c]×weight[o,k,c]。FIR有效視窗對應一般filter的反向係數及n+7對齊。IIR定義正回授係數0.75。參考：[SciPy差分方程](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html)、[FFT forward normalization](https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.fft.html)。逐步固定點政策以本專案規格為準。

Notion只放架構、演算法、資料格式、介面、操作與驗收規則；本報告、CSV、logs、figure與SHA256交付包保留實際證據。按照使用者安排，下一階段沿原路線做C，優化、創意與新問題研究暫緩。
