"""
Email Builder — assembles the final HTML email.
6 visual themes, one per day. Meme images embedded where available.
"""
import datetime

# ── THEME DEFINITIONS ─────────────────────────────────────────
THEMES = {
    "NEWSPAPER": {
        "bg": "#f5f2eb", "ink": "#121212", "accent": "#be1414",
        "surface": "#ece8df", "border": "#ccc8c0", "gray": "#6b6b65",
        "font_head": "Georgia, 'Times New Roman', serif",
        "font_body": "Georgia, 'Times New Roman', serif",
        "font_mono": "'Courier New', Courier, monospace",
        "label": "THE AI ROAST BRIEF",
    },
    "MEME": {
        "bg": "#0f0f0f", "ink": "#ffffff", "accent": "#ff2d78",
        "surface": "#1a1a1a", "border": "#2a2a2a", "gray": "#888888",
        "font_head": "Impact, 'Arial Black', sans-serif",
        "font_body": "'Arial Black', Arial, sans-serif",
        "font_mono": "'Courier New', monospace",
        "label": "😂 DAILY AI ROAST BRIEF",
    },
    "COMIC": {
        "bg": "#0a0a1c", "ink": "#ffffff", "accent": "#ffd600",
        "surface": "#13132e", "border": "#2a2a50", "gray": "#9090b0",
        "font_head": "Impact, 'Arial Black', sans-serif",
        "font_body": "Arial, sans-serif",
        "font_mono": "'Courier New', monospace",
        "label": "🤖 AI ROAST BRIEF",
    },
    "STARTUP": {
        "bg": "#ffffff", "ink": "#111111", "accent": "#6366f1",
        "surface": "#f8f8fc", "border": "#e5e5eb", "gray": "#6b7280",
        "font_head": "'Helvetica Neue', Helvetica, Arial, sans-serif",
        "font_body": "'Helvetica Neue', Helvetica, Arial, sans-serif",
        "font_mono": "'SF Mono', 'Fira Code', monospace",
        "label": "AI Roast Brief",
    },
    "TERMINAL": {
        "bg": "#080a08", "ink": "#e0ffe0", "accent": "#00ff88",
        "surface": "#0d100d", "border": "#1a2a1a", "gray": "#507050",
        "font_head": "'Courier New', 'Lucida Console', monospace",
        "font_body": "'Courier New', 'Lucida Console', monospace",
        "font_mono": "'Courier New', 'Lucida Console', monospace",
        "label": "AI-ROAST-BRIEF v{episode}.0",
    },
    "MAGAZINE": {
        "bg": "#faf8f4", "ink": "#1a1a18", "accent": "#dc2626",
        "surface": "#f0ede6", "border": "#d0cdc6", "gray": "#6b6860",
        "font_head": "Georgia, 'Playfair Display', serif",
        "font_body": "Georgia, serif",
        "font_mono": "'Courier New', monospace",
        "label": "AI ROAST",
    },
}

VIBE_COLORS = {
    "hype":        "#ef4444",
    "interesting": "#3b82f6",
    "bullish":     "#22c55e",
    "thoughtful":  "#a855f7",
    "useful":      "#f59e0b",
}


def build_email(brief: dict) -> str:
    """
    Takes a brief dict (from writer agent, with meme URLs added).
    Returns a complete HTML email string.
    """
    style = brief.get("style", "COMIC")
    theme = THEMES.get(style, THEMES["COMIC"])
    stories = brief.get("stories", [])
    date_str = brief.get("date", datetime.date.today().strftime("%B %d, %Y"))
    episode  = brief.get("episode", 1)

    try:
        display_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        display_date = date_str

    label = theme["label"].replace("{episode}", str(episode))

    t = theme  # shorthand

    # Build story cards HTML
    story_cards = ""
    for story in stories:
        vibe_color = VIBE_COLORS.get(story.get("vibe", "useful"), "#f59e0b")
        meme_html = ""
        if story.get("meme_url"):
            meme_html = f"""
            <div style="margin:16px 0;text-align:center;">
              <img src="{story['meme_url']}" alt="meme"
                   style="max-width:100%;max-height:300px;border-radius:8px;border:2px solid {t['border']};" />
            </div>"""

        story_cards += f"""
        <!-- STORY {story['id']} -->
        <div style="background:{t['surface']};border:1px solid {t['border']};border-left:5px solid {vibe_color};
                    border-radius:8px;padding:24px;margin-bottom:20px;">

          <!-- Header row -->
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
            <span style="background:{vibe_color};color:#fff;font-family:{t['font_mono']};
                         font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;
                         text-transform:uppercase;letter-spacing:0.5px;">
              #{story['id']}
            </span>
            <span style="font-family:{t['font_mono']};font-size:11px;color:{t['gray']};
                         text-transform:uppercase;letter-spacing:0.5px;">
              {story.get('source', '')}
            </span>
            <span style="font-family:{t['font_mono']};font-size:11px;color:{vibe_color};
                         margin-left:auto;text-transform:uppercase;">
              {story.get('vibe', '')}
            </span>
          </div>

          <!-- Headline -->
          <h2 style="font-family:{t['font_head']};font-size:20px;font-weight:800;
                     color:{t['ink']};line-height:1.3;margin:0 0 16px 0;">
            {story.get('headline', '')}
          </h2>

          {meme_html}

          <!-- 3 content blocks -->
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
            <tr>
              <td style="vertical-align:top;padding-right:8px;width:33%;">
                <div style="font-family:{t['font_mono']};font-size:10px;font-weight:700;
                            color:{t['accent']};text-transform:uppercase;letter-spacing:0.5px;
                            margin-bottom:6px;">What Happened</div>
                <p style="font-family:{t['font_body']};font-size:14px;color:{t['gray']};
                          line-height:1.6;margin:0;">
                  {story.get('what', '')}
                </p>
              </td>
              <td style="vertical-align:top;padding:0 8px;width:33%;">
                <div style="font-family:{t['font_mono']};font-size:10px;font-weight:700;
                            color:#22c55e;text-transform:uppercase;letter-spacing:0.5px;
                            margin-bottom:6px;">Why It Matters</div>
                <p style="font-family:{t['font_body']};font-size:14px;color:{t['gray']};
                          line-height:1.6;margin:0;">
                  {story.get('why', '')}
                </p>
              </td>
              <td style="vertical-align:top;padding-left:8px;width:33%;">
                <div style="font-family:{t['font_mono']};font-size:10px;font-weight:700;
                            color:#f59e0b;text-transform:uppercase;letter-spacing:0.5px;
                            margin-bottom:6px;">Use Today</div>
                <p style="font-family:{t['font_body']};font-size:14px;color:{t['gray']};
                          line-height:1.6;margin:0;">
                  {story.get('use_today', '')}
                </p>
              </td>
            </tr>
          </table>

          <!-- Roast line -->
          <div style="background:{t['bg']};border:1px solid {t['border']};border-left:3px solid {t['accent']};
                      border-radius:6px;padding:12px 16px;">
            <span style="font-family:{t['font_mono']};font-size:11px;font-weight:700;
                         color:{t['accent']};margin-right:8px;">🔥 ROAST:</span>
            <span style="font-family:{t['font_body']};font-size:14px;color:{t['ink']};
                         font-style:italic;">
              {story.get('roast', '')}
            </span>
          </div>
        </div>
        """

    # Power move
    power_move_html = f"""
    <div style="background:{t['accent']};border-radius:10px;padding:28px;margin:28px 0;text-align:center;">
      <div style="font-family:{t['font_mono']};font-size:12px;font-weight:700;color:rgba(255,255,255,0.8);
                  text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">
        ⚡ TODAY'S POWER MOVE
      </div>
      <p style="font-family:{t['font_head']};font-size:20px;font-weight:700;color:#fff;
                line-height:1.4;margin:0 0 12px 0;">
        {brief.get('power_move', '')}
      </p>
      <div style="display:inline-block;background:rgba(0,0,0,0.2);border-radius:20px;
                  padding:6px 16px;font-family:{t['font_mono']};font-size:12px;color:rgba(255,255,255,0.9);">
        ⏱ {brief.get('power_move_time', '15 min')}
      </div>
    </div>
    """

    # Stats footer
    stats_html = f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background:{t['surface']};border:1px solid {t['border']};
                  border-radius:8px;margin-bottom:24px;">
      <tr>
        <td style="text-align:center;padding:20px;border-right:1px solid {t['border']};">
          <div style="font-family:{t['font_mono']};font-size:28px;font-weight:700;color:{t['accent']};">
            {brief.get('stat_stories', '5')}
          </div>
          <div style="font-family:{t['font_mono']};font-size:10px;color:{t['gray']};
                      text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">Stories Today</div>
        </td>
        <td style="text-align:center;padding:20px;border-right:1px solid {t['border']};">
          <div style="font-family:{t['font_mono']};font-size:28px;font-weight:700;color:#22c55e;">
            {brief.get('stat_cost', '₹0')}
          </div>
          <div style="font-family:{t['font_mono']};font-size:10px;color:{t['gray']};
                      text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">Your Cost</div>
        </td>
        <td style="text-align:center;padding:20px;">
          <div style="font-family:{t['font_mono']};font-size:28px;font-weight:700;color:#3b82f6;">
            {brief.get('power_move_time', '15 min')}
          </div>
          <div style="font-family:{t['font_mono']};font-size:10px;color:{t['gray']};
                      text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">To Implement</div>
        </td>
      </tr>
    </table>
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Roast Brief — {display_date}</title>
</head>
<body style="margin:0;padding:0;background:{t['bg']};font-family:{t['font_body']};">

<!-- WRAPPER -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{t['bg']};">
<tr><td align="center" style="padding:24px 16px;">

<!-- CONTAINER -->
<table width="640" cellpadding="0" cellspacing="0"
       style="max-width:640px;width:100%;">

  <!-- HEADER -->
  <tr><td style="background:{t['ink']};border-radius:12px 12px 0 0;padding:28px 32px;">
    <div style="font-family:{t['font_head']};font-size:28px;font-weight:800;
                color:{t['accent']};letter-spacing:-0.5px;">
      {label}
    </div>
    <div style="font-family:{t['font_mono']};font-size:12px;color:rgba(255,255,255,0.5);
                margin-top:6px;text-transform:uppercase;letter-spacing:0.5px;">
      {display_date} &nbsp;·&nbsp; Episode #{episode} &nbsp;·&nbsp; {style} Edition
    </div>
    <div style="font-family:{t['font_body']};font-size:16px;color:rgba(255,255,255,0.8);
                margin-top:10px;font-style:italic;">
      {brief.get('tagline', '')}
    </div>
  </td></tr>

  <!-- BODY -->
  <tr><td style="background:{t['bg']};padding:28px 32px;
                 border:1px solid {t['border']};border-top:none;">

    {story_cards}
    {power_move_html}
    {stats_html}

    <!-- FOOTER -->
    <div style="text-align:center;padding-top:16px;border-top:1px solid {t['border']};">
      <p style="font-family:{t['font_mono']};font-size:11px;color:{t['gray']};margin:0;">
        AI Roast Brief &nbsp;·&nbsp; Daily at 7AM IST &nbsp;·&nbsp; Powered by CrewAI + Groq
      </p>
      <p style="font-family:{t['font_mono']};font-size:11px;color:{t['gray']};margin:6px 0 0 0;">
        Tomorrow brings more. Stay curious. Stay dangerous.
      </p>
    </div>

  </td></tr>
</table>
<!-- END CONTAINER -->

</td></tr>
</table>
<!-- END WRAPPER -->

</body>
</html>"""

    return html
