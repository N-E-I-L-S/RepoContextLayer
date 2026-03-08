const fs=require("fs");

const files=JSON.parse(
  fs.readFileSync("context_data/files.json","utf8")
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
  "context_data/imports.json",
  JSON.stringify(imports,null,2)
);

console.log("imports.json generated");