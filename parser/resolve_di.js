const fs=require("fs");

const nodes=JSON.parse(
  fs.readFileSync("context_data/repo-context.json","utf8")
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
  "context_data/di-map.json",
  JSON.stringify(di,null,2)
);

console.log("di-map.json generated");