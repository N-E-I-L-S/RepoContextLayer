import json
import os

configPath = os.path.join(os.path.dirname(__file__), "config.json")
with open(configPath, "r") as f:
    config = json.load(f)

CONTEXT_DATA_PATH = config["context_data"]["path"]


def load(name):
    with open(os.path.join(CONTEXT_DATA_PATH, name), "r", encoding="utf-8") as f:
        return json.load(f)


repo = load("repo-context.json")
class_index = load("class-index.json")
imports = load("imports.json")
di_map = load("di-map.json")
resolved_types = load("resolved-types.json")

forward = {}
reverse = {}

method_index = {}
class_method_index = {}
class_methods = {}
repository_classes = set()

# ------------------------------------------------
# Build method indexes
# ------------------------------------------------

for node in repo:

    if node["type"] != "method":
        continue

    cls = node["class"]
    method = node["method"]

    full = f"{cls}.{method}"

    method_index.setdefault(method, []).append(full)
    class_method_index[full] = True
    class_methods.setdefault(cls, []).append(full)

    forward.setdefault(full, [])

# ------------------------------------------------
# Edge helper
# ------------------------------------------------

def add_edge(src, dst):

    if src == dst:
        return

    forward.setdefault(src, [])
    reverse.setdefault(dst, [])

    if dst not in forward[src]:
        forward[src].append(dst)

    if src not in reverse[dst]:
        reverse[dst].append(src)

# ------------------------------------------------
# Resolve direct method calls
# ------------------------------------------------

for node in repo:

    if node["type"] != "method":
        continue

    if node["type"] == "repository":
        repository_classes.add(node["class"])

    src_class = node["class"]
    src_method = node["method"]
    source = f"{src_class}.{src_method}"
    file_path = node["file"]

    for call in node.get("calls", []):

        candidates = set()

        # -------------------------------
        # STRING CALL
        # -------------------------------
        if isinstance(call, str):

            method = call

            candidates.add(f"{src_class}.{method}")

            if method in method_index:
                candidates.update(method_index[method])

        # -------------------------------
        # DICT CALL
        # -------------------------------
        elif isinstance(call, dict):

            target = call.get("target")
            obj = call.get("object")
            call_type = call.get("type")

            if not target:
                continue

            method = target.split(".")[-1]

            # explicit type
            if call_type:
                candidates.add(f"{call_type}.{method}")

            # resolved types
            if obj:
                key = f"{src_class}.{obj}"
                if key in resolved_types:
                    candidates.add(f"{resolved_types[key]}.{method}")

            # DI map
            if obj:
                key = f"{src_class}.{obj}"
                if key in di_map:
                    candidates.add(f"{di_map[key]}.{method}")

            # imports
            if file_path in imports and call_type:
                for short, full in imports[file_path].items():
                    if short == call_type:
                        cls = full.split(".")[-1]
                        candidates.add(f"{cls}.{method}")

            # same class
            candidates.add(f"{src_class}.{method}")

            # global fallback
            if method in method_index:
                candidates.update(method_index[method])

        # validate
        for c in candidates:
            if c in class_method_index:
                add_edge(source, c)
                continue

            cls = c.split(".")[0]

            if cls in repository_classes:
                forward.setdefault(c, [])
                add_edge(source, c)

# ------------------------------------------------
# Spring @Bean dependencies
# ------------------------------------------------

for node in repo:

    if node["type"] != "method":
        continue

    if "Bean" not in node.get("annotations", []):
        continue

    src = f"{node['class']}.{node['method']}"

    for call in node.get("calls", []):

        if isinstance(call, str):

            target = f"{node['class']}.{call}"

            if target in class_method_index:
                add_edge(src, target)

# ------------------------------------------------
# Field Injection (@Autowired)
# ------------------------------------------------

for node in repo:

    if node["type"] != "class":
        continue

    cls = node["class"]

    for inj in node.get("injections", []):

        target_class = inj.get("type")

        if not target_class:
            continue

        if target_class in class_methods:

            for src_method in class_methods.get(cls, []):
                for dst_method in class_methods[target_class]:
                    add_edge(src_method, dst_method)

# ------------------------------------------------
# Constructor Injection
# ------------------------------------------------

for node in repo:

    if node["type"] != "class":
        continue

    cls = node["class"]

    for ctor in node.get("constructors", []):

        for param in ctor.get("parameters", []):

            target_class = param

            if target_class in class_methods:

                for src_method in class_methods.get(cls, []):
                    for dst_method in class_methods[target_class]:
                        add_edge(src_method, dst_method)

# ------------------------------------------------
# Builder Chains
# ------------------------------------------------

for node in repo:

    if node["type"] != "method":
        continue

    src = f"{node['class']}.{node['method']}"

    for call in node.get("calls", []):

        if not isinstance(call, dict):
            continue

        target = call.get("target", "")

        if "builder" in target.lower():

            cls = target.split(".")[0]
            candidate = f"{cls}.build"

            if candidate in class_method_index:
                add_edge(src, candidate)

# ------------------------------------------------
# Layer detection
# ------------------------------------------------

def get_layer(node):

    anns = node.get("annotations", [])

    if "RestController" in anns or "Controller" in anns:
        return "controller"

    if "Service" in anns:
        return "service"

    if "Repository" in anns:
        return "repository"

    return "unknown"


class_layer = {}

for node in repo:

    if node["type"] == "class":
        class_layer[node["class"]] = node.get("layer") or get_layer(node)

# ------------------------------------------------
# Controller → Service → Repository flow
# ------------------------------------------------

for src_class, src_layer in class_layer.items():

    for dst_class, dst_layer in class_layer.items():

        if src_layer == "controller" and dst_layer == "service":

            for s in class_methods.get(src_class, []):
                for d in class_methods.get(dst_class, []):
                    add_edge(s, d)

        if src_layer == "service" and dst_layer == "repository":

            for s in class_methods.get(src_class, []):
                for d in class_methods.get(dst_class, []):
                    add_edge(s, d)

# ------------------------------------------------
# Save graph
# ------------------------------------------------

output = {
    "forward": forward,
    "reverse": reverse
}

with open(os.path.join(CONTEXT_DATA_PATH, "call_graph.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("✅ call_graph.json generated")