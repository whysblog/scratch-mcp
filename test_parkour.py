import sys, os, json, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.project import Project

p = Project()
sid = p.add_target("Stage", True, "<svg width='480' height='360'></svg>")
pid = p.add_target("Player", False, "<svg width='32' height='48'></svg>", -150, -80)
oid = p.add_target("Obstacle", False, "<svg width='24' height='32'></svg>", 250, -80)
p.add_variable(sid, "Score", 0)
p.add_variable(pid, "gravity", 0)

# Player main script
p.add_block(pid, "event_whenflagclicked", top_level=True, x=50, y=0, block_id="p0")
p.add_block(pid, "data_setvariableto", fields={"VARIABLE": "gravity"}, inputs={"VALUE": "0"}, next_block_id="p2", block_id="p1")
p.add_block(pid, "data_setvariableto", fields={"VARIABLE": "Score"}, inputs={"VALUE": "0"}, next_block_id="p3", block_id="p2")
p.add_block(pid, "looks_show", next_block_id="p4", block_id="p3")
p.add_block(pid, "motion_gotoxy", inputs={"X": "-150", "Y": "-80"}, next_block_id="p5", block_id="p4")
p.add_block(pid, "control_forever", inputs={"SUBSTACK": "p6"}, block_id="p5")
p.add_block(pid, "data_changevariableby", fields={"VARIABLE": "gravity"}, inputs={"VALUE": "-0.8"}, next_block_id="p7", block_id="p6")
p.add_block(pid, "data_variable", fields={"VARIABLE": "gravity"}, block_id="p7r")
p.add_block(pid, "motion_changeyby", inputs={"DY": "p7r"}, next_block_id="p8", block_id="p7")
p.add_block(pid, "motion_yposition", block_id="p8y")
p.add_block(pid, "operator_lt", inputs={"OPERAND1": "p8y", "OPERAND2": "-80"}, block_id="p8c")
p.add_block(pid, "control_if", inputs={"CONDITION": "p8c", "SUBSTACK": "p8a"}, next_block_id="p9", block_id="p8")
p.add_block(pid, "motion_sety", inputs={"Y": "-80"}, next_block_id="p8b", block_id="p8a")
p.add_block(pid, "data_setvariableto", fields={"VARIABLE": "gravity"}, inputs={"VALUE": "0"}, block_id="p8b")
p.add_block(pid, "sensing_keypressed", inputs={"KEY_OPTION": "space"}, block_id="p9k")
p.add_block(pid, "data_variable", fields={"VARIABLE": "gravity"}, block_id="p9r")
p.add_block(pid, "operator_equals", inputs={"OPERAND1": "p9r", "OPERAND2": "0"}, block_id="p9e")
p.add_block(pid, "operator_and", inputs={"OPERAND1": "p9k", "OPERAND2": "p9e"}, block_id="p9c")
p.add_block(pid, "control_if", inputs={"CONDITION": "p9c", "SUBSTACK": "p9a"}, next_block_id="pA", block_id="p9")
p.add_block(pid, "data_setvariableto", fields={"VARIABLE": "gravity"}, inputs={"VALUE": "14"}, block_id="p9a")
p.add_block(pid, "sensing_touchingobject", inputs={"TOUCHINGOBJECTMENU": "Obstacle"}, block_id="pAc")
p.add_block(pid, "control_if", inputs={"CONDITION": "pAc", "SUBSTACK": "pAa"}, next_block_id="pB", block_id="pA")
p.add_block(pid, "control_stop", fields={"STOP_OPTION": "all"}, block_id="pAa")
p.add_block(pid, "control_wait", inputs={"DURATION": "0.016"}, block_id="pB")

# Score timer
p.add_block(pid, "event_whenflagclicked", top_level=True, x=50, y=200, block_id="ps0")
p.add_block(pid, "control_forever", inputs={"SUBSTACK": "ps2"}, block_id="ps1")
p.add_block(pid, "control_wait", inputs={"DURATION": "1"}, next_block_id="ps3", block_id="ps2")
p.add_block(pid, "data_changevariableby", fields={"VARIABLE": "Score"}, inputs={"VALUE": "1"}, block_id="ps3")
p.link_next(pid, "ps0", "ps1")

# Obstacle spawner
p.add_block(oid, "event_whenflagclicked", top_level=True, x=50, y=0, block_id="o0")
p.add_block(oid, "looks_hide", next_block_id="o2", block_id="o1")
p.add_block(oid, "control_forever", inputs={"SUBSTACK": "o3"}, block_id="o2")
p.add_block(oid, "operator_random", inputs={"FROM": "1", "TO": "2.5"}, block_id="o3r")
p.add_block(oid, "control_wait", inputs={"DURATION": "o3r"}, next_block_id="o4", block_id="o3")
p.add_block(oid, "control_create_clone_of", inputs={"CLONE_OPTION": "_myself_"}, block_id="o4")

# Obstacle clone
p.add_block(oid, "control_when_started_as_clone", top_level=True, x=50, y=200, block_id="o10")
p.add_block(oid, "looks_show", next_block_id="o12", block_id="o11")
p.add_block(oid, "motion_gotoxy", inputs={"X": "250", "Y": "-80"}, next_block_id="o13", block_id="o12")
p.add_block(oid, "control_forever", inputs={"SUBSTACK": "o14"}, block_id="o13")
p.add_block(oid, "motion_xposition", block_id="o14x")
p.add_block(oid, "operator_lt", inputs={"OPERAND1": "o14x", "OPERAND2": "-260"}, block_id="o14c")
p.add_block(oid, "control_if", inputs={"CONDITION": "o14c", "SUBSTACK": "o14a"}, next_block_id="o15", block_id="o14")
p.add_block(oid, "control_delete_this_clone", block_id="o14a")
p.add_block(oid, "motion_changexby", inputs={"DX": "-5"}, next_block_id="o16", block_id="o15")
p.add_block(oid, "control_wait", inputs={"DURATION": "0.016"}, block_id="o16")

# Fix links
p.link_next(pid, "p0", "p1")
p.link_next(oid, "o10", "o11")

out = p.export_sb3()
print(f"OK: {out}")
with zipfile.ZipFile(out) as zf:
    d = json.loads(zf.read("project.json"))
    for t in d["targets"]:
        print(f"  {t['name']}: {len(t['blocks'])} blocks")
        for bid, b in sorted(t["blocks"].items(), key=lambda x: (x[1].get("y",0), x[1].get("x",0), x[0])):
            fi = list(b["fields"].keys()) if b["fields"] else []
            ii = list(b["inputs"].keys()) if b["inputs"] else []
            sh = b["shadow"]
            print(f"    {bid}: {b['opcode']} sh={sh} tl={b['topLevel']} parent={b['parent']} next={b['next']} fields={fi} inputs={ii}")
