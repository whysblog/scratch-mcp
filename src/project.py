import json
import hashlib
import os
import shutil
import tempfile
import zipfile
import copy
from datetime import date
from pathlib import Path
from typing import Any, Optional

_literal_counter = [0]
_shadow_counter = [0]

def _reset_counters():
    _literal_counter[0] = 0
    _shadow_counter[0] = 0

def _new_lit_id():
    _literal_counter[0] += 1
    return f"lit{_literal_counter[0]}"

def _new_shadow_id():
    _shadow_counter[0] += 1
    return f"sh{_shadow_counter[0]}"

_SHADOW_MAP = {
    "sensing_keypressed": ("KEY_OPTION", "sensing_keyoptions", "KEY_OPTION"),
    "sensing_touchingobject": ("TOUCHINGOBJECTMENU", "sensing_touchingobjectmenu", "TOUCHINGOBJECTMENU"),
    "control_create_clone_of": ("CLONE_OPTION", "control_create_clone_of_menu", "CLONE_OPTION"),
}

_VARIABLE_BLOCKS = {"data_setvariableto", "data_changevariableby", "data_variable", "data_showvariable", "data_hidevariable"}


def _is_numeric_literal(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


class Project:
    def __init__(self):
        self.targets = []
        self.extensions = []
        self._next_target_id = 0
        self._next_block_id = 0
        _reset_counters()

    def add_target(self, name: str, is_stage: bool, svg: str, x: float = 0, y: float = 0, size: float = 100, visible: bool = True) -> str:
        tid = f"t{self._next_target_id}"
        self._next_target_id += 1
        target = {
            "id": tid,
            "name": name,
            "isStage": is_stage,
            "variables": {},
            "lists": {},
            "broadcasts": {},
            "blocks": {},
            "costumes": [],
            "sounds": [],
            "volume": 100,
            "layerOrder": len(self.targets),
            "currentCostume": 0,
            "svg": svg,
            "visible": visible,
            "tempo": 60,
        }
        if not is_stage:
            target["x"] = x
            target["y"] = y
            target["size"] = size
            target["direction"] = 90
            target["draggable"] = False
            target["rotationStyle"] = "all around"
        self.targets.append(target)
        return tid

    def add_variable(self, target_id: str, name: str, default: Any = 0) -> str:
        target = self._find_target(target_id)
        vid = f"v{len(target['variables'])}"
        target["variables"][vid] = [name, default]
        return vid

    def add_block(self, target_id: str, opcode: str, fields: dict = None, inputs: dict = None,
                  next_block_id: Optional[str] = None, top_level: bool = False, x: int = 0, y: int = 0,
                  block_id: Optional[str] = None) -> str:
        target = self._find_target(target_id)
        if block_id:
            if block_id in target["blocks"]:
                raise ValueError(f"Block ID '{block_id}' already exists in target {target_id}")
            bid = block_id
        else:
            bid = f"b{self._next_block_id}"
            self._next_block_id += 1

        fields = fields or {}
        raw_inputs = inputs or {}

        parsed_inputs = {}

        variable_fields = {}
        for fk, fv in fields.items():
            if opcode in _VARIABLE_BLOCKS and fk == "VARIABLE":
                vid = self._find_variable_id(target, fv)
                variable_fields[fk] = [fv, vid]
            elif opcode == "control_stop" and fk == "STOP_OPTION":
                variable_fields[fk] = [fv, None]
            else:
                variable_fields[fk] = [fv, None]

        for ik, iv in raw_inputs.items():
            if iv is None:
                continue
            if isinstance(iv, (int, float)):
                parsed_inputs[ik] = [1, [4, str(iv)]]
            elif isinstance(iv, str):
                if iv.startswith("var:"):
                    vname = iv[4:]
                    var_block_id = f"b{self._next_block_id}"
                    self._next_block_id += 1
                    vid = self._find_variable_id(target, vname)
                    target["blocks"][var_block_id] = {
                        "opcode": "data_variable", "next": None, "parent": None,
                        "inputs": {}, "fields": {"VARIABLE": [vname, vid]},
                        "shadow": False, "topLevel": False
                    }
                    parsed_inputs[ik] = [1, var_block_id]
                elif iv.startswith("lit:"):
                    parsed_inputs[ik] = [1, [4, iv[4:]]]
                elif iv.startswith("block:"):
                    parsed_inputs[ik] = [1, iv[6:]]
                elif _is_numeric_literal(iv):
                    parsed_inputs[ik] = [1, [4, iv]]
                else:
                    parsed_inputs[ik] = [1, iv]
            else:
                parsed_inputs[ik] = [1, iv]

        block = {
            "opcode": opcode,
            "next": next_block_id,
            "parent": None,
            "inputs": parsed_inputs,
            "fields": variable_fields,
            "shadow": False,
            "topLevel": top_level,
        }
        if top_level:
            block["x"] = x
            block["y"] = y

        target["blocks"][bid] = block

        if next_block_id and next_block_id in target["blocks"]:
            nb = target["blocks"][next_block_id]
            if nb["parent"] is None:
                nb["parent"] = bid

        # Handle shadow blocks for dropdown menus with string/num inputs
        if opcode in _SHADOW_MAP:
            inp_key, shadow_opcode, shadow_field = _SHADOW_MAP[opcode]
            if inp_key in parsed_inputs:
                val = parsed_inputs[inp_key][1]
                # val is either a string (block ref) or a list [4, literal]
                if isinstance(val, str):
                    # Check if it's a literal stored as string, or a block ref
                    existing_block = target["blocks"].get(val)
                    if existing_block and existing_block.get("shadow") is True:
                        pass  # already set up
                    else:
                        # Treat as dropdown value - create shadow block
                        sid = f"b{self._next_block_id}"
                        self._next_block_id += 1
                        target["blocks"][sid] = {
                            "opcode": shadow_opcode, "next": None, "parent": None,
                            "inputs": {},
                            "fields": {shadow_field: [val, None]},
                            "shadow": True, "topLevel": False
                        }
                        parsed_inputs[inp_key] = [1, sid]
                        block["inputs"] = parsed_inputs
                        if sid in target["blocks"]:
                            target["blocks"][sid]["parent"] = bid

        return bid

    def link_next(self, target_id: str, block_id: str, next_block_id: str) -> bool:
        target = self._find_target(target_id)
        if block_id not in target["blocks"] or next_block_id not in target["blocks"]:
            return False
        target["blocks"][block_id]["next"] = next_block_id
        nb = target["blocks"][next_block_id]
        if nb["parent"] is None:
            nb["parent"] = block_id
        return True

    def set_input_block(self, target_id: str, block_id: str, input_name: str, provider_block_id: str) -> bool:
        target = self._find_target(target_id)
        if block_id not in target["blocks"] or provider_block_id not in target["blocks"]:
            return False
        target["blocks"][block_id]["inputs"][input_name] = [1, provider_block_id]
        provider = target["blocks"][provider_block_id]
        if provider["parent"] is None:
            provider["parent"] = block_id
        return True

    def _find_target(self, tid: str):
        for t in self.targets:
            if t["id"] == tid:
                return t
        raise ValueError(f"Target {tid} not found")

    def _find_variable_id(self, target, name):
        for vid, vdata in target["variables"].items():
            if vdata[0] == name:
                return vid
        if self.targets:
            for vid, vdata in self.targets[0]["variables"].items():
                if vdata[0] == name:
                    return vid
        raise ValueError(f"Variable '{name}' not found")

    def _write_svg(self, tmp, name, svg):
        p = os.path.join(tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        h = hashlib.md5()
        with open(p, "rb") as f:
            h.update(f.read())
        hx = h.hexdigest()
        dst = os.path.join(tmp, f"{hx}.svg")
        if os.path.exists(dst):
            os.remove(p)
        else:
            os.rename(p, dst)
        return hx, f"{hx}.svg"

    def export_sb3(self, output_dir: Optional[str] = None, filename: str = "project.sb3") -> str:
        targets = copy.deepcopy(self.targets)
        tmp = tempfile.mkdtemp()
        try:
            for t in targets:
                svg = t.pop("svg", None)
                t.pop("id", None)
                if svg:
                    h, fn = self._write_svg(tmp, f"{t['name']}.svg", svg)
                    cost = {"assetId": h, "name": f"{t['name']}_costume", "bitmapResolution": 1,
                            "dataFormat": "svg", "md5ext": fn}
                    if t["isStage"]:
                        cost["rotationCenterX"] = 240
                        cost["rotationCenterY"] = 180
                    else:
                        cost["rotationCenterX"] = 16
                        cost["rotationCenterY"] = 24
                    t["costumes"] = [cost]

            for t in targets:
                blocks = t["blocks"]
                # fix parents for next links
                for bid, b in list(blocks.items()):
                    nid = b.get("next")
                    if nid and nid in blocks and blocks[nid].get("parent") is None:
                        blocks[nid]["parent"] = bid
                # fix parents for input references
                for bid, b in list(blocks.items()):
                    for ikey, ival in (b.get("inputs") or {}).items():
                        if isinstance(ival, list) and len(ival) == 2 and ival[0] == 1 and isinstance(ival[1], str):
                            rid = ival[1]
                            if rid in blocks and blocks[rid].get("parent") is None:
                                blocks[rid]["parent"] = bid

            monitors = []
            for t in targets:
                for vid, vdata in t["variables"].items():
                    monitors.append({
                        "id": f"mon_{vid}", "mode": "default", "opcode": "data_variable",
                        "params": {"VARIABLE": vid},
                        "spriteName": None if t["isStage"] else t["name"],
                        "value": vdata[1] if isinstance(vdata[1], (int, float)) else 0,
                        "width": 100, "height": 30, "x": 10, "y": 10,
                        "visible": True, "min": 0, "max": 0
                    })

            project = {
                "targets": targets,
                "monitors": monitors,
                "extensions": self.extensions,
                "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "scratch-mcp"}
            }

            with open(os.path.join(tmp, "project.json"), "w", encoding="utf-8") as f:
                json.dump(project, f, ensure_ascii=False, separators=(",", ":"))

            if output_dir is None:
                today = date.today()
                output_dir = os.path.join(os.getcwd(), f"scratch-export-{today.year}.{today.month}.{today.day}")
            os.makedirs(output_dir, exist_ok=True)
            outpath = os.path.join(output_dir, Path(filename).name)

            with zipfile.ZipFile(outpath, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname in os.listdir(tmp):
                    zf.write(os.path.join(tmp, fname), fname)

            return outpath
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
