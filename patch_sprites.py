with open("frontend/js/rpg_modules/06_sprites.js", "r", encoding="utf-8") as f:
    text = f.read()

old_code = """        if (bIdKey.includes("roshan") || bIdKey.includes("рошан")) assetKey = "roshan";
        else if (bIdKey.includes("terrorblade") || bIdKey.includes("террорблейд")) assetKey = "terrorblade";
        else if (bIdKey.includes("void") || bIdKey.includes("хроно") || bIdKey.includes("faceless")) assetKey = "faceless_void";"""

new_code = """        if (bIdKey.includes("roshan") || bIdKey.includes("рошан") || bIdKey.includes("огненный демон")) assetKey = "roshan";
        else if (bIdKey.includes("terrorblade") || bIdKey.includes("террорблейд") || bIdKey.includes("демон бездны")) assetKey = "terrorblade";
        else if (bIdKey.includes("void") || bIdKey.includes("хроно") || bIdKey.includes("faceless") || bIdKey.includes("хроно-владыка")) assetKey = "faceless_void";
        else if (bIdKey.includes("мясник") || bIdKey.includes("butcher")) assetKey = "butcher";
        else if (bIdKey.includes("повелитель теней") || bIdKey.includes("shadow")) assetKey = "shadow_lord";"""

if old_code in text:
    text = text.replace(old_code, new_code)
    with open("frontend/js/rpg_modules/06_sprites.js", "w", encoding="utf-8") as f:
        f.write(text)
    print("Patched!")
else:
    print("Old code not found!")
