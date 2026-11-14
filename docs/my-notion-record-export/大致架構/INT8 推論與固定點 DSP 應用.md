# INT8 推論與固定點 DSP 應用

## 1．整體架構與範圍

應用程式在既有 Fault-V 上執行：32-bit、多周期、單指令依序執行，RV32I＋XFaultVDSP v1.1 十二條自訂指令。CPU、Register File、FSM、自訂運算單元與 UART／GPIO 的 RTL 延續運算單元擴充版。

本階段增加的是 Assembly 應用、資料、參考模型、驗證環境及 FPGA 展示 ROM。CPU 維持四個乘法器與兩讀一寫 Register File，尚未增加 DMA、scratchpad 或流水化。

```
輸入、係數、bias、量化參數 → 資料 RAM
                                 │
                           Load／Store
                                 │
                     Fault-V 執行 Assembly 迴圈
                         │               │
                       RV32I        DSP 自訂單元
                         └───────┬───────┘
                                 ▼
                     中間結果、輸出、分類索引
                                 │
                     自我檢查 → UART／GPIO／狀態
```

## 2．應用清單

| 應用 | 輸入與規模 | 輸出 | 使用的自訂指令 |
| --- | --- | --- | --- |
| CONV1D_INT8 | 10 個位置×2 input channels；3 taps；3 output channels；stride=1、valid | 8×3 INT32 累加結果、24 個 INT8 activation | DOT4ACC、RQNT8 |
| FC_INT8 | 24 個 INT8 feature；4 個輸出；每輸出有 bias | 4 個 INT32 累加值、4 個 INT8 logit、argmax 索引 | DOT4ACC、RQNT8 |
| CHAIN_INT8 | 卷積→量化→ReLU→flatten→全連接→量化→argmax | 完整中間結果與最終索引 | DOT4ACC、RQNT8 |
| FIR8_Q15 | 39 個 signed INT16 sample；8 個 Q15 coefficient | 32 個有效視窗的 Q15 輸出 | MAC16 |
| IIR1_Q15 | 32 個 signed INT16 sample；一階回授 | 32 個 Q15 輸出 | MAC16 |
| FFT16_Q15 | 16 個複數 Q15 sample；radix-2 DIT | 16 個複數 Q15 頻域值 | MUL16 |

INT8 推論使用固定權重與合成測試輸入，驗證完整運算流程。沒有訓練模型、真實資料集或分類準確率的成果聲明。Argmax 是對四個量化 logit 取最大值；同值選最小索引，不另外計算 softmax。

## 3．INT8 卷積與資料排列

本專案以以下公式定義 kernel，權重不反轉：

```
acc[n,o] = bias[o]
         + Σ(k=0..2) Σ(c=0..1) input[n+k,c] × weight[o,k,c]

q[n,o]   = RQNT8(acc[n,o], control[o])
act[n,o] = max(0, q[n,o])
```

input 以位置優先、channel 在內排列：`[x[0,0],x[0,1],x[1,0],x[1,1],…]`。每個 output channel 的六個權重依 tap／input channel 排列；輸出也採位置優先，再依 output channel 排列。

每個輸出有六組乘積。Custom 版以四組＋兩組的 DOT4ACC 完成；第二組的兩個未用 lane 明確填零。來源視窗可能不對齊 word，所以用 LBU／移位／OR 打包；這些指令全部計入執行時間。

bias 先載入累加 rd，再執行 DOT4ACC。參考模型檢查累加值可放進 signed INT32，避免 modulo 2³² 的指令行為讓本應用意外溢位。

卷積 output zero-point 固定為 0，因此 ReLU 的下限為整數 0。輸出共24 bytes，可直接作為串接全連接層的輸入。

## 4．全連接層與 argmax

```
acc[o] = bias[o] + Σ(i=0..23) feature[i] × weight[o,i]
logit[o] = RQNT8(acc[o], control[o])
prediction = 第一個取得最大 logit 的索引
```

Custom 版每個輸出使用六次 DOT4ACC。Feature 和每列24 bytes的權重均 word aligned，因此可使用 LW 讀取四個 lane。四個 logit 使用相同的 multiplier、shift 和 zero-point，讓 argmax 比較具有一致尺度。

獨立 FC 程式由資料 RAM 讀24個測試 feature；串接版則讀取剛完成的卷積 activation。串接版包含中間資料寫回、重讀與兩層計算，不只量測內積指令。

## 5．量化規則

沿用 RQNT8：rs1 是 signed INT32；rs2 保存 signed INT16 multiplier、5-bit shift 與 signed INT8 zero-point。

```
product = acc × multiplier
rounded = 最近整數(product / 2^shift)，恰好一半時遠離零
output  = clamp(rounded + zero_point, -128, 127)
```

卷積有各 output channel 的量化控制字；全連接層四個輸出使用相同控制字。獨立參考模型以整數除法和餘數實作捨入。

本應用資料的比例乘積經檢查可放進 signed INT32，純 RV32I 版能用32-bit shift/add得到相同結果。RQNT8 指令本身的完整48-bit乘積語意仍沿用原規格。

## 6．Q15 固定點格式

signed INT16 原始值 `r` 代表實數 `r / 32768`，範圍 −1～接近1。例如8192表示0.25，24576表示0.75。

```
Q15 × Q15 → signed INT32 乘積，比例因子為 2^30
恢復 Q15 → 對乘積或累加值算術右移15位
寫出前   → 限制到 −32768～32767
```

DSP 應用使用算術右移，負數朝負無限方向取整；與 RQNT8 的 nearest 捨入規則分開。輸入與係數用 LH 讀取；輸出 Q15 原始值以符號擴展 INT32 保存，便於驗證與後續 CPU 處理。

## 7．八抽頭 FIR

```
acc[n] = Σ(k=0..7) sample[n+k] × coefficient[k]
y[n]   = clamp_INT16(acc[n] >>> 15)，n=0..31
```

以39個 sample 產生32個有效視窗。這個視窗索引等價於一般 FIR 使用反向係數、再取輸出索引 n+7；本例的係數是對稱的。

一般係數的總和為32768，即 DC gain=1；飽和測試的係數總和為65536，即 gain=2。資料限制為 sample 絕對值不超過20000、係數絕對值總和不超過65536，故 INT32 累加值不溢位。

每個輸出先清空 rd，再以八次 MAC16 累加。原始sample與係數保持不變，下一個輸出將視窗前進一個 halfword。包含脈衝、階躍、隨機與正／負飽和案例。

## 8．一階 IIR

```
y[-1] = 0
acc[n] = 8192 × x[n] + 24576 × y[n-1]
y[n]   = clamp_INT16(acc[n] >>> 15)
```

實數形式為 `y[n]=0.25×x[n]+0.75×y[n−1]`。回授係數的絕對值小於1；本例的正係數總和為1，且每步限制到INT16。

兩次 MAC16 計算輸入項與回授項；y[n−1] 保存於一般 Register File，沒有另加硬體狀態。每次程式啟動都把前值設為0，reset 後重跑不依賴 RAM 的舊輸出。

浮點參考保留未取整的回授值；固定點參考使用每步量化後的 y[n−1]。比較兩者的差異，才能看出回授累積的量化誤差。

## 9．16 點複數 FFT

使用 radix-2、decimation-in-time。先按4-bit bit-reversal把輸入搬到工作區，再執行 m=2、4、8、16 四個階段，輸出以自然頻率順序排列。

```
t_real = (v_real×w_real − v_imag×w_imag) >>> 15
t_imag = (v_real×w_imag + v_imag×w_real) >>> 15

upper = clamp_INT16((u + t) >>> 1)
lower = clamp_INT16((u − t) >>> 1)
```

每個 butterfly 的複數乘法使用四次 MUL16。Twiddle table 有8組Q15實部／虛部，來自 `exp(−j×2π×k/16)`；+1以32767表示，−1可以用−32768表示。

每個階段右移1位，四階段的總比例為1/16，因此與**正向 DFT 除以16**比較。每一階段都先做乘法的Q15轉換，再做加減、右移與INT16限制；不能把所有取整延後到最後一階段。

Bit-reversal搬移、twiddle讀取、所有工作 RAM Load／Store、加減、移位與限制都計入執行時間。每次啟動重新從原始輸入建立工作區，工作RAM保留也能重新執行。

驗證包含零輸入、脈衝、DC、實數單頻、複數單頻、隨機及full-scale飽和。整數golden檢查逐階段量化語意；另外以直接O(N²)浮點DFT檢查頻率順序、正負號和1/16比例。飽和案例的失真會另列，不以一般低振幅的誤差門檻判定。

## 10．資料記憶體配置

以下均為相對資料 RAM 起點 `0x10000000` 的 byte offset。

| Offset | 內容 | 格式 |
| --- | --- | --- |
| 0x000 | 卷積輸入 | 20 signed INT8 |
| 0x040 | 卷積權重 | 3×6 signed INT8 |
| 0x080／0x090 | 卷積 bias／control | 各3個word |
| 0x100 | 獨立FC輸入 | 24 signed INT8 |
| 0x180 | FC權重 | 4×24 signed INT8 |
| 0x200／0x210 | FC bias／control | 各4個word |
| 0x300／0x380 | FIR sample／coefficient | 39／8個signed halfword |
| 0x400 | IIR sample | 32個signed halfword |
| 0x500／0x580 | FFT sample／twiddle | 16／8組複數signed halfword |
| 0x7FC | 示範程式失敗編號 | 只有status=2時有效 |
| 0x800／0x900 | 卷積／FC原始累加結果 | 24／4個signed word |
| 0x1000／0x1100 | 卷積activation／FC logit | 24／4個signed byte |
| 0x1110 | Argmax索引 | unsigned word，0～3 |
| 0x1200／0x1300 | FIR／IIR輸出 | 各32個符號擴展Q15 word |
| 0x1400 | FFT工作區暨輸出 | 16組實部／虛部，各為符號擴展Q15 word |

UART data/status仍為0x20000100／0x20000104；GPIO仍為0x20000200／0x20000204；完成狀態仍為0x20000000。

## 11．軟體比較與量測邊界

每個資料集都有純RV32I與custom版本，讀相同原始輸入、權重、係數、bias與control，寫出相同結果。純RV32I乘法採inline signed shift/add，沒有標準M或custom指令。

第一個PC=0的取指請求被接受時開始，下一次取指到kernel_end前結束。初始化指標、迴圈、CPU資料打包、ReLU、量化、argmax、FFT搬移與所有RAM交易都計入；排除testbench載入資料、reset、完成狀態寫入、EBREAK及UART。

取指／資料延遲模式為1／1和4／7。程式先重跑，再於pending RAM交易中reset後保留RAM重新執行，確認IIR state、FFT工作區與串接中間結果重新建立。

參考模型、RTL與程式產生器分開。機器碼模型另檢查實際指令數、custom、Load／Store；cycle再用FSM公式獨立核對。加速比代表本資料與本手寫基準，不宣稱最佳編譯器或所有應用都相同。

## 12．展示與驗收規則

`applications_demo.mem` 是可獨立啟動的ROM：CPU自己填入資料，依序執行CHAIN、FIR、IIR、FFT，再比較所有預期結果。

| 條件 | 要看到的行為 |
| --- | --- |
| 所有比較相同 | UART輸出`APP OK\r\n`，GPIO=5，status=1，EBREAK |
| 任一比較失敗 | 記錄失敗編號，GPIO=15，status=2，EBREAK；不輸出成功字串 |
| 其他CPU錯誤 | 停止並保留halt_cause、fault_pc、fault_addr |
| BTN0 reset | 重置CPU，程式重新初始化並執行 |
| RTL應用驗收 | 所有原始／packed輸出與golden一致，來源資料不被修改，重跑與保留RAM重啟一致 |
| 固定點精度 | FIR／IIR對浮點參考檢查誤差；FFT對直接DFT檢查頻率、比例與誤差，另列飽和失真 |
| FPGA驗收 | 配對bit/HWH、50 MHz時序、DSP數、UART設定與實板結果符合規格 |

有限案例不是完整輸入空間證明。這階段的應用參數範圍、取整與飽和政策均已列出；其他模型尺寸、係數或格式需要重新分析並驗證。

## 13．檔案與操作

| 檔案 | 用途 |
| --- | --- |
| application_models.py | 直接整數golden、浮點參考、測試資料 |
| application_asm.py | 產生各應用Assembly |
| binary_model.py | 獨立解碼與執行生成的機器碼 |
| generate_applications.py | 產生完整S／mem、inputs、golden、manifest與示範ROM |
| programs/applications/ | 每個應用與資料集的RV32I／custom程式和輸入 |
| verify/ | 應用、自我檢查、reset、周邊及既有CPU回歸測試 |
| Application_Extensions_Notion.md | 本份設計筆記 |
| Verification_Report.md／results.csv | 獨立實際驗證與效能資料 |

```powershell
python .\generate_applications.py
powershell -ExecutionPolicy Bypass -File .\run_regression.ps1
powershell -ExecutionPolicy Bypass -File .\run_applications.ps1
powershell -ExecutionPolicy Bypass -File .\run_payload.ps1
powershell -ExecutionPolicy Bypass -File .\run_build.ps1
python .\make_delivery.py
```

生成、模擬及建置不自動下載板子。需要實板時，使用`deploy_and_receive.py`載入配對映像；PYNQ的ARM／Ethernet接收UART內容。實際測試紀錄留在專案報告，與本份Notion設計筆記分開。

參考定義：[SciPy filter差分方程](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html)、[FFT的forward normalization](https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.fft.html)。本專案的逐步固定點取整與飽和以本文件為準。