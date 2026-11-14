# Fault-V ASIC 平面規劃與電源架構

## 1．實作範圍

Floorplan 決定 SRAM、標準元件區域與對外訊號腳的位置；Power Plan 建立供應電源與接地的金屬網路。

CPU、DSP 自訂指令、DMA、加速器、UART 與 GPIO 的功能維持原本設計。SRAM 先固定位置，功能性標準元件再放入剩餘的合法 placement rows。

| 項目 | 設計 |
| --- | --- |
| 製程與標準元件庫 | SKY130A、`sky130_fd_sc_hd` |
| 電源域 | 單一數位核心電源域，名義電壓 1.8 V |
| Clock | 外部 25 MHz、週期 40 ns；時脈樹另行建立 |
| 實作區外框 | 2500 × 3300 µm，面積 8.25 mm² |
| 標準元件 core 範圍 | 左下角 (80.04, 81.60)，右上角 (2419.60, 3217.76) µm |
| Core 面積 | 約 7.33723 mm² |
| SRAM | 18 顆，每顆 512 × 32-bit＝2 KiB |
| 記憶體容量 | IMEM 16 KiB＋DMEM 16 KiB＋Scratch 4 KiB |
| SRAM 單顆尺寸 | 683.10 × 416.54 µm |
| SRAM 合計面積 | 約 5.12169 mm² |
| 邏輯區 | 使用 SRAM 外的合法 rows；不以空白區域全部都能放置元件計算 |
| 晶片邊界 | 此外框是核心實作邊界；尚未包含 pad ring、ESD 與封裝整合 |

這個面積不能直接當成最終含 I/O pads 的晶片面積。

## 2．SRAM 配置

所有 SRAM 使用 R0／N 方向，不旋轉。座標原點在實作區左下角，單位為 µm。

三欄的左下角 x 分別為 120、900、1680；六列的左下角 y 如下。

| 每列 y | 左欄：x＝120 | 中欄：x＝900 | 右欄：x＝1680 |
| --- | --- | --- | --- |
| 2720 | DMEM bank 7 | Scratch bank 0 | Scratch bank 1 |
| 2200 | DMEM bank 4 | DMEM bank 5 | DMEM bank 6 |
| 1680 | DMEM bank 1 | DMEM bank 2 | DMEM bank 3 |
| 1160 | IMEM bank 6 | IMEM bank 7 | DMEM bank 0 |
| 640 | IMEM bank 3 | IMEM bank 4 | IMEM bank 5 |
| 120 | IMEM bank 0 | IMEM bank 1 | IMEM bank 2 |

- 相鄰 SRAM 邊界間距：水平方向 96.90 µm、垂直方向 103.46 µm。
- 每顆 SRAM 四周保留 20 µm halo，不放功能性標準元件。
- 扣除兩側 halo 後，兩顆 SRAM 間剩餘的幾何寬度分別為 56.90／63.46 µm；實際可走線容量還要扣除電源線、阻擋與其他設計規則。
- 這是供後續 placement、CTS 與 routing 使用的初版配置；是否需要調整，以實際擁塞與時序結果決定。

實際 instance 名稱格式：

```text
u_soc.u_imem.banks[0].u_sram
u_soc.u_dmem.banks[0].u_sram
u_soc.u_scratch.banks[0].u_sram
```

## 3．電源網路

頂層電源網為 `VPWR`，接地網為 `VGND`。標準元件與 SRAM 使用相同電源域。

| 部分 | 金屬層／接線 | 幾何與用途 |
| --- | --- | --- |
| 標準元件電源軌 | met1 | 線寬 0.48 µm，沿合法 rows 建立 |
| 垂直主幹 | met4 | 線寬 3 µm；成組 pitch 150 µm；組內線距 3 µm；設定 offset 30 µm |
| 水平主幹 | met5 | 線寬 3 µm；成組 pitch 150 µm；組內線距 3 µm；設定 offset 35 µm |
| 核心電源環 | 垂直 met4＋水平 met5 | 線寬 5 µm、電源／接地間距 5 µm、core offset 10 µm，必須位於實作區外框內 |
| SRAM 電源 | `vccd1 → VPWR` | SRAM 既有 met4 電源腳透過 via 接到上層 met5 網路 |
| SRAM 接地 | `vssd1 → VGND` | SRAM 既有 met4 接地腳透過 via 接到上層 met5 網路 |
| 標準元件供電／井接點 | `VPWR／VPB → VPWR`；`VGND／VNB → VGND` | 供電與 well tie 接線 |
| Well tap | `sky130_fd_sc_hd__tapvpwrvgnd_1` | 依 PDK 規則與可用 rows 插入 |
| Row endcap | `sky130_fd_sc_hd__decap_3` | 放在切割後的 row 兩端，依此 PDK 流程使用 |

Pitch 是整組電源／接地線的重複距離，不是每兩條相鄰線的距離。Offset 是傳給 PDN 工具的設定值；實際金屬位置以輸出的 ODB／DEF 為準。

上述線寬與間距是初版電源幾何配置，仍須依後續負載、IR drop、電遷移與繞線結果調整。

電源主幹只在同一電源網的合法交會處建立 via；巨集上層供電方式依 SRAM pin layer 接到更高一層。[LibreLane PDN 說明](https://librelane.readthedocs.io/en/latest/usage/pdn.html)、[OpenROAD PDN 指令](https://openroad.readthedocs.io/en/latest/main/src/pdn/README.html)。

## 4．核心訊號腳配置

| 邊界 | 訊號 | Bit 數 |
| --- | --- | --- |
| 西側 | clk、reset_n、uart_rx、uart_tx、running、boot_error | 6 |
| 南側 | gpio_in[1:0]、gpio_out[3:0] | 6 |
| 東側 | fault_pc[31:0]、fault_addr[31:0] | 64 |
| 北側 | debug_status[31:0] | 32 |
| 合計 | 功能性訊號 | 108 |

東西兩側使用 met3，南北兩側使用 met2。VPWR／VGND 另外以電源網路的 block pins 提供整合接點。

這些是 ASIC 核心邊界上的金屬 pin，和 FPGA 板子的 pin assignment、封裝接腳及 I/O pad cell 不同。獨立晶片仍需加入 I/O、ESD、電源輸入與封裝設計。

## 5．後續實體設計的交接

後續以這份固定 SRAM 位置、已切割 rows、電源網路與訊號腳配置為起點，擺放功能性標準元件，再建立時脈樹與訊號繞線。

Clock／reset 的電路語意及 40 ns 約束沿用既有設計；PDN 建立不代表時序、IR drop、電遷移、DRC、LVS 或 antenna 已完成簽核。

![Fault-V Floorplan 與 PDN](figures/Floorplan_PDN.png)
