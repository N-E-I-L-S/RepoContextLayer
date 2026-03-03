const fs = require("fs");
const path = require("path");
const Parser = require("tree-sitter");
const Java = require("tree-sitter-java");

const parser = new Parser();
parser.setLanguage(Java);

const repoNodes = [];
const classFieldMap = {}; // { className: [fieldNames] }

function getText(node, code) {
    return code.slice(node.startIndex, node.endIndex);
}

function walk(node, callback) {
    callback(node);
    for (let i = 0; i < node.namedChildCount; i++) {
        walk(node.namedChild(i), callback);
    }
}

function analyzeJavaFile(filePath) {
    const code = fs.readFileSync(filePath, "utf8");
    const tree = parser.parse(code);
    const root = tree.rootNode;

    let currentClass = null;

    walk(root, (node) => {
        // ---- CLASS DECLARATION ----
        if (node.type === "class_declaration") {
            const nameNode = node.childForFieldName("name");
            if (!nameNode) return;

            currentClass = getText(nameNode, code);
            if (!classFieldMap[currentClass]) {
                classFieldMap[currentClass] = [];
            }
        }

        // ---- FIELD DECLARATION ----
        if (node.type === "field_declaration" && currentClass) {
            const typeNode = node.childForFieldName("type");
            const typeText = typeNode ? getText(typeNode, code) : "unknown";

            walk(node, (child) => {
                if (child.type === "variable_declarator") {
                    const nameNode = child.childForFieldName("name");
                    if (!nameNode) return;

                    const fieldName = getText(nameNode, code);
                    classFieldMap[currentClass].push(fieldName);

                    repoNodes.push({
                        id: `${currentClass}.${fieldName}`,
                        type: "field",
                        class: currentClass,
                        name: fieldName,
                        fieldType: typeText,
                        file: filePath,
                    });
                }
            });
        }

        // ---- METHOD DECLARATION ----
        if (node.type === "method_declaration" && currentClass) {
            const nameNode = node.childForFieldName("name");
            if (!nameNode) return;

            const methodName = getText(nameNode, code);

            const returnNode = node.childForFieldName("type");
            const returnType = returnNode ? getText(returnNode, code) : "void";

            const parametersNode = node.childForFieldName("parameters");
            const parameters = [];

            if (parametersNode) {
                walk(parametersNode, (paramNode) => {
                    if (paramNode.type === "formal_parameter") {
                        const typeNode = paramNode.childForFieldName("type");
                        if (typeNode) {
                            parameters.push(getText(typeNode, code));
                        }
                    }
                });
            }

            const calls = [];
            const reads = [];
            const writes = [];

            // Walk method body
            walk(node, (child) => {
                // ---- METHOD CALL ----
                if (child.type === "method_invocation") {
                    const methodNode = child.childForFieldName("name");
                    if (methodNode) {
                        calls.push(getText(methodNode, code));
                    }
                }

                // ---- FIELD READ / WRITE ----
                if (child.type === "identifier") {
                    const name = getText(child, code);
                    const classFields = classFieldMap[currentClass] || [];

                    if (classFields.includes(name)) {
                        reads.push(`${currentClass}.${name}`);
                    }
                }

                // WRITE detection
                if (child.type === "assignment_expression") {
                    const leftNode = child.childForFieldName("left");
                    if (leftNode && leftNode.type === "identifier") {
                        const name = getText(leftNode, code);
                        const classFields = classFieldMap[currentClass] || [];

                        if (classFields.includes(name)) {
                            writes.push(`${currentClass}.${name}`);
                        }
                    }
                }
            });

            repoNodes.push({
                id: `${currentClass}.${methodName}`,
                type: "method",
                class: currentClass,
                method: methodName,
                file: filePath,
                returnType,
                parameters,
                calls,
                reads: [...new Set(reads)],
                writes: [...new Set(writes)],
            });
        }
    });
}

function analyzeRepo(rootDir) {
    const ignoreDirs = [
  "target",
  ".idea",
  "generated-sources",
  "node_modules",
  "mysql",
  "data",
  "docker",
  ".git",
  ".mvn"
];

function walkDir(dir) {
  let files;

  try {
    files = fs.readdirSync(dir);
  } catch (err) {
    console.warn(`Skipping unreadable directory: ${dir}`);
    return;
  }

  for (const file of files) {
    const fullPath = path.join(dir, file);

    // 🔥 Ignore directories by name BEFORE stat
    if (ignoreDirs.includes(file)) {
      continue;
    }

    let stat;
    try {
      stat = fs.lstatSync(fullPath);
    } catch (err) {
      console.warn(`Skipping inaccessible path: ${fullPath}`);
      continue;
    }

    // Skip symbolic links (important for sockets)
    if (stat.isSymbolicLink()) {
      continue;
    }

    if (stat.isDirectory()) {
      walkDir(fullPath);
    } else if (file.endsWith(".java")) {
      analyzeJavaFile(fullPath);
    }
  }
}

    walkDir(rootDir);

    fs.writeFileSync(
        "repo-context.json",
        JSON.stringify(repoNodes, null, 2)
    );

    console.log("repo-context.json generated.");
}

// ---- RUN ----
const rootDirectory = "./";
analyzeRepo(rootDirectory);