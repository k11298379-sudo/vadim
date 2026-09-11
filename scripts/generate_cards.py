"""
Generator for all 36 Durak playing cards + card back in crisp, standalone vector SVG format.
Outputs to frontend/img/cards/
"""
import os

OUT_DIR = "frontend/img/cards"
os.makedirs(OUT_DIR, exist_ok=True)

SUITS = {
    "spades": {"symbol": "♠", "color": "#0f172a", "name": "spades", "label": "Пики"},
    "clubs": {"symbol": "♣", "color": "#1e293b", "name": "clubs", "label": "Трефы"},
    "hearts": {"symbol": "♥", "color": "#e11d48", "name": "hearts", "label": "Черви"},
    "diamonds": {"symbol": "♦", "color": "#ea580c", "name": "diamonds", "label": "Бубны"},
}

RANKS = ["6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Suit vector paths normalized in a 100x100 viewBox
SUIT_PATHS = {
    "hearts": "M 50,28 C 38,12 15,20 15,42 C 15,64 45,86 50,90 C 55,86 85,64 85,42 C 85,20 62,12 50,28 Z",
    "diamonds": "M 50,12 L 82,50 L 50,88 L 18,50 Z",
    "spades": "M 50,14 C 38,32 20,42 20,58 C 20,72 32,80 44,76 L 42,90 L 58,90 L 56,76 C 68,80 80,72 80,58 C 80,42 62,32 50,14 Z",
    "clubs": "M 50,14 C 41,14 34,21 34,30 C 34,36 37,41 42,44 C 34,43 23,50 23,62 C 23,73 32,82 44,80 L 42,90 L 58,90 L 56,80 C 68,82 77,73 77,62 C 77,50 66,43 58,44 C 63,41 66,36 66,30 C 66,21 59,14 50,14 Z",
}

def generate_card_svg(rank: str, suit_key: str) -> str:
    suit_info = SUITS[suit_key]
    color = suit_info["color"]
    path_d = SUIT_PATHS[suit_key]
    symbol = suit_info["symbol"]

    # Crown / royal badges for face cards
    center_art = ""
    if rank == "A":
        center_art = f"""
        <!-- Ace Center -->
        <g transform="translate(30, 52) scale(0.6)">
            <path d="{path_d}" fill="{color}" />
        </g>
        <circle cx="60" cy="82" r="3" fill="#ffffff" opacity="0.9"/>
        """
    elif rank in ("K", "Q", "J"):
        role_title = "КОРОЛЬ" if rank == "K" else ("ДАМА" if rank == "Q" else "ВАЛЕТ")
        center_art = f"""
        <!-- Royal Card Frame -->
        <rect x="28" y="44" width="64" height="76" rx="8" fill="#f8fafc" stroke="{color}" stroke-width="1.5" stroke-dasharray="3,2"/>
        <g transform="translate(42, 54) scale(0.36)">
            <path d="{path_d}" fill="{color}" />
        </g>
        <text x="60" y="98" font-size="28" font-weight="900" text-anchor="middle" fill="{color}" font-family="system-ui, -apple-system, sans-serif">{rank}</text>
        <text x="60" y="112" font-size="8" font-weight="700" letter-spacing="1" text-anchor="middle" fill="{color}" opacity="0.75" font-family="system-ui, -apple-system, sans-serif">{role_title}</text>
        """
    else:
        # Number cards (6..10)
        center_art = f"""
        <!-- Number Card Center -->
        <g transform="translate(34, 56) scale(0.52)">
            <path d="{path_d}" fill="{color}" />
        </g>
        <text x="60" y="90" font-size="18" font-weight="900" text-anchor="middle" fill="#ffffff" font-family="system-ui, -apple-system, sans-serif">{rank}</text>
        """

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 170" width="120" height="170">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000000" flood-opacity="0.12"/>
    </filter>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f8fafc"/>
    </linearGradient>
  </defs>

  <!-- Card Body -->
  <rect x="2" y="2" width="116" height="166" rx="10" ry="10" fill="url(#bgGrad)" stroke="#cbd5e1" stroke-width="1.5" filter="url(#shadow)"/>
  <rect x="6" y="6" width="108" height="158" rx="7" ry="7" fill="none" stroke="{color}" stroke-width="0.75" stroke-opacity="0.25"/>

  <!-- Top-Left Corner -->
  <g transform="translate(8, 10)">
    <text x="0" y="14" font-size="16" font-weight="900" fill="{color}" font-family="system-ui, -apple-system, sans-serif">{rank}</text>
    <g transform="translate(0, 18) scale(0.16)">
      <path d="{path_d}" fill="{color}"/>
    </g>
  </g>

  <!-- Center Artwork -->
  {center_art}

  <!-- Bottom-Right Corner (Inverted) -->
  <g transform="translate(112, 160) rotate(180)">
    <text x="0" y="14" font-size="16" font-weight="900" fill="{color}" font-family="system-ui, -apple-system, sans-serif">{rank}</text>
    <g transform="translate(0, 18) scale(0.16)">
      <path d="{path_d}" fill="{color}"/>
    </g>
  </g>
</svg>
"""
    return svg


def generate_back_svg() -> str:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 170" width="120" height="170">
  <defs>
    <linearGradient id="backGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b"/>
      <stop offset="50%" stop-color="#312e81"/>
      <stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>
    <pattern id="backPattern" width="12" height="12" patternUnits="userSpaceOnUse">
      <path d="M 0,6 L 6,0 L 12,6 L 6,12 Z" fill="none" stroke="#6366f1" stroke-width="0.75" opacity="0.35"/>
      <circle cx="6" cy="6" r="1.2" fill="#fbbf24" opacity="0.6"/>
    </pattern>
  </defs>

  <!-- Card Body -->
  <rect x="2" y="2" width="116" height="166" rx="10" ry="10" fill="url(#backGrad)" stroke="#e2e8f0" stroke-width="1.5"/>
  
  <!-- Outer Rim -->
  <rect x="7" y="7" width="106" height="156" rx="7" ry="7" fill="none" stroke="#fbbf24" stroke-width="1.2" opacity="0.8"/>
  
  <!-- Pattern Fill -->
  <rect x="10" y="10" width="100" height="150" rx="5" ry="5" fill="url(#backPattern)"/>

  <!-- Center Medallion -->
  <circle cx="60" cy="85" r="22" fill="#1e1b4b" stroke="#fbbf24" stroke-width="1.5"/>
  <circle cx="60" cy="85" r="18" fill="none" stroke="#6366f1" stroke-width="0.75" stroke-dasharray="2,2"/>
  <text x="60" y="91" font-size="18" text-anchor="middle" fill="#fbbf24">✦</text>
</svg>
"""
    return svg


def main():
    count = 0
    # Generate all 36 cards
    for suit_key in SUITS:
        for rank in RANKS:
            content = generate_card_svg(rank, suit_key)
            filename = f"{rank}_{suit_key}.svg"
            filepath = os.path.join(OUT_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content.strip())
            count += 1

    # Generate back card
    back_content = generate_back_svg()
    with open(os.path.join(OUT_DIR, "back.svg"), "w", encoding="utf-8") as f:
        f.write(back_content.strip())
    count += 1

    print(f"Generated {count} card images in {OUT_DIR}")


if __name__ == "__main__":
    main()
