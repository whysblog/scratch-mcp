from mcp.server.fastmcp import FastMCP
from src.project import Project

_projects = {}

mcp = FastMCP("scratch-mcp")

@mcp.tool()
def create_project() -> str:
    """Create a new Scratch project. Returns project ID."""
    pid = f"p{len(_projects)}"
    _projects[pid] = Project()
    return pid

@mcp.tool()
def add_sprite(project_id: str, name: str, svg: str, x: float = 0, y: float = 0, size: float = 100, visible: bool = True) -> str:
    """Add a sprite to the project. Returns target ID."""
    proj = _projects.get(project_id)
    if not proj: raise ValueError(f"Project {project_id} not found")
    return proj.add_target(name, False, svg, x, y, size, visible)

@mcp.tool()
def add_backdrop(project_id: str, svg: str) -> str:
    """Add backdrop to stage. Returns target ID (stage is always t0)."""
    proj = _projects.get(project_id)
    if not proj: raise ValueError(f"Project {project_id} not found")
    # Stage is first target
    if not any(t["isStage"] for t in proj.targets):
        proj.add_target("Stage", True, svg)
    return "t0"

@mcp.tool()
def add_variable(project_id: str, target_id: str, name: str, default: float = 0) -> str:
    """Add a variable to a target. Returns variable ID."""
    proj = _projects.get(project_id)
    if not proj: raise ValueError(f"Project {project_id} not found")
    return proj.add_variable(target_id, name, default)

@mcp.tool()
def add_block(project_id: str, target_id: str, opcode: str, fields: dict = None,
              inputs: dict = None, next_block_id: str = None,
              top_level: bool = False, x: int = 0, y: int = 0,
              block_id: str = None) -> str:
    """Add a block to a target's script. Returns block ID.

    Common opcodes:
      Event: event_whenflagclicked, event_whenkeypressed, event_broadcast
      Motion: motion_gotoxy, motion_changexby, motion_setx, motion_changeyby, motion_sety, motion_xposition, motion_yposition, motion_movesteps, motion_pointindirection, motion_ifonedgebounce, motion_glidesecstoxy
      Looks: looks_show, looks_hide, looks_say, looks_sayforsecs, looks_switchcostumeto, looks_nextcostume, looks_changeeffectby, looks_seteffectto
      Sound: sound_play, sound_playuntildone
      Control: control_wait, control_repeat, control_forever, control_if, control_if_else, control_stop, control_create_clone_of, control_delete_this_clone, control_when_started_as_clone
      Sensing: sensing_keypressed, sensing_touchingobject, sensing_touchingcolor, sensing_askandwait, sensing_answer, sensing_resettimer, sensing_timer, sensing_current, sensing_mousedown, sensing_mousex, sensing_mousey
      Operators: operator_add, operator_subtract, operator_multiply, operator_divide, operator_random, operator_lt, operator_equals, operator_gt, operator_and, operator_or, operator_not, operator_join, operator_length, operator_compute, operator_round, operator_mod
      Variables: data_setvariableto, data_changevariableby, data_variable
      My Blocks: procedures_definition (custom), procedures_call

    Input values:
      - number or string: creates a literal block automatically
      - "lit:<value>": explicit literal (e.g. "lit:hello")
      - "var:<name>": references a variable by name
      - block_id string: references another block's output

    Field values:
      - For VARIABLE field: variable name string
      - For STOP_OPTION: "all", "this script", or "other scripts in sprite"
      - For KEY_OPTION: "space", "up arrow", "down arrow", "left arrow", "right arrow", "a"..."z", "any"

    block_id: optional custom block ID for forward references. Use meaningful names like "main_loop" or "jump_check" to make scripts easier to build.
    """
    proj = _projects.get(project_id)
    if not proj: raise ValueError(f"Project {project_id} not found")
    return proj.add_block(target_id, opcode, fields, inputs, next_block_id, top_level, x, y, block_id)

@mcp.tool()
def link_next(project_id: str, target_id: str, block_id: str, next_block_id: str) -> bool:
    """Chain two blocks within a target (set block.next = next_block_id). Returns success.
    Use add_block's next_block_id for simple chains; link_next is for where you need to connect blocks added separately."""
    proj = _projects.get(project_id)
    if not proj: raise ValueError(f"Project {project_id} not found")
    return proj.link_next(target_id, block_id, next_block_id)

@mcp.tool()
def set_input_block(project_id: str, target_id: str, block_id: str, input_name: str, provider_block_id: str) -> bool:
    """Connect a block as input to another block's input slot. See add_block doc for input names."""
    proj = _projects.get(project_id)
    if not proj: raise ValueError(f"Project {project_id} not found")
    return proj.set_input_block(target_id, block_id, input_name, provider_block_id)

@mcp.tool()
def export_sb3(project_id: str, output_dir: str = None, filename: str = "project.sb3") -> str:
    """Generate the sb3 file and return its path."""
    proj = _projects.get(project_id)
    if not proj: raise ValueError(f"Project {project_id} not found")
    return proj.export_sb3(output_dir, filename)

if __name__ == "__main__":
    mcp.run()
