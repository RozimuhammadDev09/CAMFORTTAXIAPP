import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUTPUT_DIR = r"C:\Users\rozim\Downloads\screenshots"
ASSETS_DIR = r"d:\Loyihalar va darslar\Amaliyotlar\CAMFORT TAXI\camfort_taxi_app\assets\images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors
C_GOLD = (212, 175, 55)
C_GOLD_BRIGHT = (245, 197, 24)
C_GOLD_BG = (45, 38, 15)
C_BG_DARK = (13, 16, 22)
C_POSTER_TOP = (16, 18, 26)
C_POSTER_BOT = (8, 10, 14)
C_PHONE_FRAME = (28, 32, 42)
C_PHONE_BORDER = (55, 62, 78)
C_APP_BG = (15, 18, 25)
C_CARD_BG = (24, 28, 38)
C_CARD_BORDER = (42, 48, 64)
C_TEXT_WHITE = (255, 255, 255)
C_TEXT_MUTED = (155, 165, 180)
C_GREEN = (34, 197, 94)
C_BLUE = (59, 130, 246)
C_RED = (239, 68, 68)

# Fonts
def get_font(size, bold=False):
    font_path = "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(font_path, size)

def round_corners(image, radius):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius=radius, fill=255)
    result = image.copy().convert("RGBA")
    result.putalpha(mask)
    return result

def create_base_poster(width=1080, height=1920, badge="", title="", subtitle=""):
    poster = Image.new("RGB", (width, height), C_POSTER_TOP)
    draw = ImageDraw.Draw(poster)
    
    # Vertical gradient
    for y in range(height):
        ratio = y / height
        r = int(C_POSTER_TOP[0] * (1 - ratio) + C_POSTER_BOT[0] * ratio)
        g = int(C_POSTER_TOP[1] * (1 - ratio) + C_POSTER_BOT[1] * ratio)
        b = int(C_POSTER_TOP[2] * (1 - ratio) + C_POSTER_BOT[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Subtle ambient glow behind phone
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([width//2 - 400, 350, width//2 + 400, 1150], fill=(212, 175, 55, 22))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    poster.paste(glow, (0, 0), glow)

    # Re-draw for text
    draw = ImageDraw.Draw(poster)

    # Top Badge
    if badge:
        f_badge = get_font(26, bold=True)
        bbox = f_badge.getbbox(badge)
        bw = bbox[2] - bbox[0] + 36
        bh = bbox[3] - bbox[1] + 18
        bx = (width - bw) // 2
        by = 55
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=C_GOLD_BG, outline=C_GOLD, width=2)
        draw.text((bx + 18, by + 8), badge, font=f_badge, fill=C_GOLD_BRIGHT)

    # Main Title
    f_title = get_font(52, bold=True)
    t_bbox = f_title.getbbox(title)
    tx = (width - (t_bbox[2] - t_bbox[0])) // 2
    draw.text((tx, 125), title, font=f_title, fill=C_TEXT_WHITE)

    # Subtitle
    f_sub = get_font(28, bold=False)
    s_bbox = f_sub.getbbox(subtitle)
    sx = (width - (s_bbox[2] - s_bbox[0])) // 2
    draw.text((sx, 195), subtitle, font=f_sub, fill=C_TEXT_MUTED)

    return poster

def draw_phone_frame(poster, screen_content):
    # Phone dimensions: 860 width x 1620 height positioned at center-bottom
    px = 110
    py = 270
    pw = 860
    ph = 1650
    radius = 56

    # Shadow
    shadow = Image.new("RGBA", poster.size, (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([px - 10, py + 15, px + pw + 10, py + ph + 25], radius=radius + 4, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(25))
    poster.paste(shadow, (0, 0), shadow)

    # Outer metallic bezel
    draw = ImageDraw.Draw(poster)
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=radius, fill=C_PHONE_FRAME, outline=C_PHONE_BORDER, width=4)

    # Inner Screen container (820 width x 1580 height)
    sx = px + 20
    sy = py + 20
    sw = pw - 40
    sh = ph - 40

    # Resize screen content to fit
    resized_screen = screen_content.resize((sw, sh), Image.Resampling.LANCZOS)
    rounded_screen = round_corners(resized_screen, radius - 16)
    poster.paste(rounded_screen, (sx, sy), rounded_screen)

    # Top speaker & Dynamic Island pill
    pill_w = 180
    pill_h = 28
    pill_x = px + (pw - pill_w) // 2
    pill_y = py + 28
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=14, fill=(10, 12, 16))
    draw.ellipse([pill_x + pill_w - 36, pill_y + 6, pill_x + pill_w - 20, pill_y + 22], fill=(20, 24, 34))

    return poster

def create_base_app_screen(w=820, h=1580):
    screen = Image.new("RGB", (w, h), C_APP_BG)
    draw = ImageDraw.Draw(screen)

    # Status Bar
    f_status = get_font(20, bold=True)
    draw.text((40, 24), "12:00", font=f_status, fill=C_TEXT_WHITE)
    # Status bar icons text (5G, WiFi, Battery)
    draw.text((w - 130, 24), "5G  ●  100%", font=get_font(18, bold=True), fill=C_TEXT_WHITE)

    return screen, draw

def draw_bottom_nav(screen, active_idx=2):
    w, h = screen.size
    draw = ImageDraw.Draw(screen)
    nav_h = 110
    nav_y = h - nav_h

    draw.rectangle([0, nav_y, w, h], fill=(18, 22, 30))
    draw.line([(0, nav_y), (w, nav_y)], fill=C_CARD_BORDER, width=1)

    items = [
        ("Zakazlarim", "📋"),
        ("Zakaz berish", "➕"),
        ("Asosiy", "🚕"),
        ("Yo'nalishlar", "🛣"),
        ("Profil", "👤"),
    ]

    item_w = w // 5
    f_nav = get_font(15, bold=True)
    f_icon = get_font(24, bold=True)

    for i, (label, icon) in enumerate(items):
        cx = i * item_w + item_w // 2
        is_active = (i == active_idx)

        if i == 2: # Central floating gold button
            btn_r = 34
            cy = nav_y + 40
            draw.ellipse([cx - btn_r, cy - btn_r, cx + btn_r, cy + btn_r], fill=C_GOLD, outline=(255, 230, 120), width=2)
            draw.text((cx - 15, cy - 18), "🚕", font=get_font(26), fill=(0, 0, 0))
            draw.text((cx - 24, nav_y + 82), label, font=f_nav, fill=C_GOLD_BRIGHT)
        else:
            color = C_GOLD if is_active else C_TEXT_MUTED
            draw.text((cx - 12, nav_y + 22), icon, font=f_icon, fill=color)
            bbox = f_nav.getbbox(label)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw // 2, nav_y + 68), label, font=f_nav, fill=color)

# -------------------------------------------------------------
# SCREEN 1: HOME SCREEN
# -------------------------------------------------------------
def make_screenshot_1():
    poster = create_base_poster(
        badge="★ RESPUBLIKA BO'YICHA 1144",
        title="CAMFORT TAXI 1144",
        subtitle="Vodiy — Toshkent va Shaharlararo Qulay Taxi"
    )
    screen, draw = create_base_app_screen()
    w, _ = screen.size

    # Top App Bar
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(logo_path):
        logo_img = Image.open(logo_path).resize((50, 50), Image.Resampling.LANCZOS)
        screen.paste(logo_img, (35, 75), logo_img.convert("RGBA"))
    
    draw.text((95, 82), "CAMFORT TAXI 1144", font=get_font(26, bold=True), fill=C_GOLD_BRIGHT)

    # Header Action Pills (Night mode + Lang)
    draw.rounded_rectangle([w - 180, 80, w - 105, 120], radius=12, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((w - 165, 88), "🌙", font=get_font(18))
    draw.rounded_rectangle([w - 95, 80, w - 35, 120], radius=12, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((w - 82, 88), "UZ", font=get_font(16, bold=True), fill=C_GOLD)

    # Promotion Carousel Banner
    banner_path = os.path.join(ASSETS_DIR, "camfort_banner.png")
    if os.path.exists(banner_path):
        b_img = Image.open(banner_path).resize((w - 70, 240), Image.Resampling.LANCZOS)
        b_rounded = round_corners(b_img, 20)
        screen.paste(b_rounded, (35, 150), b_rounded)
        draw.rounded_rectangle([35, 150, w - 35, 390], radius=20, outline=C_GOLD, width=2)

    # Dots indicator
    for idx, dx in enumerate([w//2 - 25, w//2 - 5, w//2 + 15]):
        color = C_GOLD if idx == 0 else C_CARD_BORDER
        draw.ellipse([dx, 405, dx + 12, 417], fill=color)

    # Quick Action Cards
    # 1. Tezkor Zakaz (Gold Card)
    draw.rounded_rectangle([35, 440, w - 310, 560], radius=22, fill=C_GOLD)
    draw.ellipse([55, 465, 115, 525], fill=(0, 0, 0))
    draw.text((73, 477), "🚖", font=get_font(24))
    draw.text((130, 465), "TEZKOR ZAKAZ", font=get_font(22, bold=True), fill=(0, 0, 0))
    draw.text((130, 502), "Bir zumda buyurtma bering", font=get_font(16), fill=(40, 40, 40))

    # 2. 1144 Call Center Card
    draw.rounded_rectangle([w - 290, 440, w - 35, 560], radius=22, fill=C_CARD_BG, outline=C_CARD_BORDER, width=2)
    draw.text((w - 265, 462), "📞 1144", font=get_font(24, bold=True), fill=C_GREEN)
    draw.text((w - 265, 502), "Call Markaz", font=get_font(16), fill=C_TEXT_MUTED)

    # Section Title: Tajribali Haydovchilarimiz
    draw.text((35, 590), "Bizning Tajribali Haydovchilarimiz", font=get_font(24, bold=True), fill=C_TEXT_WHITE)
    draw.text((35, 625), "Eng yuqori reytingli professional haydovchilar", font=get_font(16), fill=C_TEXT_MUTED)

    # Driver Card 1
    d_card_y = 665
    draw.rounded_rectangle([35, d_card_y, w - 35, d_card_y + 240], radius=22, fill=C_CARD_BG, outline=C_CARD_BORDER, width=2)
    
    # Gentra car image inside card
    gentra_path = os.path.join(ASSETS_DIR, "tariff_camfort.png")
    if os.path.exists(gentra_path):
        g_img = Image.open(gentra_path).resize((220, 150), Image.Resampling.LANCZOS)
        g_rounded = round_corners(g_img, 14)
        screen.paste(g_rounded, (55, d_card_y + 20), g_rounded)

    draw.text((295, d_card_y + 25), "Sardor Akramov", font=get_font(22, bold=True), fill=C_TEXT_WHITE)
    draw.text((295, d_card_y + 60), "Chevrolet Lacetti Gentra", font=get_font(17), fill=C_TEXT_MUTED)
    
    # Car badge
    draw.rounded_rectangle([295, d_card_y + 95, 435, d_card_y + 130], radius=8, fill=(35, 42, 55))
    draw.text((308, d_card_y + 102), "40 A 777 AA", font=get_font(15, bold=True), fill=C_GOLD_BRIGHT)

    # Rating badge
    draw.rounded_rectangle([445, d_card_y + 95, 560, d_card_y + 130], radius=8, fill=(45, 38, 15))
    draw.text((455, d_card_y + 102), "⭐ 5.0 (420+)", font=get_font(15, bold=True), fill=C_GOLD)

    # Call Button inside driver card
    draw.rounded_rectangle([295, d_card_y + 150, w - 55, d_card_y + 210], radius=16, fill=C_GREEN)
    draw.text((350, d_card_y + 168), "📞 Bog'lanish: +998 90 123 45 67", font=get_font(17, bold=True), fill=C_TEXT_WHITE)

    # Section 2: Yo'nalishlar tezkor havolasi
    r_card_y = 935
    draw.rounded_rectangle([35, r_card_y, w - 35, r_card_y + 110], radius=22, fill=C_CARD_BG, outline=C_GOLD, width=2)
    draw.text((55, r_card_y + 28), "🛣 Yo'nalishlar va Tariflar Jadvali", font=get_font(20, bold=True), fill=C_GOLD_BRIGHT)
    draw.text((55, r_card_y + 64), "Vodiy — Toshkent bo'yicha barcha yo'nalishlar narxlari", font=get_font(15), fill=C_TEXT_MUTED)
    draw.text((w - 85, r_card_y + 38), "➔", font=get_font(28, bold=True), fill=C_GOLD)

    # Section 3: Sharhlar
    rev_y = 1075
    draw.text((35, rev_y), "Mijozlarimiz Fikrlari", font=get_font(22, bold=True), fill=C_TEXT_WHITE)
    draw.rounded_rectangle([35, rev_y + 40, w - 35, rev_y + 170], radius=20, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, rev_y + 58), "⭐⭐⭐⭐⭐  Azizbek R.", font=get_font(18, bold=True), fill=C_GOLD)
    draw.text((55, rev_y + 95), "“Mashina juda toza va qulay, haydovchi o'z vaqtida keldi.", font=get_font(16), fill=C_TEXT_WHITE)
    draw.text((55, rev_y + 125), "Vodiyga qatnovda doim 1144 Camfort Taxidan foydalanaman!”", font=get_font(16), fill=C_TEXT_MUTED)

    draw_bottom_nav(screen, active_idx=2)
    return draw_phone_frame(poster, screen)

# -------------------------------------------------------------
# SCREEN 2: ORDER SCREEN
# -------------------------------------------------------------
def make_screenshot_2():
    poster = create_base_poster(
        badge="TEZKOR BUYURTMA",
        title="Qulay va Oson Zakaz Bering",
        subtitle="Yo'nalish va tarifni tanlang, narxni darhol hisoblang"
    )
    screen, draw = create_base_app_screen()
    w, _ = screen.size

    # Header
    draw.text((35, 80), "Yangi Buyurtma Berish", font=get_font(26, bold=True), fill=C_GOLD_BRIGHT)
    draw.text((35, 115), "Manzil va tarifni tanlab, tezkor taksi chaqiring", font=get_font(15), fill=C_TEXT_MUTED)

    # Route Selector Dropdown Card
    draw.rounded_rectangle([35, 160, w - 35, 260], radius=20, fill=C_CARD_BG, outline=C_GOLD, width=2)
    draw.text((55, 180), "📍 Yo'nalishni tanlang:", font=get_font(15), fill=C_TEXT_MUTED)
    draw.text((55, 212), "Rishton — Toshkent", font=get_font(22, bold=True), fill=C_TEXT_WHITE)
    draw.text((w - 85, 205), "▼", font=get_font(20), fill=C_GOLD)

    # 3 Tariff Cards (Standart, Camfort, Biznes)
    draw.text((35, 280), "Tarif turini tanlang:", font=get_font(18, bold=True), fill=C_TEXT_WHITE)
    
    tariffs = [
        ("Standart", "Cobalt", "120 000 so'm", False),
        ("Camfort", "Gentra", "150 000 so'm", True),
        ("Biznes", "Malibu", "200 000 so'm", False),
    ]

    card_w = (w - 70 - 24) // 3
    for idx, (tname, tcar, tprice, is_sel) in enumerate(tariffs):
        tx = 35 + idx * (card_w + 12)
        ty = 315
        th = 160
        border_col = C_GOLD if is_sel else C_CARD_BORDER
        bg_col = (45, 38, 18) if is_sel else C_CARD_BG
        draw.rounded_rectangle([tx, ty, tx + card_w, ty + th], radius=18, fill=bg_col, outline=border_col, width=2 if is_sel else 1)
        
        icon = "🚗" if idx == 0 else ("🚙" if idx == 1 else "🚘")
        draw.text((tx + 20, ty + 16), icon, font=get_font(22))
        draw.text((tx + 20, ty + 50), tname, font=get_font(18, bold=True), fill=C_GOLD_BRIGHT if is_sel else C_TEXT_WHITE)
        draw.text((tx + 20, ty + 80), tcar, font=get_font(14), fill=C_TEXT_MUTED)
        draw.text((tx + 20, ty + 115), tprice, font=get_font(16, bold=True), fill=C_GOLD if is_sel else C_TEXT_WHITE)

    # Passengers count & Seat Selection
    draw.rounded_rectangle([35, 500, w - 35, 620], radius=20, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, 520), "👥 Yo'lovchilar soni va O'rindiq:", font=get_font(16, bold=True), fill=C_TEXT_WHITE)
    draw.rounded_rectangle([55, 555, 280, 600], radius=12, fill=(35, 42, 55))
    draw.text((75, 567), "Old o'rindiq (1 kishi)", font=get_font(15), fill=C_TEXT_MUTED)
    draw.rounded_rectangle([295, 555, w - 55, 600], radius=12, fill=C_GOLD_BG, outline=C_GOLD)
    draw.text((315, 567), "✓ Orqa o'rindiq (3 kishi)", font=get_font(15, bold=True), fill=C_GOLD_BRIGHT)

    # Luggage Card
    draw.rounded_rectangle([35, 640, w - 35, 730], radius=20, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, 658), "🧳 Yuk holati:", font=get_font(15), fill=C_TEXT_MUTED)
    draw.text((55, 688), "Ha, bagaj kerak (Katta yukxona)", font=get_font(17, bold=True), fill=C_TEXT_WHITE)

    # Phone input & Location
    draw.rounded_rectangle([35, 750, w - 35, 840], radius=20, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, 768), "📞 Telefon raqamingiz:", font=get_font(15), fill=C_TEXT_MUTED)
    draw.text((55, 798), "+998 90 123 45 67", font=get_font(19, bold=True), fill=C_TEXT_WHITE)
    
    # GPS Button
    draw.rounded_rectangle([35, 860, w - 35, 930], radius=16, fill=(28, 40, 58), outline=C_BLUE)
    draw.text((65, 882), "📍 Aniq turgan GPS lokatsiyangiz olindi", font=get_font(16, bold=True), fill=C_BLUE)

    # Coupon & Calculation
    draw.rounded_rectangle([35, 950, w - 35, 1070], radius=20, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, 970), "🏷 Kupon (Promo kod): CAMFORT2026", font=get_font(16, bold=True), fill=C_GREEN)
    draw.text((55, 1005), "Asl narx: 150 000 so'm    Chegirma: -20 000 so'm", font=get_font(15), fill=C_TEXT_MUTED)
    draw.text((55, 1035), "To'lov summasi: 130 000 so'm", font=get_font(18, bold=True), fill=C_GOLD_BRIGHT)

    # Big Submit Button
    draw.rounded_rectangle([35, 1100, w - 35, 1180], radius=22, fill=C_GOLD)
    draw.text((w//2 - 130, 1125), "🚖 BUYURTMA YUBORISH", font=get_font(22, bold=True), fill=(0, 0, 0))

    draw_bottom_nav(screen, active_idx=1)
    return draw_phone_frame(poster, screen)

# -------------------------------------------------------------
# SCREEN 3: ROUTES & CAR SELECTOR
# -------------------------------------------------------------
def make_screenshot_3():
    poster = create_base_poster(
        badge="ANIQ TARIFLAR",
        title="Yo'nalishlar va Avtomobillar",
        subtitle="Tarif tanlanganda avtomobil surati dinamik almashadi"
    )
    screen, draw = create_base_app_screen()
    w, _ = screen.size

    # Header
    draw.text((35, 80), "Yo'nalishlar va Tariflar", font=get_font(26, bold=True), fill=C_GOLD_BRIGHT)
    draw.text((35, 115), "Shaharlararo qulay va xavfsiz qatnovlar", font=get_font(15), fill=C_TEXT_MUTED)
    
    # Refresh button
    draw.rounded_rectangle([w - 170, 78, w - 35, 125], radius=14, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((w - 150, 90), "🔄 Yangilash", font=get_font(15, bold=True), fill=C_GOLD)

    # Section 1 Header
    draw.text((35, 155), "VODIYDAN TOSHKENTGA", font=get_font(18, bold=True), fill=C_GOLD)

    # Main Interactive Route Card: Rishton — Toshkent
    rc_y = 195
    draw.rounded_rectangle([35, rc_y, w - 35, rc_y + 590], radius=24, fill=C_CARD_BG, outline=C_GOLD, width=2)

    # Car Photo (Gentra)
    gentra_path = os.path.join(ASSETS_DIR, "tariff_camfort.png")
    if os.path.exists(gentra_path):
        g_img = Image.open(gentra_path).resize((w - 90, 240), Image.Resampling.LANCZOS)
        g_rounded = round_corners(g_img, 18)
        screen.paste(g_rounded, (45, rc_y + 10), g_rounded)

    # Duration Badge over image
    draw.rounded_rectangle([60, rc_y + 25, 210, rc_y + 65], radius=10, fill=(0, 0, 0, 200), outline=C_GOLD)
    draw.text((75, rc_y + 35), "⏱ 4 soatlik yo'l", font=get_font(15, bold=True), fill=C_GOLD_BRIGHT)

    # Route title inside card
    draw.text((55, rc_y + 270), "Rishton — Toshkent", font=get_font(26, bold=True), fill=C_TEXT_WHITE)
    draw.text((55, rc_y + 308), "Tarifni bosing (Mashina rasmi almashadi):", font=get_font(15), fill=C_TEXT_MUTED)

    # Interactive 3 tariffs list
    tariffs_info = [
        ("🚗 Standart", "Chevrolet Cobalt", "120 000 so'm", False),
        ("🚙 Camfort (Tanlangan)", "Lacetti Gentra", "150 000 so'm", True),
        ("🚘 Biznes", "Chevrolet Malibu", "200 000 so'm", False),
    ]

    for tidx, (tname, tcar, tprice, tsel) in enumerate(tariffs_info):
        ty = rc_y + 345 + tidx * 62
        b_col = C_GOLD if tsel else C_CARD_BORDER
        f_col = (45, 38, 18) if tsel else (20, 24, 34)
        draw.rounded_rectangle([55, ty, w - 55, ty + 54], radius=14, fill=f_col, outline=b_col, width=2 if tsel else 1)
        draw.text((75, ty + 15), tname, font=get_font(16, bold=True), fill=C_GOLD_BRIGHT if tsel else C_TEXT_WHITE)
        draw.text((w - 220, ty + 15), tprice, font=get_font(16, bold=True), fill=C_GOLD if tsel else C_TEXT_MUTED)

    # Order Button inside card
    draw.rounded_rectangle([55, rc_y + 535, w - 55, rc_y + 580], radius=16, fill=C_GOLD)
    draw.text((w//2 - 120, rc_y + 546), "🚖 USHBU YO'NALISHGA ZAKAZ", font=get_font(17, bold=True), fill=(0, 0, 0))

    # Section 2 Header: Toshkentdan Vodiyga
    draw.text((35, 810), "TOSHKENTDAN VODIYGA", font=get_font(18, bold=True), fill=C_GOLD)

    # Next Route Card Preview
    nrc_y = 845
    draw.rounded_rectangle([35, nrc_y, w - 35, nrc_y + 110], radius=20, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, nrc_y + 25), "Toshkent — Farg'ona (Rishton)", font=get_font(20, bold=True), fill=C_TEXT_WHITE)
    draw.text((55, nrc_y + 60), "Standart: 120 000 • Camfort: 150 000 • Biznes: 200 000", font=get_font(15), fill=C_TEXT_MUTED)
    draw.text((w - 85, nrc_y + 35), "➔", font=get_font(24), fill=C_GOLD)

    draw_bottom_nav(screen, active_idx=3)
    return draw_phone_frame(poster, screen)

# -------------------------------------------------------------
# SCREEN 4: ORDERS STATUS & RATING
# -------------------------------------------------------------
def make_screenshot_4():
    poster = create_base_poster(
        badge="JONLI NAZORAT",
        title="Buyurtmangiz Doim Nazoratda",
        subtitle="Haydovchi ma'lumotlari, jonli aloqa va baholash"
    )
    screen, draw = create_base_app_screen()
    w, _ = screen.size

    # Header
    draw.text((35, 80), "Mening Buyurtmalarim", font=get_font(26, bold=True), fill=C_GOLD_BRIGHT)
    draw.text((35, 115), "Barcha faol va yakunlangan buyurtmalar holati", font=get_font(15), fill=C_TEXT_MUTED)

    # 3 Filter Tabs
    tabs = [("Kutilayotgan", False), ("Qabul qilingan (1)", True), ("Bekor qilingan", False)]
    tab_w = (w - 70 - 20) // 3
    for idx, (tname, is_sel) in enumerate(tabs):
        tx = 35 + idx * (tab_w + 10)
        ty = 160
        bg_col = C_GOLD if is_sel else C_CARD_BG
        txt_col = (0, 0, 0) if is_sel else C_TEXT_MUTED
        draw.rounded_rectangle([tx, ty, tx + tab_w, ty + 48], radius=14, fill=bg_col)
        draw.text((tx + 18, ty + 12), tname, font=get_font(16, bold=True), fill=txt_col)

    # Accepted Order Card
    oc_y = 230
    draw.rounded_rectangle([35, oc_y, w - 35, oc_y + 440], radius=24, fill=C_CARD_BG, outline=C_GREEN, width=2)

    # Status Pill
    draw.rounded_rectangle([55, oc_y + 20, 310, oc_y + 65], radius=12, fill=(20, 50, 32))
    draw.text((70, oc_y + 30), "✅ QABUL QILINDI", font=get_font(16, bold=True), fill=C_GREEN)
    draw.text((w - 180, oc_y + 30), "#CF3886", font=get_font(18, bold=True), fill=C_GOLD)

    draw.line([(55, oc_y + 80), (w - 55, oc_y + 80)], fill=C_CARD_BORDER, width=1)

    draw.text((55, oc_y + 98), "Yo'nalish: Rishton — Toshkent", font=get_font(20, bold=True), fill=C_TEXT_WHITE)
    draw.text((55, oc_y + 132), "Tarif: Camfort (Orqa o'rindiq • 1 kishi)", font=get_font(16), fill=C_TEXT_MUTED)
    draw.text((55, oc_y + 165), "To'lov summasi: 130 000 so'm", font=get_font(18, bold=True), fill=C_GOLD_BRIGHT)

    # Driver Info Box
    draw.rounded_rectangle([55, oc_y + 210, w - 55, oc_y + 340], radius=16, fill=(18, 22, 32), outline=C_CARD_BORDER)
    draw.text((75, oc_y + 225), "Haydovchi: Sardor Akramov", font=get_font(18, bold=True), fill=C_TEXT_WHITE)
    draw.text((75, oc_y + 258), "Mashina: Lacetti Gentra (40 A 777 AA)", font=get_font(16), fill=C_TEXT_MUTED)
    draw.text((75, oc_y + 295), "📞 Tel: +998 90 123 45 67", font=get_font(17, bold=True), fill=C_GREEN)

    # Call Driver Button
    draw.rounded_rectangle([55, oc_y + 360, w - 55, oc_y + 420], radius=16, fill=C_GREEN)
    draw.text((w//2 - 130, oc_y + 377), "📞 HAYDOVCHIGA QO'NG'IROQ", font=get_font(17, bold=True), fill=C_TEXT_WHITE)

    # Review & Rating Modal Box (Overlay style)
    rw_y = 700
    draw.rounded_rectangle([35, rw_y, w - 35, rw_y + 320], radius=24, fill=(30, 26, 18), outline=C_GOLD, width=2)
    draw.text((55, rw_y + 25), "⭐️ Safarni Baholash", font=get_font(22, bold=True), fill=C_GOLD_BRIGHT)
    draw.text((55, rw_y + 60), "Safar qanday o'tdi? Haydovchiga baho bering:", font=get_font(15), fill=C_TEXT_MUTED)
    
    # Stars
    draw.text((55, rw_y + 95), "⭐  ⭐  ⭐  ⭐  ⭐", font=get_font(32), fill=C_GOLD)

    # Comment input field mockup
    draw.rounded_rectangle([55, rw_y + 155, w - 55, rw_y + 225], radius=14, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((75, rw_y + 178), "Juda ajoyib xizmat, haydovchi o'z vaqtida keldi!", font=get_font(16), fill=C_TEXT_WHITE)

    # Submit review button
    draw.rounded_rectangle([55, rw_y + 245, w - 55, rw_y + 300], radius=16, fill=C_GOLD)
    draw.text((w//2 - 80, rw_y + 260), "BAHONI YUBORISH", font=get_font(17, bold=True), fill=(0, 0, 0))

    draw_bottom_nav(screen, active_idx=0)
    return draw_phone_frame(poster, screen)

# -------------------------------------------------------------
# SCREEN 5: 24/7 SUPPORT & PROFILE
# -------------------------------------------------------------
def make_screenshot_5():
    poster = create_base_poster(
        badge="24/7 ALOQA",
        title="Doimiy Yordam va Aloqa",
        subtitle="1144 qisqa raqami va Telegram orqali tunu-kun yordam"
    )
    screen, draw = create_base_app_screen()
    w, _ = screen.size

    # Header
    draw.text((35, 80), "Yordam va Sozlamalar", font=get_font(26, bold=True), fill=C_GOLD_BRIGHT)
    draw.text((35, 115), "24/7 qo'llab-quvvatlash va ilovani sozlash", font=get_font(15), fill=C_TEXT_MUTED)

    # Big 1144 Call Center Banner Card
    call_y = 160
    draw.rounded_rectangle([35, call_y, w - 35, call_y + 200], radius=24, fill=(20, 48, 30), outline=C_GREEN, width=2)
    draw.ellipse([65, call_y + 40, 165, call_y + 140], fill=C_GREEN)
    draw.text((92, call_y + 60), "📞", font=get_font(42))
    draw.text((190, call_y + 45), "CALL MARKAZ: 1144", font=get_font(26, bold=True), fill=C_GREEN)
    draw.text((190, call_y + 88), "+998 95 287 16 66", font=get_font(22, bold=True), fill=C_TEXT_WHITE)
    draw.text((190, call_y + 128), "Tunu-kun operatorlar xizmatda", font=get_font(16), fill=(180, 230, 195))

    # Telegram Support Card
    tg_y = 385
    draw.rounded_rectangle([35, tg_y, w - 35, tg_y + 120], radius=22, fill=C_CARD_BG, outline=C_BLUE, width=2)
    draw.ellipse([55, tg_y + 25, 125, tg_y + 95], fill=(28, 55, 90))
    draw.text((72, tg_y + 42), "✈️", font=get_font(26))
    draw.text((145, tg_y + 32), "Telegram Administrator", font=get_font(20, bold=True), fill=C_TEXT_WHITE)
    draw.text((145, tg_y + 68), "@akramjonov777 ga to'g'ridan-to'g'ri yozish", font=get_font(16), fill=C_BLUE)

    # App Language Card
    lang_y = 530
    draw.rounded_rectangle([35, lang_y, w - 35, lang_y + 220], radius=22, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, lang_y + 22), "🌐 Ilova Tili (Language):", font=get_font(18, bold=True), fill=C_TEXT_WHITE)
    
    # 3 Lang Options
    langs = [("🇺🇿 O'zbekcha (Lotin)", True), ("🇷🇺 Русский", False), ("🇺🇿 Ўзбекча (Крилл)", False)]
    for lidx, (lname, lsel) in enumerate(langs):
        ly = lang_y + 65 + lidx * 46
        b_col = C_GOLD if lsel else (35, 42, 55)
        draw.rounded_rectangle([55, ly, w - 55, ly + 38], radius=10, fill=(30, 36, 48) if lsel else (20, 24, 32), outline=b_col)
        draw.text((75, ly + 8), lname, font=get_font(16, bold=lsel), fill=C_GOLD_BRIGHT if lsel else C_TEXT_MUTED)
        if lsel:
            draw.text((w - 95, ly + 8), "✓", font=get_font(18, bold=True), fill=C_GOLD)

    # Dark / Light Theme Selector
    theme_y = 775
    draw.rounded_rectangle([35, theme_y, w - 35, theme_y + 110], radius=22, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, theme_y + 24), "🎨 Ilova Mavzusi:", font=get_font(18, bold=True), fill=C_TEXT_WHITE)
    draw.text((55, theme_y + 60), "Qorong'u (Dark Gold) rejim tanlangan", font=get_font(15), fill=C_GOLD)
    draw.rounded_rectangle([w - 145, theme_y + 35, w - 55, theme_y + 75], radius=20, fill=C_GOLD)
    draw.ellipse([w - 95, theme_y + 38, w - 60, theme_y + 72], fill=(0, 0, 0))

    # App Info & Security Footer
    info_y = 910
    draw.rounded_rectangle([35, info_y, w - 35, info_y + 150], radius=22, fill=C_CARD_BG, outline=C_CARD_BORDER)
    draw.text((55, info_y + 25), "🔒 Xavfsiz va Ishonchli Taxi Xizmati", font=get_font(18, bold=True), fill=C_TEXT_WHITE)
    draw.text((55, info_y + 60), "CAMFORT TAXI 1144 • Versiya 1.0.1", font=get_font(15), fill=C_TEXT_MUTED)
    draw.text((55, info_y + 95), "Barcha huquqlar himoyalangan © 2026", font=get_font(14), fill=(100, 110, 125))

    draw_bottom_nav(screen, active_idx=4)
    return draw_phone_frame(poster, screen)

def main():
    print("Generating Google Play Store screenshots for CAMFORT TAXI 1144...")
    
    s1 = make_screenshot_1()
    s1.save(os.path.join(OUTPUT_DIR, "screenshot_1_home.png"), quality=95)
    print("[OK] Saved screenshot_1_home.png")

    s2 = make_screenshot_2()
    s2.save(os.path.join(OUTPUT_DIR, "screenshot_2_order.png"), quality=95)
    print("[OK] Saved screenshot_2_order.png")

    s3 = make_screenshot_3()
    s3.save(os.path.join(OUTPUT_DIR, "screenshot_3_routes.png"), quality=95)
    print("[OK] Saved screenshot_3_routes.png")

    s4 = make_screenshot_4()
    s4.save(os.path.join(OUTPUT_DIR, "screenshot_4_orders_status.png"), quality=95)
    print("[OK] Saved screenshot_4_orders_status.png")

    s5 = make_screenshot_5()
    s5.save(os.path.join(OUTPUT_DIR, "screenshot_5_support.png"), quality=95)
    print("[OK] Saved screenshot_5_support.png")

    print("\nAll 5 Play Store screenshots generated successfully in:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
