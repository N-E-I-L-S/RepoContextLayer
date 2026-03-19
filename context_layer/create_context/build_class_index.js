const fs=require("fs");
const path=require("path");
const configPath = path.join(__dirname, "config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const CONTEXT_DATA_PATH = config["context_data"]["path"];

const nodes=JSON.parse(
  fs.readFileSync(`${CONTEXT_DATA_PATH}repo-context.json`,`utf8`)
);

const index={};

for(const node of nodes){

  if(node.type!=="class") continue;

  index[node.class]={
    file:node.file
  };

}

fs.writeFileSync(
  "context_data/class-index.json",
  JSON.stringify(index,null,2)
);

console.log("class-index.json generated");