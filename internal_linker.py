import os, requests, logging

log = logging.getLogger("seo-bot.linker")

def analyze_and_fix_issue(user_command_or_error):
    """
    Direct Layout Fixer Agent for MedzPalace product tables.
    """
    return (
        "🌐 <b>MedzPalace Table Design Fix:</b>\n\n"
        "Aapki website par dono tables ko ek barabar straight line (side-by-side) mein align karne "
        "aur unka size compact chota karne ke liye niche diya gaya CSS code copy karke "
        "apne WordPress Dashboard -> <b>Appearance -> Customize -> Additional CSS</b> mein daal dijiye:\n\n"
        "<code>"
        "/* Tables ko ek line me lane ke liye */\n"
        ".product-tables-container {\n"
        "  display: flex;\n"
        "  gap: 20px;\n"
        "  justify-content: center;\n"
        "  align-items: flex-start;\n"
        "  flex-wrap: wrap;\n"
        "  margin: 20px 0;\n"
        "}\n\n"
        "/* Tables ka size compact aur tight karne ke liye */\n"
        ".product-tables-container table {\n"
        "  flex: 1;\n"
        "  min-width: 300px;\n"
        "  max-width: 48%;\n"
        "  font-size: 13px !important;\n"
        "  border-collapse: collapse;\n"
        "}\n\n"
        "/* Columns ki spacing kam karne ke liye */\n"
        ".product-tables-container th, \n"
        ".product-tables-container td {\n"
        "  padding: 6px 8px !important;\n"
        "  text-align: center;\n"
        "}\n"
        "</code>\n\n"
        "<i>💡 Tip: WordPress editor me dono tables ke upar ek div class <code>product-tables-container</code> jodh dene se tables ekdum barabar level me aa jayengi!</i>"
    )
