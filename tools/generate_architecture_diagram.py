from PIL import Image, ImageDraw, ImageFont
import os

# Output path
out_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'architecture_diagram.png')

W, H = 1200, 700
img = Image.new('RGB', (W, H), (255, 255, 255))
d = ImageDraw.Draw(img)

# Try to load a common font; fall back to default
try:
    font = ImageFont.truetype('arial.ttf', 16)
    title_font = ImageFont.truetype('arial.ttf', 20)
except Exception:
    font = ImageFont.load_default()
    title_font = font

# Helper to draw a box with text
def draw_box(x, y, w, h, text, fill=(240,240,255), outline=(0,0,0)):
    d.rectangle([x, y, x+w, y+h], fill=fill, outline=outline)
    # center text
    lines = text.split('\n')
    # compute text sizes using textbbox for Pillow >=10 compatibility
    bboxes = [d.textbbox((0, 0), line, font=font) for line in lines]
    heights = [bbox[3] - bbox[1] for bbox in bboxes]
    widths = [bbox[2] - bbox[0] for bbox in bboxes]
    total_h = sum(heights)
    cur_y = y + (h - total_h) / 2
    for line, w_line, h_line in zip(lines, widths, heights):
        tw = w_line
        d.text((x + (w - tw)/2, cur_y), line, fill=(0,0,0), font=font)
        cur_y += h_line

# Title
d.text((20, 10), 'Arquitectura: CyberMind (FastAPI monolítica modular)', fill=(0,0,0), font=title_font)

# Boxes coordinates
pad = 40
client_box = (W//2 - 120, 60, 240, 60)
api_box = (W//2 - 160, 160, 320, 70)
controllers_box = (W//4 - 140, 270, 280, 120)
services_box = (W//2 - 140, 270, 280, 120)
background_box = (3*W//4 - 140, 270, 280, 120)
db_box = (W//2 - 140, 440, 280, 80)

# Draw boxes
draw_box(*client_box, 'Clientes\n(Front-end\n/ API Consumers)')
draw_box(*api_box, 'FastAPI\n(app = FastAPI(...))')

# Controllers / Services / Background
draw_box(*controllers_box, 'Controllers\n(routers)\n`src/app/controllers`')
draw_box(*services_box, 'Services / Utils\n`src/app/services`\n`src/app/utils`')
draw_box(*background_box, 'Background Workers\nScrapy / spaCy / LLM\n(hilos + asyncio)')

# DB box
draw_box(*db_box, 'PostgreSQL\n(asyncpg pool)\n`app.state.pool`', fill=(240,255,240))

# Arrows: helper
def arrow(x1, y1, x2, y2, w=3, color=(0,0,0)):
    d.line((x1, y1, x2, y2), fill=color, width=w)
    # simple arrowhead
    ax = x2 - x1
    ay = y2 - y1
    import math
    ang = math.atan2(ay, ax)
    sz = 12
    a1 = ang + math.radians(160)
    a2 = ang - math.radians(160)
    d.line((x2, y2, x2 + sz*math.cos(a1), y2 + sz*math.sin(a1)), fill=color, width=w)
    d.line((x2, y2, x2 + sz*math.cos(a2), y2 + sz*math.sin(a2)), fill=color, width=w)

# From clients to API
arrow(client_box[0]+client_box[2]/2, client_box[1]+client_box[3], api_box[0]+api_box[2]/2, api_box[1])
# API to Controllers/Services/Background
arrow(api_box[0]+api_box[2]/2 - 60, api_box[1]+api_box[3], controllers_box[0]+controllers_box[2]/2, controllers_box[1])
arrow(api_box[0]+api_box[2]/2, api_box[1]+api_box[3], services_box[0]+services_box[2]/2, services_box[1])
arrow(api_box[0]+api_box[2]/2 + 60, api_box[1]+api_box[3], background_box[0]+background_box[2]/2, background_box[1])

# Services and Background to DB
arrow(services_box[0]+services_box[2]/2, services_box[1]+services_box[3], db_box[0]+db_box[2]/2 - 30, db_box[1])
arrow(background_box[0]+background_box[2]/2, background_box[1]+background_box[3], db_box[0]+db_box[2]/2 + 30, db_box[1])

# Footer note
note = 'Generado automáticamente: `tools/generate_architecture_diagram.py` → `outputs/architecture_diagram.png`'
d.text((20, H-30), note, fill=(80,80,80), font=font)

img.save(out_path)
print(f'Archivo generado: {out_path}')
