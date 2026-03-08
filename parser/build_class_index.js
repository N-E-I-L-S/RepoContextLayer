const fs=require("fs");

const nodes=JSON.parse(
  fs.readFileSync("context_data/repo-context.json","utf8")
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