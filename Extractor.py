import os

def extract_snippet_method(file_path, location):
    if not os.path.exists(file_path):
        return None

    start_line = location["start"]["line"]
    end_line = location["end"]["line"]

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Lines are 1-based in your JSON
    snippet = lines[start_line - 1:end_line]

    return "".join(snippet)


# Example usage
location = {
    "start": {"line": 12, "column": 0},
    "end": {"line": 13, "column": 1}
}

print(extract_snippet_method(
    "inventory-service\\src\\main\\java\\com\\neil\\microservices\\inventory\\controller\\InventoryController.java",
    location
))