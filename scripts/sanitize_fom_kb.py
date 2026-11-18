from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend" / "app" / "db" / "fom_kb_seed.py"
t = p.read_text(encoding="utf-8")
repls = [
    ("Task Manager", "vazifalar oynasi"),
    ("End task", "to'xtating"),
    ("Run as administrator", "administrator huquqi bilan oching"),
    ("Restart", "qayta yoqing"),
    ("Ready", "tayyor"),
    ("Online", "ulangan"),
    ("Offline", "ulanmagan"),
]
for a, b in repls:
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("fom_kb_seed sanitized")
