import json, zipfile
with zipfile.ZipFile(r"C:\Visual Studio Code\C++\2026.7.10\project.sb3") as zf:
    d = json.loads(zf.read("project.json"))
for t in d["targets"]:
    print(f"--- {t['name']} ---")
    for bid, b in sorted(t["blocks"].items(), key=lambda x: (x[1].get("y",0), x[1].get("x",0), x[0])):
        fi = list(b["fields"].keys()) if b["fields"] else []
        ii = list(b["inputs"].keys()) if b["inputs"] else []
        print(f"  {bid}: {b['opcode']} sh={b['shadow']} tl={b['topLevel']} parent={b['parent']} next={b['next']} fields={fi} inputs={ii}")
