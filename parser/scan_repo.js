const fs = require("fs");
const path = require("path");

const ignoreDirs = [
  "target",".idea","generated-sources","node_modules", "parser",
  "mysql","data","docker",".git",".mvn"
];

const files = [];

function walk(dir) {

  let list;
  try {
    list = fs.readdirSync(dir);
  } catch {
    return;
  }

  for (const file of list) {

    if (ignoreDirs.includes(file)) continue;

    const full = path.join(dir,file);

    let stat;
    try {
      stat = fs.lstatSync(full);
    } catch {
      continue;
    }

    if (stat.isSymbolicLink()) continue;

    if (stat.isDirectory()) walk(full);
    else if (file.endsWith(".java")) files.push(full);
  }
}

walk("../");

fs.writeFileSync(
  "context_data/files.json",
  JSON.stringify(files,null,2)
);

console.log("files.json generated");