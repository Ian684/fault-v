"""H0 / H1 metal-layer images side by side at the same scale (1.28 px/um source), SRAM banks labelled. WSL python3 + PIL."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / 'w26/competition/figures'
PX = 1.28                      # source pixels per um (3200 px / 2500 um)
W, H = 683.1, 416.54           # SRAM macro size (um)
FONT = '/mnt/c/Windows/Fonts/msjhbd.ttc'


def banks(cols, rows):
    """Bank order of both floorplans: imem 0-7, dmem 0-7, scratch 0-1 filling a 3 x 6 grid row by row from the bottom."""
    names = [f'I{i}' for i in range(8)] + [f'D{i}' for i in range(8)] + ['S0', 'S1']
    return [(n, cols[k % 3], rows[k // 3]) for k, n in enumerate(names)]


designs = [
    ('H0', 'h0_layout_metal.png', 3300, banks([120, 900, 1680], [120, 640, 1160, 1680, 2200, 2720]),
     'H0　2500 × 3300 µm（8.250 mm²）'),
    ('H1', 'h1_layout_metal.png', 3217, banks([120, 893, 1666], [120, 632, 1144, 1656, 2168, 2680]),
     'H1　2470 × 3217 µm（7.946 mm²，縮小 3.7%）'),
]
scale = 0.30
label_font = ImageFont.truetype(FONT, 46)
cap_font = ImageFont.truetype(FONT, 44)
tiles = []
for name, png, die_h, bank_list, caption in designs:
    im = Image.open(FIG / png).convert('RGB')
    d = ImageDraw.Draw(im)
    for label, x, y in bank_list:
        cx, cy = (x + W / 2) * PX, (die_h - (y + H / 2)) * PX
        colour = {'I': '#ffd166', 'D': '#7fe3ff', 'S': '#b6f09c'}[label[0]]
        d.text((cx, cy), label, font=ImageFont.truetype(FONT, 150), fill=colour, anchor='mm',
               stroke_width=8, stroke_fill='#000000')
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    tiles.append((im, caption))
gap, margin, cap_h = 60, 30, 80
width = sum(t.width for t, _ in tiles) + gap + 2 * margin
height = max(t.height for t, _ in tiles) + cap_h + 2 * margin + 70
canvas = Image.new('RGB', (width, height), 'white')
d = ImageDraw.Draw(canvas)
x = margin
base = margin + max(t.height for t, _ in tiles)
for t, caption in tiles:
    canvas.paste(t, (x, base - t.height))
    d.text((x + t.width / 2, base + 20), caption, font=cap_font, fill='#0b0b0b', anchor='mt')
    x += t.width + gap
d.text((margin, height - 50), 'I0–I7：指令 SRAM　D0–D7：資料 SRAM　S0–S1：Scratchpad（每顆 2 KiB；只顯示 met1–met5 金屬層）',
       font=ImageFont.truetype(FONT, 34), fill='#52514e', anchor='lm')
canvas.save(FIG / 'fig_layout.png', dpi=(300, 300))
print('LAYOUT_FIG', canvas.size)
