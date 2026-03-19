const fs=require("fs");
const path=require("path");

const configPath = path.join(__dirname, "config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const CONTEXT_DATA_PATH = config["context_data"]["path"];

const nodes=JSON.parse(
  fs.readFileSync(`${CONTEXT_DATA_PATH}repo-context.json`,`utf8`)
);

const di={};

for(const node of nodes){

  if(node.type!=="class") continue;

  if(!node.injections) continue;

  for(const inj of node.injections){

    di[`${node.class}.${inj.field}`]=inj.type;

  }

}

fs.writeFileSync(
  `${CONTEXT_DATA_PATH}di-map.json`,
  JSON.stringify(di,null,2)
);

console.log("di-map.json generated");