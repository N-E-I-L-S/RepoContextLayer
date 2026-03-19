const fs=require("fs");
const path=require("path");

const configPath = path.join(__dirname, "config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const CONTEXT_DATA_PATH = config["context_data"]["path"];

const context=JSON.parse(
  fs.readFileSync(`${CONTEXT_DATA_PATH}repo-context.json`,`utf8`)
);

const classIndex=JSON.parse(
  fs.readFileSync(`${CONTEXT_DATA_PATH}class-index.json`,`utf8`)
);

const resolved={};

for(const node of context){

  if(node.type!=="class") continue;

  for(const field of node.fields){

    const type=field.type;

    if(classIndex[type]){

      resolved[`${node.class}.${field.name}`]=type;

    }

  }

}

fs.writeFileSync(
  `${CONTEXT_DATA_PATH}resolved-types.json`,
  JSON.stringify(resolved,null,2)
);

console.log("resolved-types.json generated");