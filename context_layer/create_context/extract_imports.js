const fs=require("fs");
const path=require("path");
const configPath = path.join(__dirname, "config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const CONTEXT_DATA_PATH = config["context_data"]["path"];

const files=JSON.parse(
  fs.readFileSync(`${CONTEXT_DATA_PATH}files.json`, "utf8")
);

const imports={};

for(const file of files){

  const code=fs.readFileSync(file,"utf8");

  const lines=code.split("\n");

  const map={};

  for(const l of lines){

    if(!l.startsWith("import")) continue;

    const pkg=l.replace("import","")
               .replace(";","")
               .trim();

    const name=pkg.split(".").pop();

    map[name]=pkg;

  }

  imports[file]=map;

}

fs.writeFileSync(
  `${CONTEXT_DATA_PATH}imports.json`,
  JSON.stringify(imports,null,2)
);

console.log("imports.json generated");