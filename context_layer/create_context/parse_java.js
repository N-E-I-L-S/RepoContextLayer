const fs = require("fs");
const path = require("path");
const Parser = require("tree-sitter");
const Java = require("tree-sitter-java");

const configPath = path.join(__dirname, "config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const CONTEXT_DATA_PATH = config["context_data"]["path"];

const parser = new Parser();
parser.setLanguage(Java);

const repoNodes = [];
const files = JSON.parse(
    fs.readFileSync(`${CONTEXT_DATA_PATH}files.json`, "utf8")
);
/* ---------------- UTIL ---------------- */

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

function extractAnnotations(node, code) {
    const annotations = [];

    walk(node, (child) => {
        if (child.type === "annotation" || child.type === "marker_annotation") {
            let text = getText(child, code);
            text = text.replace("@", "").split("(")[0].trim();
            annotations.push(text);
        }
    });

    return [...new Set(annotations)];
}

/* ---------------- LAYER DETECTION ---------------- */

function detectLayer(filePath, classNode, code) {

    const lower = filePath.toLowerCase();

    if (lower.includes("\\controller\\")) return "controller";
    if (lower.includes("\\service\\")) return "service";
    if (lower.includes("\\repository\\")) return "repository";
    if (lower.includes("\\dao\\")) return "dao";
    if (lower.includes("\\dto\\")) return "dto";
    if (lower.includes("\\model\\") || lower.includes("\\entity\\")) return "model";

    const annotations = extractAnnotations(classNode, code);

    if (annotations.includes("RestController")) return "controller";
    if (annotations.includes("Controller")) return "controller";
    if (annotations.includes("Service")) return "service";
    if (annotations.includes("Repository")) return "repository";
    if (annotations.includes("Entity")) return "model";

    return "unknown";
}

/* ---------------- REPOSITORY MODEL ---------------- */

function extractRepositoryModel(node, code) {

    const text = getText(node, code);

    const jpaMatch = text.match(/JpaRepository<\s*([A-Za-z0-9_]+)\s*,/);
    if (jpaMatch) return jpaMatch[1];

    const crudMatch = text.match(/CrudRepository<\s*([A-Za-z0-9_]+)\s*,/);
    if (crudMatch) return crudMatch[1];

    const mongoMatch = text.match(/MongoRepository<\s*([A-Za-z0-9_]+)\s*,/);
    if (mongoMatch) return mongoMatch[1];

    return null;
}

/* ---------------- JAVA FILE ANALYSIS ---------------- */

function analyzeJavaFile(filePath) {

    const code = fs.readFileSync(filePath, "utf8");
    const tree = parser.parse(code);
    const root = tree.rootNode;

    walk(root, (node) => {

        if (
            node.type !== "class_declaration" &&
            node.type !== "interface_declaration"
        ) return;

        const nameNode = node.childForFieldName("name");
        if (!nameNode) return;

        const className = getText(nameNode, code);
        const layer = detectLayer(filePath, node, code);
        const classLocation = getLocation(node);

        const fields = [];
        const injections = [];
        const methods = [];

        const fieldTypeMap = {};

        /* -------- FIELD EXTRACTION -------- */

        walk(node, (child) => {

            if (child.type !== "field_declaration") return;

            const typeNode = child.childForFieldName("type");
            const fieldType = typeNode ? getText(typeNode, code) : "unknown";

            const annotations = extractAnnotations(child, code);

            walk(child, (v) => {

                if (v.type !== "variable_declarator") return;

                const nameNode = v.childForFieldName("name");
                if (!nameNode) return;

                const fieldName = getText(nameNode, code);

                fields.push({
                    name: fieldName,
                    type: fieldType
                });

                fieldTypeMap[fieldName] = fieldType;

                if (annotations.includes("Autowired")) {
                    injections.push({
                        field: fieldName,
                        type: fieldType
                    });
                }

            });

        });

        /* -------- CONSTRUCTOR INJECTION -------- */

        walk(node, (child) => {

            if (child.type !== "constructor_declaration") return;

            const paramNode = child.childForFieldName("parameters");

            if (!paramNode) return;

            walk(paramNode, (p) => {

                if (p.type !== "formal_parameter") return;

                const typeNode = p.childForFieldName("type");
                const nameNode = p.childForFieldName("name");

                if (!typeNode || !nameNode) return;

                const type = getText(typeNode, code);
                const name = getText(nameNode, code);

                injections.push({
                    field: name,
                    type: type
                });

            });

        });

        /* -------- METHOD EXTRACTION -------- */

        walk(node, (child) => {

            if (child.type !== "method_declaration") return;

            const nameNode = child.childForFieldName("name");
            if (!nameNode) return;

            const methodName = getText(nameNode, code);
            const returnNode = child.childForFieldName("type");

            const returnType = returnNode
                ? getText(returnNode, code)
                : "void";

            const parameters = [];
            const paramTypeMap = {};
            const localVarTypes = {};

            const calls = [];
            const reads = [];
            const writes = [];

            const methodAnnotations = extractAnnotations(child, code);

            /* -------- PARAMETERS -------- */

            const paramNode = child.childForFieldName("parameters");

            if (paramNode) {
                walk(paramNode, (p) => {

                    if (p.type !== "formal_parameter") return;

                    const typeNode = p.childForFieldName("type");
                    const nameNode = p.childForFieldName("name");

                    if (!typeNode || !nameNode) return;

                    const type = getText(typeNode, code);
                    const name = getText(nameNode, code);

                    parameters.push(type);
                    paramTypeMap[name] = type;

                });
            }

            /* -------- LOCAL VARIABLES -------- */

            walk(child, (inner) => {

                if (inner.type === "local_variable_declaration") {

                    const typeNode = inner.childForFieldName("type");
                    if (!typeNode) return;

                    const type = getText(typeNode, code);

                    walk(inner, (v) => {

                        if (v.type !== "variable_declarator") return;

                        const nameNode = v.childForFieldName("name");
                        if (!nameNode) return;

                        const name = getText(nameNode, code);

                        localVarTypes[name] = type;

                    });

                }

            });

            /* -------- METHOD BODY ANALYSIS -------- */

            walk(child, (inner) => {

                /* CALLS */

                if (inner.type === "method_invocation") {

                    const objectNode = inner.childForFieldName("object");
                    const methodNode = inner.childForFieldName("name");

                    if (!methodNode) return;

                    const method = getText(methodNode, code);

                    if (!objectNode) {
                        calls.push(method);
                        return;
                    }

                    const object = getText(objectNode, code);

                    const type =
                        localVarTypes[object] ||
                        paramTypeMap[object] ||
                        fieldTypeMap[object];

                    if (type) {
                        calls.push({
                            target: `${type}.${method}`,
                            object: object,
                            type: type
                        });
                    } else {
                        calls.push(method);
                    }

                }

                /* READS */

                if (inner.type === "identifier") {

                    const name = getText(inner, code);

                    if (fieldTypeMap[name]) {
                        reads.push(`${className}.${name}`);
                    }

                }

                /* WRITES */

                if (inner.type === "assignment_expression") {

                    const left = inner.childForFieldName("left");

                    if (left && left.type === "identifier") {

                        const name = getText(left, code);

                        if (fieldTypeMap[name]) {
                            writes.push(`${className}.${name}`);
                        }

                    }

                }

            });

            const methodId = `${className}.${methodName}`;

            methods.push(methodId);

            repoNodes.push({
                id: methodId,
                type: "method",
                layer: layer,
                class: className,
                method: methodName,
                file: filePath,
                returnType,
                parameters,
                annotations: methodAnnotations,
                calls,
                reads: [...new Set(reads)],
                writes: [...new Set(writes)],
                location: getLocation(child)
            });

        });

        /* -------- CLASS NODE -------- */

        repoNodes.push({
            id: className,
            type: "class",
            layer: layer,
            class: className,
            file: filePath,
            fields,
            injections,
            methods,
            location: classLocation
        });

        /* -------- REPOSITORY NODE -------- */

        if (layer === "repository") {

            const model = extractRepositoryModel(node, code);

            repoNodes.push({
                id: className,
                type: "repository",
                layer: "repository",
                class: className,
                model,
                file: filePath,
                location: classLocation
            });

        }

        /* -------- MODEL NODE -------- */

        if (layer === "model") {

            repoNodes.push({
                id: className,
                type: "model",
                layer: "model",
                fields,
                file: filePath,
                location: classLocation
            });

        }

    });

}

/* ---------------- PASS RUNNER ---------------- */
function runPass() {

    for (const filePath of files) {
        analyzeJavaFile(filePath);
    }

    fs.mkdirSync(CONTEXT_DATA_PATH, { recursive: true });

    fs.writeFileSync(
        `${CONTEXT_DATA_PATH}repo-context.json`,
        JSON.stringify(repoNodes, null, 2)
    );
    console.log("repo-context.json generated successfully.");
    try {
        generateRepoContextDoc(repoNodes);
        console.log("repo-context.md generated successfully.");
    }
    catch (e) {
        console.error("Error generating repo-context.md:", e);
    }   
}

runPass();

/* ---------------- REPO CONTEXT DOC ---------------- */

function generateRepoContextDoc(nodes) {

    const typeCounts = {};
    const schemaMap = {};

    for (const node of nodes) {

        const type = node.type || "unknown";

        /* Count node types */

        typeCounts[type] = (typeCounts[type] || 0) + 1;

        /* Collect schema */

        if (!schemaMap[type]) {
            schemaMap[type] = new Set();
        }

        Object.keys(node).forEach(k => schemaMap[type].add(k));
    }

    const totalNodes = nodes.length;

    /* Convert schema sets → arrays */

    const schemaObj = {};
    for (const type in schemaMap) {
        schemaObj[type] = Array.from(schemaMap[type]).sort();
    }

    /* Build Markdown */

    let md = "";

    md += "# Repository Context\n\n";

    md += "## Summary\n\n";
    md += `Total Nodes: **${totalNodes}**\n\n`;

    md += "### Node Type Counts\n\n";

    for (const type in typeCounts) {
        md += `- ${type}: **${typeCounts[type]}**\n`;
    }

    md += "\n";

    md += "## Node Schemas\n\n";

    for (const type in schemaObj) {

        md += `### ${type} node\n\n`;

        md += "Fields:\n\n";

        schemaObj[type].forEach(field => {
            md += `- ${field}\n`;
        });

        md += "\n";
    }

    fs.writeFileSync(
        `${CONTEXT_DATA_PATH}repo-context.md`,
        md
    );

}