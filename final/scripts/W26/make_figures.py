"""Competition report figures (WSL python3 + matplotlib). Numbers are read from the PPA result JSON files.
Writes w26/competition/figures/fig_*.png."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'w26/competition/figures'
OUT.mkdir(parents=True, exist_ok=True)
for f in ('/mnt/c/Windows/Fonts/msjh.ttc', '/mnt/c/Windows/Fonts/msjhbd.ttc'):
    font_manager.fontManager.addfont(f)
plt.rcParams['font.family'] = 'Microsoft JhengHei'
plt.rcParams['axes.unicode_minus'] = False

INK, INK2, MUTED, GRID, AXIS = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7'
BLUE, ORANGE, AQUA, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
h0 = json.loads((ROOT / 'ppa/formal_h0/reports/H0_PPA_result.json').read_text())
h1 = json.loads((ROOT / 'ppa/formal_h1/reports/H1_PPA_result.json').read_text())
DPI = 300


def clean(ax):
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(AXIS)
    ax.tick_params(colors=INK2, length=0)


# ---- Fig: DOT64 rv32i vs custom (two panels, one measure each; same hardware H0) ----
p = h0['power']
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2), dpi=DPI)
panels = [('執行週期數', [p['dot64_rv32i']['cycles'], p['dot64_custom']['cycles']], '{:,.0f}', '週期'),
          ('總能量（µJ）', [p['dot64_rv32i']['energy_nJ'] / 1000, p['dot64_custom']['energy_nJ'] / 1000], '{:.2f}', 'µJ')]
labels = ['RV32I\n（軟體乘法）', '自訂指令\nDOT4']
for ax, (title, vals, fmt, unit) in zip(axes, panels):
    bars = ax.barh([1, 0], vals, color=[ORANGE, BLUE], height=0.55, edgecolor='white', linewidth=2)
    ax.set_yticks([1, 0], labels, fontsize=8.5, color=INK)
    ax.set_title(title, fontsize=9.5, color=INK, loc='left', fontweight='bold')
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    clean(ax)
    ax.tick_params(axis='x', labelsize=7.5)
    ax.set_xlim(0, max(vals) * 1.32)
    for b, v in zip(bars, vals):
        ax.text(b.get_width() + max(vals) * 0.02, b.get_y() + b.get_height() / 2, fmt.format(v) + ' ' + unit,
                va='center', fontsize=8, color=INK)
    ratio = vals[0] / vals[1]
    ax.text(max(vals) * 1.30, 0.5, f'{ratio:.1f}×', ha='right', va='center', fontsize=13, color=BLUE, fontweight='bold')
fig.tight_layout(w_pad=2.5)
fig.savefig(OUT / 'fig_dot64.png', facecolor='white')
plt.close(fig)

# ---- Fig: power breakdown, mixed workload, H0 and H1 (stacked, 2 px gaps) ----
groups = [('SRAM', BLUE), ('時脈網路', ORANGE), ('暫存器', AQUA), ('組合邏輯', YELLOW)]
def parts(r):
    g = r['power']['mixed']['group_total_mW']
    return [r['power']['mixed']['sram_mW'], g['Clock'], g['Sequential'], g['Combinational']]
fig, ax = plt.subplots(figsize=(7.0, 1.9), dpi=DPI)
for y, (name, r) in zip([1, 0], [('H0', h0), ('H1', h1)]):
    left = 0
    vals = parts(r)
    for (lab, col), v in zip(groups, vals):
        ax.barh(y, v, left=left, color=col, height=0.55, edgecolor='white', linewidth=2)
        if v > 2.0:
            ax.text(left + v / 2, y, f'{v:.2f}', ha='center', va='center', fontsize=7.5,
                    color='#0b0b0b' if col == YELLOW else 'white')
        left += v
    ax.text(left + 0.4, y, f'{left:.2f} mW', va='center', fontsize=8, color=INK)
ax.set_yticks([1, 0], ['H0', 'H1'], fontsize=9, color=INK)
ax.set_xlim(0, 38)
ax.set_xlabel('功耗（mW，mixed 工作負載，25 MHz、TT、nominal RC）', fontsize=8, color=INK2)
ax.xaxis.grid(True, color=GRID, linewidth=0.6)
ax.set_axisbelow(True)
clean(ax)
ax.tick_params(axis='x', labelsize=7.5)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in groups]
ax.legend(handles, [g for g, _ in groups], ncol=4, fontsize=7.5, frameon=False, loc='upper left',
          bbox_to_anchor=(0, 1.32))
fig.tight_layout()
fig.savefig(OUT / 'fig_power.png', facecolor='white')
plt.close(fig)


# ---- block diagram helpers ----
def box(ax, x, y, w, h, text, fc='#f3f6fb', ec='#2a78d6', fs=8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08', fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs, color=INK,
            fontweight='bold' if bold else 'normal', linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, both=False):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='<|-|>' if both else '-|>', mutation_scale=9,
                                 color=INK2, lw=0.9, shrinkA=1, shrinkB=1))


# ---- Fig: SoC architecture ----
fig, ax = plt.subplots(figsize=(7.0, 3.5), dpi=DPI)
ax.set_xlim(0, 14); ax.set_ylim(0, 7.2); ax.axis('off')
# column A: loader -> instruction SRAM; column B: CPU / arbiter / data SRAM; column C: custom unit, DMA + DOT4, scratchpad
box(ax, 0.2, 4.6, 2.6, 1.7, 'UART RX\n開機載入器\nCRC-32 檢查', fc='#fdf1ec', ec=ORANGE, fs=7.8)
box(ax, 3.4, 4.6, 4.2, 1.7, 'RV32I 多週期 CPU\n32×32 暫存器檔、FSM 控制', fs=8.5, bold=True)
box(ax, 8.4, 4.6, 3.0, 1.7, '自訂執行單元\n12 條自訂指令\nDOT4／DOT8／MAC16\nQNT8／RQNT8 等', fc='#e8f6f0', ec=AQUA, fs=7.2)
box(ax, 3.4, 2.5, 4.2, 1.3, 'Round-robin 記憶體仲裁器\nCPU／DMA／加速器', fs=7.8)
box(ax, 8.4, 3.25, 3.0, 0.75, 'DMA 搬移引擎', fs=7.4)
box(ax, 8.4, 2.35, 3.0, 0.75, 'DOT4 加速器', fc='#e8f6f0', ec=AQUA, fs=7.4)
box(ax, 0.2, 0.3, 3.0, 1.5, '指令 SRAM\n16 KiB（8 × 2 KiB）', fc='#eef3fb', fs=7.8)
box(ax, 4.0, 0.3, 3.2, 1.5, '資料 SRAM\n16 KiB（8 × 2 KiB）', fc='#eef3fb', fs=7.8)
box(ax, 8.4, 0.3, 3.0, 1.5, 'Scratchpad\n4 KiB（2 × 2 KiB）', fc='#eef3fb', fs=7.8)
box(ax, 11.95, 2.35, 1.85, 3.95, 'MMIO\n\nUART TX\nGPIO\n執行狀態\nDMA／加速器\n控制暫存器', fc='#f6f5f1', ec=MUTED, fs=7.2)
arrow(ax, 2.8, 5.45, 3.4, 5.45)
ax.text(2.85, 5.6, '啟動', fontsize=6.3, color=INK2)
arrow(ax, 1.2, 4.6, 1.2, 1.8)
ax.text(1.3, 3.2, '載入程式\n(boot write)', fontsize=6.3, color=INK2)
arrow(ax, 3.5, 4.6, 2.7, 1.8)
ax.text(2.55, 3.75, '取指', fontsize=6.3, color=INK2)
arrow(ax, 7.6, 5.45, 8.4, 5.45, both=True)
arrow(ax, 5.5, 4.6, 5.5, 3.8, both=True)
arrow(ax, 8.4, 3.6, 7.6, 3.4, both=True)
arrow(ax, 8.4, 2.7, 7.6, 2.9, both=True)
arrow(ax, 5.6, 2.5, 5.6, 1.8, both=True)
arrow(ax, 7.6, 2.55, 8.7, 1.8, both=True)
ax.plot([5.5, 5.5, 12.85], [6.3, 6.75, 6.75], color=INK2, lw=0.9)
arrow(ax, 12.85, 6.75, 12.85, 6.3)
ax.text(9.6, 6.85, 'CPU 資料介面（MMIO）', fontsize=6.3, color=INK2)
arrow(ax, 11.4, 3.6, 11.95, 3.6, both=True)
arrow(ax, 11.4, 2.7, 11.95, 2.7, both=True)
ax.text(0.2, 7.0, 'fault_v_asic_top（SKY130A、25 MHz、核心 1.8 V）', ha='left', fontsize=8.5, color=INK, fontweight='bold')
fig.savefig(OUT / 'fig_arch.png', facecolor='white', bbox_inches='tight', pad_inches=0.03)
plt.close(fig)

# ---- Fig: design flow ----
steps = ['RTL 設計\n與模擬', '邏輯合成\nYosys', '佈局規劃\nSRAM／電源', '擺放\n時脈樹',
         '繞線\n修時序', '實體驗證\nDRC／LVS', '時序電源\nSTA／IR', 'PPA\n功耗分析']
fig, ax = plt.subplots(figsize=(7.0, 1.0), dpi=DPI)
ax.set_xlim(0, 8 * 1.75); ax.set_ylim(0.15, 1.35); ax.axis('off')
for i, s in enumerate(steps):
    x = i * 1.75 + 0.05
    box(ax, x, 0.25, 1.5, 1.0, s, fs=7.0, fc='#eef3fb' if i < 5 else '#e8f6f0', ec=BLUE if i < 5 else AQUA)
    if i:
        arrow(ax, x - 0.25, 0.75, x, 0.75)
fig.savefig(OUT / 'fig_flow.png', facecolor='white', bbox_inches='tight', pad_inches=0.03)
plt.close(fig)
print('FIGURES_DONE', sorted(p.name for p in OUT.glob('fig_*.png')))
