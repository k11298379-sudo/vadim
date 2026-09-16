import re

with open("backend/db/crud/rpg/creeps.py", "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    ('"РОШАН СВИРЕПЫЙ (Roshan)"', '"Огненный Демон"'),
    ('"Левиафан Бездны (Tidehunter)"', '"Король Кракенов"'),
    ('"Повелитель Душ (Nevermore)"', '"Тёмный Жнец"'),
    ('"Чумной Владыка (Necrophos)"', '"Высший Некромант"'),
    ('"Демиург Арсенала (Invoker)"', '"Архимаг Хаоса"'),
    ('"Всадник Хаоса (Chaos Knight)"', '"Тёмный Рыцарь"'),
    ('"Вестник Апокалипсиса (Doom)"', '"Владыка Преисподней"'),
    ('"Первобытный Титан (Primal Beast)"', '"Древний Бегемот"'),
    ('"Призрачный Рошан Хаоса"', '"Призрачный Дракон"'),
    ('"Пожиратель Миров (Enigma Cosmic)"', '"Космический Ужас"')
]

for old, new in replacements:
    text = text.replace(old, new)

with open("backend/db/crud/rpg/creeps.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Done")
