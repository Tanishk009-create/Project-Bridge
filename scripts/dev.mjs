import {existsSync} from "node:fs";
import {resolve,dirname} from "node:path";
import {fileURLToPath} from "node:url";
import {spawn} from "node:child_process";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const python=resolve(root,"backend/.venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");
if(!existsSync(python))throw new Error("Run npm run setup first.");
const port=Number(process.env.WEB_PORT||3000),apiPort=Number(process.env.API_PORT||8000);
for(const value of [port,apiPort])if(!Number.isInteger(value)||value<1||value>65535)throw new Error("Invalid port");
const children=[];let stopping=false;
function stop(code=0){if(stopping)return;stopping=true;for(const child of children)child.kill();process.exitCode=code;}
function launch(command,args,cwd,env){const child=spawn(command,args,{cwd,env:{...process.env,...env},stdio:"inherit",windowsHide:true});children.push(child);child.on("error",e=>{console.error(e.message);stop(1);});child.on("exit",code=>{if(!stopping)stop(code||0);});return child;}
process.on("SIGINT",()=>stop());process.on("SIGTERM",()=>stop());
const backend=launch(python,["-m","uvicorn","app.main:app","--host","127.0.0.1","--port",String(apiPort)],resolve(root,"backend"),{ALLOWED_ORIGINS:JSON.stringify([`http://localhost:${port}`,`http://127.0.0.1:${port}`]),PUBLIC_URL:`http://localhost:${port}`});
let ready=false;
for(let attempt=0;attempt<40&&!stopping;attempt++){try{ready=(await fetch(`http://127.0.0.1:${apiPort}/api/v1/health/db`,{signal:AbortSignal.timeout(1000)})).ok;if(ready)break;}catch{}await new Promise(r=>setTimeout(r,500));}
if(!ready){console.error("Backend could not start. Check the errors above and database settings.");stop(1);}
else if(!stopping){launch(process.execPath,[resolve(root,"frontend/node_modules/next/dist/bin/next"),"dev","--webpack","-p",String(port)],resolve(root,"frontend"),{BACKEND_URL:`http://127.0.0.1:${apiPort}`,NEXTAUTH_URL:`http://localhost:${port}`,NEXT_DIST_DIR:".next-dev"});console.log(`Bridge: http://localhost:${port} | API docs: http://127.0.0.1:${apiPort}/docs`);}
