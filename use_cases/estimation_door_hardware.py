"""Derive door hardware from checked physical leaves and opening evidence."""

from collections import Counter, defaultdict
import re

from use_cases.estimation_cb_geometry_parts import part
from use_cases.estimation_v9_inventory import _overlap, page_box


DOOR_OPENING_ROLES = {"door_without_handle", "door_with_pull"}
_HANDLE_NOTE = re.compile(r"(?:без\s+ручек|no\s+handles|handleless|be3\s+py[cu]ek)", re.I)
_HANDLE_LABEL = re.compile(r"(?:ручки|руки|handles|pyku)", re.I)
_DOOR_LABEL = re.compile(r"(?:петли|hinges|двери|doors)", re.I)
_PUSH_NOTE = re.compile(r"\b(?:с\s+толкателем|push[- ]to[- ]open|tip[- ]on)\b", re.I)


def _opening_note_refs(input_row):
    refs = []
    for block in input_row["input_payload"]["evidence"].get("ocr_blocks", ()):
        if not block.get("block_ref"):
            continue
        for line in block["text"].splitlines():
            label, colon, value = re.sub(r"^\d+[.)]\s*", "", line.strip()).partition(":")
            note = (value if colon else label).strip(" .;")
            label = label.strip()
            door_label = _DOOR_LABEL.fullmatch(label)
            no_handles = (not colon or _HANDLE_LABEL.fullmatch(label) or door_label) and _HANDLE_NOTE.fullmatch(note)
            specified_push = colon and door_label and _PUSH_NOTE.search(note)
            if no_handles or specified_push:
                refs.append(block["block_ref"])
                break
    return refs


def add_push_latches(parts, analyze, views, input_rows):
    """Count one latch per grounded hinged door with confirmed opening evidence."""
    inputs = {row["input_payload"]["object"]["object_id"]: row for row in input_rows}
    for oid, obj in parts["objects"].items():
        front = analyze["objects"][oid]["front"]
        leaves = defaultdict(list)
        for face in front["faces"]:
            if face["role"] == "hinged_door" and face.get("candidate_id") and face.get("bbox_px"):
                leaves[face["view_id"]].append(face)
        observations = defaultdict(set)
        for finding in front.get("door_opening_observations", ()):
            source = finding["source"]
            view = views[source["view_id"]]
            if not source.get("bbox_normalized"):
                continue
            matches = []
            for face in leaves[source["view_id"]]:
                box = page_box(face["bbox_px"], view, size=(view["width"], view["height"]))
                if _overlap(box, source["bbox_normalized"]) >= .65:
                    matches.append(f"{face['view_id']}:{face['candidate_id']}")
            if len(matches) == 1:
                observations[matches[0]].add(finding["role"])

        note_refs = _opening_note_refs(inputs[oid]) if oid in inputs else []
        scopes = [*obj["blocks"], *obj["shared_parts"]]
        grounded = {f"{face['view_id']}:{face['candidate_id']}" for faces in leaves.values() for face in faces}
        door_counts = Counter(row.get("instance_ref") for scope in scopes for row in scope["parts"]
                              if row["role"] == "door_front")
        installed = {row.get("instance_ref") for scope in scopes for row in scope["parts"]
                     if row["role"] == "push_latch"}
        for scope in scopes:
            for door in tuple(scope["parts"]):
                ref = door.get("instance_ref")
                if (door["role"] != "door_front" or ref not in grounded or ref in installed
                        or door_counts[ref] != 1 or type(door.get("quantity")) is not int or door["quantity"] < 1):
                    continue
                visual = observations[ref]
                if "door_with_pull" in visual or (not note_refs and "door_without_handle" not in visual):
                    continue
                scope["parts"].append({
                    **part("push_latch", door["quantity"], material="Push latch"),
                    "unit": "piece", "instance_ref": ref, "count_refs": [ref, *note_refs],
                    "construction_basis": "One push latch per hinged leaf with no visible pull or explicit hardware specification.",
                })
