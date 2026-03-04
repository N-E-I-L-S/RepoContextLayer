const fs = require("fs");
const path = require("path");
const Parser = require("tree-sitter");
const Java = require("tree-sitter-java");

const parser = new Parser();
parser.setLanguage(Java);

const repoNodes = [];
const classFieldMap = {};

function getText(node, code) {
    return code.slice(node.startIndex, node.endIndex);
}

function getLocation(node) {
    return {
        start: {
            line: node.startPosition.row + 1,
            column: node.startPosition.column,
        },
        end: {
            line: node.endPosition.row + 1,
            column: node.endPosition.column,
        },
    };
}

function walk(node, callback) {
    callback(node);
    for (let i = 0; i < node.namedChildCount; i++) {
        walk(node.namedChild(i), callback);
    }
}

/* -------------------- LAYER DETECTION -------------------- */

function detectLayer(filePath, classNode, code) {
    const lowerPath = filePath.toLowerCase();

    if (lowerPath.includes("\\controller\\")) return "controller";
    if (lowerPath.includes("\\service\\")) return "service";
    if (lowerPath.includes("\\repository\\")) return "repository";
    if (lowerPath.includes("\\dao\\")) return "dao";
    if (lowerPath.includes("\\dto\\")) return "dto";
    if (lowerPath.includes("\\model\\") || lowerPath.includes("\\entity\\")) return "model";

    let detected = null;

    walk(classNode.parent || classNode, (child) => {
        if (child.type === "marker_annotation" || child.type === "annotation") {
            const text = getText(child, code);

            if (text.includes("RestController")) detected = "controller";
            if (text.includes("Controller")) detected = "controller";
            if (text.includes("Service")) detected = "service";
            if (text.includes("Repository")) detected = "repository";
            if (text.includes("Entity")) detected = "model";
        }
    });

    return detected || "unknown";
}

/* -------------------- REPOSITORY MODEL EXTRACTION -------------------- */

function extractRepositoryModel(node, code) {
    const text = getText(node, code);

    const jpaMatch = text.match(/JpaRepository<\s*([A-Za-z0-9_]+)\s*,/);
    if (jpaMatch) return jpaMatch[1];

    const crudMatch = text.match(/CrudRepository<\s*([A-Za-z0-9_]+)\s*,/);
    if (crudMatch) return crudMatch[1];

    return null;
}

/* -------------------- JAVA FILE ANALYSIS -------------------- */

function analyzeJavaFile(filePath) {
    const code = fs.readFileSync(filePath, "utf8");
    const tree = parser.parse(code);
    const root = tree.rootNode;

    let currentClass = null;
    let currentLayer = "unknown";

    walk(root, (node) => {

        /* -------- CLASS / INTERFACE -------- */

        if (
            node.type === "class_declaration" ||
            node.type === "interface_declaration"
        ) {
            const nameNode = node.childForFieldName("name");
            if (!nameNode) return;

            currentClass = getText(nameNode, code);

            if (!classFieldMap[currentClass]) {
                classFieldMap[currentClass] = [];
            }

            currentLayer = detectLayer(filePath, node, code);
            const location = getLocation(node);

            const repositoryModel =
                currentLayer === "repository"
                    ? extractRepositoryModel(node, code)
                    : null;

            if (currentLayer === "repository") {
                repoNodes.push({
                    id: currentClass,
                    type: "repository",
                    layer: "repository",
                    class: currentClass,
                    model: repositoryModel,
                    file: filePath,
                    location,
                });
            }

            if (currentLayer === "model") {
                repoNodes.push({
                    id: currentClass,
                    type: "model",
                    layer: "model",
                    class: currentClass,
                    file: filePath,
                    location,
                });
            }

            if (currentLayer === "dto") {
                repoNodes.push({
                    id: currentClass,
                    type: "dto",
                    layer: "dto",
                    class: currentClass,
                    file: filePath,
                    location,
                });
            }
        }

        /* -------- FIELD -------- */

        if (node.type === "field_declaration" && currentClass) {
            const typeNode = node.childForFieldName("type");
            const typeText = typeNode ? getText(typeNode, code) : "unknown";
            const location = getLocation(node);

            walk(node, (child) => {
                if (child.type === "variable_declarator") {
                    const nameNode = child.childForFieldName("name");
                    if (!nameNode) return;

                    const fieldName = getText(nameNode, code);
                    classFieldMap[currentClass].push(fieldName);

                    repoNodes.push({
                        id: `${currentClass}.${fieldName}`,
                        type: "field",
                        layer: currentLayer,
                        class: currentClass,
                        name: fieldName,
                        fieldType: typeText,
                        file: filePath,
                        location,
                    });
                }
            });
        }

        /* -------- METHOD -------- */

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
            const location = getLocation(node);

            walk(node, (child) => {

                if (child.type === "method_invocation") {
                    const methodNode = child.childForFieldName("name");
                    if (methodNode) {
                        calls.push(getText(methodNode, code));
                    }
                }

                if (child.type === "identifier") {
                    const name = getText(child, code);
                    const classFields = classFieldMap[currentClass] || [];

                    if (classFields.includes(name)) {
                        reads.push(`${currentClass}.${name}`);
                    }
                }

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
                layer: currentLayer,
                class: currentClass,
                method: methodName,
                file: filePath,
                returnType,
                parameters,
                calls,
                reads: [...new Set(reads)],
                writes: [...new Set(writes)],
                location,
            });
        }
    });
}

/* -------------------- REPO WALKER -------------------- */

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
        ".mvn",
    ];

    function walkDir(dir) {
        let files;
        try {
            files = fs.readdirSync(dir);
        } catch {
            return;
        }

        for (const file of files) {
            if (ignoreDirs.includes(file)) continue;

            const fullPath = path.join(dir, file);

            let stat;
            try {
                stat = fs.lstatSync(fullPath);
            } catch {
                continue;
            }

            if (stat.isSymbolicLink()) continue;

            if (stat.isDirectory()) {
                walkDir(fullPath);
            } else if (file.endsWith(".java")) {
                analyzeJavaFile(fullPath);
            }
        }
    }

    walkDir(rootDir);

    fs.mkdirSync("context_data", { recursive: true });

    fs.writeFileSync(
        "context_data/repo-context.json",
        JSON.stringify(repoNodes, null, 2)
    );

    console.log("repo-context.json generated successfully.");
}

/* -------------------- RUN -------------------- */

analyzeRepo("./");