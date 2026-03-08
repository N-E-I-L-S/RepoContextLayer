const fs=require("fs");

const context=JSON.parse(
  fs.readFileSync("context_data/repo-context.json","utf8")
);

const classIndex=JSON.parse(
  fs.readFileSync("context_data/class-index.json","utf8")
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
  "context_data/resolved-types.json",
  JSON.stringify(resolved,null,2)
);

console.log("resolved-types.json generated");