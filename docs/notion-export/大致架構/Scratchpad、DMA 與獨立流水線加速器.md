# Scratchpad、DMA 與獨立流水線加速器

## 1．整體架構

CPU 保持 32-bit、多周期、單指令依序執行，以及 XFaultVDSP 的十二條自訂指令。新增的 DMA 與向量點積加速器是 CPU 之外的記憶體存取來源，透過 Memory-mapped I/O 設定及啟動。

CPU 啟動工作後可以執行其他程式，讀取狀態確認背景工作完成。CPU 本身沒有改成 pipeline；三階段 pipeline 位於獨立加速器的 DOT4 運算路徑。

```
                     指令記憶體 16 KiB
                            │
                            ▼
                 Fault-V 多周期 CPU
                 │          │
          custom_exec     資料存取
          十二條指令         │
          四個乘法器         ├────────→ UART／GPIO
                            ├────────→ DMA／加速器設定暫存器
                            │
                         Master 0
                            │
       DMA ── Master 1 ──→ Round-robin 仲裁器 ←── Master 2 ── 向量加速器
                            │                              │
                      一筆未完成交易                  三階段 DOT4 pipeline
                            │                         四個獨立乘法器
                      記憶體位址選擇
                      ┌─────┴─────┐
                 主資料 RAM     Scratchpad
                   16 KiB        4 KiB
```

| 項目 | 架構決定 | 用途／限制 |
| --- | --- | --- |
| CPU | 32-bit、多周期、FSM、單一 clock | 保留基礎 RV32I 指令與既有錯誤停止方式 |
| CPU 自訂指令 | XFaultVDSP v1.1，十二條指令 | 指令觸發核心內的 `custom_exec` |
| DMA | word-copy，讀一個 word 再寫一個 word | 搬移資料；每次工作 1～1024 words |
| 獨立加速器 | N 組 packed signed INT8 DOT4 累加 | 從記憶體讀取兩組向量，寫出一個 INT32 |
| Scratchpad | 4 KiB、1024 × 32-bit | 軟體明確管理的 RAM；沒有 cache tag 或自動替換 |
| 記憶體仲裁 | CPU、DMA、加速器三個來源，round-robin | 主 RAM 與 scratchpad 共用一個仲裁後介面 |
| 未完成交易 | 仲裁後最多一筆 | 一筆回應完成後才接受下一筆 |
| 工作通知 | 輪詢 BUSY／DONE／ERROR | 不新增中斷或 CSR |
| CPU 與引擎並行 | 引擎工作時 CPU 可執行其他指令 | CPU 不可存取正在被引擎使用的 buffer |
| CPU FENCE | 維持原本 CPU 存取排序語意 | 不代表等待 DMA／加速器完成；仍需讀狀態 |
| CPU 停止 | CPU 停止不取消背景工作 | 全域 reset 才會取消引擎與仲裁器的未完成工作 |

## 2．記憶體與周邊配置

| 範圍／基址 | 容量 | 內容 | 可存取來源 |
| --- | --- | --- | --- |
| `0x00000000～0x00003FFF` | 16 KiB | 指令記憶體 | CPU 取指介面 |
| `0x10000000～0x10003FFF` | 16 KiB | 主資料 RAM | CPU、DMA、加速器 |
| `0x10010000～0x10010FFF` | 4 KiB | Scratchpad RAM | CPU、DMA、加速器 |
| `0x20000000` | 1 word | 程式結果狀態 | CPU |
| `0x20000100` | UART 暫存器區 | TX 與狀態 | CPU |
| `0x20000200` | GPIO 暫存器區 | LED、switch 等 | CPU |
| `0x20000300～0x2000031F` | 8 words | DMA 設定／狀態 | CPU |
| `0x20000400～0x2000041F` | 8 words | 加速器設定／狀態 | CPU |

資料採 byte addressing、little-endian。CPU 對 scratchpad 使用既有 LB／LBU／LH／LHU／LW 與 SB／SH／SW；對齊要求與主 RAM 相同。DMA 與加速器只使用對齊的 32-bit word，不能存取指令記憶體或 MMIO。

兩種資料 RAM 都不因 reset 清零。FPGA 示範程式會自行準備輸入；ASIC 的記憶體巨集、程式載入及上電初始化仍需另選實作。

## 3．DMA 與加速器共用的設定介面

DMA 基址為 `0x20000300`，加速器基址為 `0x20000400`。以下 offset 相對各自基址。

| Offset | 名稱 | 存取 | 定義 |
| --- | --- | --- | --- |
| `+0x00` | CONTROL | R/W | 讀為 0；寫 0＝不動作，1＝START，2＝CLEAR |
| `+0x04` | STATUS | R | bit 0＝BUSY、bit 1＝DONE、bit 2＝ERROR；bits 15:8＝CAUSE；其他為 0 |
| `+0x08` | SRC_A | R/W | DMA 來源；加速器向量 A 起點 |
| `+0x0C` | SRC_B | R/W | 加速器向量 B 起點；DMA 保存但不使用此欄位 |
| `+0x10` | DST | R/W | DMA 目的區；加速器結果 word 位址 |
| `+0x14` | COUNT | R/W | DMA 搬移 word 數；加速器 DOT4 組數，範圍 1～1024 |
| `+0x18` | PROGRESS | R | DMA 已成功收到寫入回應的 word 數；加速器已驗證 tag 並累加的 DOT4 組數 |
| `+0x1C` | FAULT_ADDR | R | 記憶體讀寫錯誤位址；tag 錯誤記錄結果位址；描述設定錯誤為 0 |

設定寫入必須使用完整 SW，四個 byte enable 全為 1。BUSY 時任何寫入，包括 START、CLEAR、設定修改，均回覆 CPU bus error；讀取狀態及設定仍允許。只讀暫存器不可寫入，非法 CONTROL 值也回覆 bus error。

START 會檢查描述設定。設定不合法時，START 的 MMIO 交易仍正常完成，但工作不會發出記憶體請求，並回報 DONE＝1、ERROR＝1 與 CAUSE。這與「MMIO 存取本身不合法」造成 CPU 停止不同。

DONE／ERROR 保持至下一次 START 或 CLEAR。CLEAR 清除結果狀態、PROGRESS 與 FAULT_ADDR，保留描述設定。reset 則連描述設定一起清零。

| CAUSE | 名稱 | 觸發條件 |
| --- | --- | --- |
| 0 | OK | 沒有錯誤 |
| 1 | LENGTH | COUNT＝0 或大於 1024 |
| 2 | ALIGN | 使用的來源／目的位址未對齊 4 bytes |
| 3 | RANGE | 整個存取範圍超出主 RAM／scratchpad，或地址溢位 |
| 4 | OVERLAP | DMA 來源與目的重疊；或加速器輸出與任一輸入重疊 |
| 5 | CONFLICT | 新工作使用到另一個正在執行的引擎 buffer |
| 6 | READ | 記憶體讀取回應錯誤 |
| 7 | WRITE | 記憶體寫入回應錯誤 |
| 8 | TAG | 加速器收到的 pipeline tag 與預期次序不同 |

檢查優先順序為 LENGTH → ALIGN → RANGE → OVERLAP → CONFLICT。位址範圍採 33-bit 加法檢查尾端，避免 32-bit wrap-around 被誤判為合法。

## 4．DMA 資料路徑

```
設定 → 檢查 → READ_REQ → READ_WAIT → 保存一個 word
                                   │
             下一個 word ← WRITE_WAIT ← WRITE_REQ
                 │             │
                 └─ 未完成     └─ 最後一個完成 → DONE
```

DMA 按來源及目的位址遞增搬移。來源與目的可以位於不同 RAM，也可以是同一 RAM 中不重疊的區域；不提供 memmove 的重疊搬移語意。每次讀取成功後才發出相應寫入，寫入成功回應後才增加 PROGRESS。

發生 bus error 即停止工作。已完成的寫入不回復；記憶體若已接受寫入、之後才回覆錯誤，該 word 也可能已改變。因此 PROGRESS 是成功回應數，不能當作交易回滾紀錄。

## 5．向量加速器與 DOT4 pipeline

加速器使用以下運算語意：

```
result = Σ(i=0..COUNT-1) Σ(k=0..3)
         signed8(A[i][8k +: 8]) × signed8(B[i][8k +: 8])
```

每個 word 含四個 INT8 lane，最低位元組為 lane 0。每組 DOT4 範圍為 −65024～65536；COUNT ≤1024 時，總和範圍為 −66584576～67108864，可完整保存於 signed INT32，不使用飽和或量化。

| 階段 | 保存內容 | 位寬／行為 |
| --- | --- | --- |
| Stage 1 | 四個 lane 乘積與 tag | 各乘積 signed 16-bit；四個獨立乘法器 |
| Stage 2 | 兩組成對加總與 tag | 兩個 signed 17-bit sum |
| Stage 3 | 最終 DOT4 與 tag | signed 18-bit sum，符號擴展成 32-bit |
| 輸出累加 | 經 tag 檢查的 DOT4 結果 | 累加於 32-bit 暫存器，完成後寫出一個 word |

Pipeline 每級都有 valid／ready，後端不接受結果時會保存資料與 tag，並把背壓往前傳。連續輸入且無背壓時，可每個 clock 接收一組；從輸入握手至輸出握手的最短延遲為三個 clock。這是運算 pipeline 的能力。

整個加速器還需要兩次串行記憶體讀取來取得每組 A、B，並與 CPU／DMA 仲裁，因此整機吞吐量不能直接寫成「每拍完成一組 DOT4」。

加速器將每組輸入編上遞增的 16-bit tag。輸出 tag 必須等於 PROGRESS 才能累加；錯誤 tag 會停止工作、禁止寫出結果，並處理已發出的記憶體交易後釋放引擎。

## 6．仲裁、buffer 所有權與 reset

| 情況 | 處理方式 |
| --- | --- |
| 三個來源要求資料 RAM | 依 round-robin 選擇一個來源 |
| 後端尚未接受請求 | 保存 grant；該來源必須保持請求資料不變 |
| 記憶體正在處理交易 | 保存 owner，回應只交給該來源 |
| 回應被消費 | 釋放交易，下一輪優先從 owner 的下一個來源開始 |
| DMA 工作中 | 鎖定整個來源與目的範圍 |
| 加速器工作中 | 鎖定 A、B 輸入範圍及結果 word |
| CPU 存取被鎖定的範圍 | 回覆 bus error，CPU 按既有 Load／Store access fault 停止 |
| 引擎之間 buffer 重疊 | 第二個 START 拒絕，CAUSE＝CONFLICT；第一個工作繼續 |
| 引擎之間 buffer 不重疊 | 可同時執行，仍共用仲裁器與 RAM 介面 |
| 全域 reset | CPU、設定介面、引擎、pipeline、仲裁器未完成狀態清除；RAM 內容保留 |

Buffer 鎖定採保守規則，讀取來源也鎖定；兩個引擎即使只想讀取同一段資料也不能同時啟動。加速器單一工作內 A、B 可以重疊，因為兩者皆只讀，但結果 word 必須與輸入分離。

reset 不會回復已發生的記憶體寫入。軟體重啟時必須重新設定引擎、準備輸入並重新執行工作。

## 7．軟體使用順序

1. 準備輸入、確認位址對齊及 buffer 不重疊。
2. 寫入 SRC_A、SRC_B、DST、COUNT。
3. 寫 CONTROL＝1 啟動。
4. 在不接觸被鎖定 buffer 的前提下，執行其他 CPU 工作。
5. 輪詢 STATUS，直到 BUSY＝0。
6. 確認 DONE＝1、ERROR＝0，再讀取目的資料；若 ERROR＝1，讀取 CAUSE、FAULT_ADDR 及 PROGRESS。

典型資料流程：主 RAM 輸入 → DMA 搬至 scratchpad → 等待 DMA 完成 → 啟動點積加速器 → CPU 執行其他工作 → 等待加速器完成 → 讀取 INT32 結果。

## 8．RTL 模組與 FPGA 整合

| 模組／檔案 | 責任 |
| --- | --- |
| `a_stream_pkg.sv` | 記憶體範圍、錯誤代碼、範圍及重疊檢查函式 |
| `fault_v_job_regs.sv` | 共用 MMIO 設定、讀回、START／CLEAR、bus response |
| `fault_v_dma.sv` | 描述檢查、串行讀寫、搬移進度與錯誤停止 |
| `fault_v_dot_pipeline.sv` | 四乘法器、三階段 DOT4、valid／ready／tag |
| `fault_v_accelerator.sv` | 向量讀取、pipeline 發送／累加、結果寫入 |
| `fault_v_mem_arbiter.sv` | 三來源 round-robin、保留 grant 與 response owner |
| `fault_v_soc.sv` | 新介面解碼、buffer 鎖定、RAM 選擇及模組整合 |
| `fault_v_payload.sv` | Z2 reset、ARM run 控制、LED、UART、debug 狀態 |

Z2 使用 50 MHz 單一核心 clock。CPU 自訂執行單元與獨立加速器各使用四個乘法器。Fault-V UART TX 接到 PL AXI UARTLite 的 RX，板上 ARM 讀取後透過網路回傳；此路徑不需要外接 USB-to-UART 轉接器。

ASIC 版本仍需選定 RAM 巨集、製程、clock／reset、測試介面與 I/O。FPGA 的 BRAM／DSP 映射是原型平台的實作，ASIC 合成時須使用相應元件庫與記憶體方案。