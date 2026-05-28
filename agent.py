"""
PeakSync — Cycle Nutrition Image Carousel Generator
--------------------------------------------------
Each run:
  - Fetches a portrait-oriented background food/texture photo from Pexels
  - Generates a sequential 3-slide educational carousel (.png)
  - Outputs a text file with the matching nutritional caption

Requirements:
    pip install requests python-dotenv pillow
"""

import os
import json
import random
import requests
import datetime
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────────────────

PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
OUTPUT_DIR     = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Font setup for Ubuntu runners vs local environments
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "Arial.ttf"

# ── Nutritional Content Library ───────────────────────────────────────────────
# Sequentially loops or selects content based on the calendar day.
# Every topic builds a 3-slide visual story: 1. Context -> 2. Science -> 3. Food Plate
CONTENT_LIBRARY = [
    {
        "phase": "Menstrual Phase (Days 1–5)",
        "slides": [
            "MENSTRUAL PHASE\n\nYour energy is low,\nand iron levels are dipping.\nTime to replenish.",
            "THE NUTRITIONAL FOCUS\n\nPair non-heme iron\nwith Vitamin C to double\nyour body's absorption.",
            "ON YOUR PLATE\n\nDark leafy greens,\nlentils, citrus fruits,\nand dark chocolate (70%+)."
        ],
        "hooks": [
            "If you're feeling completely wiped out on Day 1 or 2 of your period, your body isn't being lazy. It's working overtime. 🩸",
            "Cramping and fatigue are data. Here is exactly how to feed your body during your bleeding window. 🥑",
        ],
        "caption_body": "During menstruation, your estrogen and progesterone are at their lowest points while your body is actively shedding its uterine lining. Pushing through with caffeine or skipping meals spikes cortisol, making cramps worse.\n\nFocusing on warm, bioavailable, iron-rich foods helps rebuild your mineral stores and stabilizes your baseline metabolic recovery.",
        "cta": "👇 What is your ultimate comfort food on Day 1? Let me know below!",
        "pexels_query": "lentil spinach soup bowl rustic"
    },
    {
        "phase": "Follicular Phase (Days 6–13)",
        "slides": [
            "FOLLICULAR PHASE\n\nEstrogen is rising.\nYour metabolism is efficient\nand ready for fuel.",
            "THE NUTRITIONAL FOCUS\n\nSupport your gut health\nto help your liver process and\nmetabolize rising estrogen.",
            "ON YOUR PLATE\n\nLight, vibrant foods:\nKimchi, quinoa, avocados,\nand lean proteins."
        ],
        "hooks": [
            "Energy shifting upwards? Welcome to your follicular phase. Here is how to fuel the build. ⚡",
            "Your body is highly insulin-sensitive this week, meaning it processes clean carbohydrates beautifully. 🌾",
        ],
        "caption_body": "As follicles develop, estrogen steadily rises, bringing an increase in physical endurance, mental clarity, and muscle recovery speeds.\n\nAdding fermented or gut-friendly components supports the microbiome, ensuring your body processes this upward shift smoothly without leaving you feeling sluggish.",
        "cta": "👇 Have you noticed your energy kicking in this week? Drop a ⚡ if yes!",
        "pexels_query": "quinoa grain salad bowl fresh"
    },
    {
        "phase": "Ovulatory Phase (Days 14–16)",
        "slides": [
            "OVULATORY PHASE\n\nEstrogen peaks.\nYour system is running at\nmaximum biological speed.",
            "THE NUTRITIONAL FOCUS\n\nLoad up on fiber and sulfur\nto support your liver as it\nclears out excess hormones.",
            "ON YOUR PLATE\n\nCruciferous vegetables:\nBroccoli, Brussels sprouts,\nberries, and raw seeds."
        ],
        "hooks": [
            "You are at your physiological peak this week. Let's make sure your nutrition matches it. 🔥",
            "The liver works double time around ovulation to process your estrogen spike. Give it an assist. 🥦",
        ],
        "caption_body": "At ovulation, estrogen hits its highest threshold. While you might feel naturally less hungry due to testosterone peaks, your liver needs heavy support to metabolize and detoxify these hormones safely.\n\nCruciferous vegetables contain essential compounds that naturally support this pathways, keeping skin clear and transitions smooth.",
        "cta": "👇 What's your favorite way to prep broccoli or greens? Share below!",
        "pexels_query": "berry smoothie bowl morning"
    },
    {
        "phase": "Luteal Phase (Days 17–28)",
        "slides": [
            "LUTEAL PHASE\n\nProgesterone takes over.\nYour resting metabolism naturally\nspeeds up.",
            "THE NUTRITIONAL FOCUS\n\nKeep blood sugar stable\nto completely bypass intense\nPMS mood and sugar cravings.",
            "ON YOUR PLATE\n\nSlow-burning complex carbs:\nRoasted sweet potatoes,\nsquash, poultry, and walnuts."
        ],
        "hooks": [
            "PMS sugar cravings are not a character flaw. They are simple biology. 🧠",
            "Feeling anxious or craving carbs before your period? Your progesterone is demanding stable fuel. 🍠",
        ],
        "caption_body": "During the luteal phase, progesterone takes over to preserve the uterine lining, raising your resting core temperature and burning more baseline calories. This triggers a biological demand for energy.\n\nFeeding that demand with rapid spikes (like processed sugars) leads to steep crashes that worsen irritability and bloating. Opting for complex, grounding root vegetables gives you steady, sustained release.",
        "cta": "👇 Save this post for your next pre-period week! 💾",
        "pexels_query": "roasted sweet potato wedges"
    }
]

APP_TEASER = "Track your biology. Fuel your potential. App coming soon. 🌸"
HASHTAGS   = "#PeakSync #CycleSyncing #HormoneNutrition #PeriodHealth #WomenWhoTrain #BodyLiteracy #LutealPhase #BiohackingWomen"


# ── Step 1: Pick Content ──────────────────────────────────────────────────────

def pick_content() -> dict:
    index = datetime.date.today().toordinal() % len(CONTENT_LIBRARY)
    topic = CONTENT_LIBRARY[index]
    hook  = random.choice(topic["hooks"])

    caption = f"""{hook}\n\n{topic['caption_body']}\n\n{topic['cta']}\n\n{APP_TEASER}\n\n{HASHTAGS}"""

    print(f"✅ Selected Phase: {topic['phase']}")
    return {
        "slides": topic["slides"],
        "caption": caption,
        "pexels_query": topic["pexels_query"]
    }


# ── Step 2: Fetch Pexels Image ────────────────────────────────────────────────

def fetch_pexels_image(query: str) -> bytes:
    resp = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "orientation": "portrait", "per_page": 5},
        timeout=15,
    )
    resp.raise_for_status()
    photos = resp.json().get("photos", [])
    if not photos:
        # Generic elegant fallback if a specific food query is empty
        print("⚠️ Specific query yielded no results. Using aesthetic fallback.")
        return fetch_pexels_image("minimalist lifestyle background")
    
    photo = random.choice(photos)
    image_url = photo["src"]["large2x"]
    
    return requests.get(image_url, timeout=30).content


# ── Step 3: Render Slides ─────────────────────────────────────────────────────

def generate_carousel_images(image_bytes: bytes, slides_text: list[str]) -> list[str]:
    date_str = datetime.date.today().isoformat()
    generated_paths = []
    
    target_w, target_h = 1080, 1920
    
    base_img = Image.open(io.BytesIO(image_bytes))
    base_img = base_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    for idx, text in enumerate(slides_text):
        slide_img = base_img.copy()
        draw = ImageDraw.Draw(slide_img, "RGBA")
        
        try:
            font = ImageFont.truetype(FONT_PATH, size=56)
        except IOError:
            font = ImageFont.load_default()

        # Premium semi-transparent overlay to keep text hyper-legible over food shots
        draw.rectangle([0, 0, target_w, target_h], fill=(15, 23, 23, 140))

        # Center layout text engine
        lines = text.splitlines()
        total_text_height = sum([draw.textbbox((0, 0), line if line.strip() else "A", font=font)[3] for line in lines]) + (len(lines) * 25)
        current_y = (target_h - total_text_height) // 2
        
        for line in lines:
            if not line.strip():
                current_y += 40  # Support double line breaks in text block
                continue
                
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_h = bbox[3] - bbox[1]
            
            x_pos = (target_w - line_w) // 2
            
            # Subtle branding shadow
            draw.text((x_pos + 2, current_y + 2), line, font=font, fill=(0, 0, 0, 120))
            # Main typography
            draw.text((x_pos, current_y), line, font=font, fill=(255, 255, 255, 255))
            
            current_y += line_h + 35

        # Save out frame
        filename = OUTPUT_DIR / f"slide_{date_str}_{idx + 1}.png"
        slide_img.save(filename, "PNG")
        generated_paths.append(str(filename))
        print(f"   ↳ Generated Slide {idx + 1}: {filename.name}")

    return generated_paths


# ── Step 4: Write Outputs ─────────────────────────────────────────────────────

def save_caption(caption: str) -> str:
    date_str = datetime.date.today().isoformat()
    path = OUTPUT_DIR / f"caption_{date_str}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(caption)
    return str(path)


def run():
    print(f"\n🌸 PeakSync Nutrition Content Engine — {datetime.date.today()}\n{'─'*50}")
    
    content = pick_content()
    image_data = fetch_pexels_image(content["pexels_query"])
    slide_files = generate_carousel_images(image_data, content["slides"])
    caption_path = save_caption(content["caption"])

    print(f"\n┌──────────────────────────────────────────────────┐")
    print(f"│  ✅ Carousel Assets Ready for Download            │")
    print(f"├──────────────────────────────────────────────────┤")
    for s_file in slide_files:
        print(f"│  📷 {Path(s_file).name:<44} │")
    print(f"│  📝 {Path(caption_path).name:<44} │")
    print(f"└──────────────────────────────────────────────────┘\n")


if __name__ == "__main__":
    run()