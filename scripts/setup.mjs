import {existsSync,mkdirSync,readFileSync,writeFileSync} from "node:fs";
import {resolve,dirname} from "node:path";
import {fileURLToPath} from "node:url";
import {spawnSync} from "node:child_process";
import {randomBytes} from "node:crypto";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const tmp=resolve(root,".tmp");mkdirSync(tmp,{recursive:true});
const env={...process.env,TEMP:tmp,TMP:tmp};
function run(command,args,cwd=root){const result=spawnSync(command,args,{cwd,env,stdio:"inherit",windowsHide:true});if(result.error)throw result.error;if(result.status!==0)process.exit(result.status||1);}
const candidates=process.env.BRIDGE_PYTHON?[[process.env.BRIDGE_PYTHON,[]]]:process.platform==="win32"?[["py",["-3"]],["python",[]]]:[["python3",[]],["python",[]]];
const selected=candidates.find(([command,args])=>spawnSync(command,[...args,"-c","import sys; assert sys.version_info >= (3,11)"],{env,stdio:"ignore",windowsHide:true}).status===0);
if(!selected)throw new Error("Python 3.11+ is required. Install Python, or set BRIDGE_PYTHON to its executable path.");
const python=resolve(root,"backend/.venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");
if(!existsSync(python))run(selected[0],[...selected[1],"-m","venv",resolve(root,"backend/.venv")]);
const secret=()=>randomBytes(48).toString("base64url");const jwt=secret(),auth=secret();
function createEnv(target,template,replacements){if(existsSync(resolve(root,target)))return;let value=readFileSync(resolve(root,template),"utf8");for(const [key,replacement]of Object.entries(replacements))value=value.replace(new RegExp(`^${key}=.*$`,"m"),`${key}=${replacement}`);writeFileSync(resolve(root,target),value);}
createEnv("backend/.env","backend/.env.example",{JWT_SECRET_KEY:jwt});
createEnv("frontend/.env.local","frontend/.env.example",{NEXTAUTH_SECRET:auth});
createEnv(".env",".env.example",{DB_PASSWORD:secret(),JWT_SECRET_KEY:jwt,NEXTAUTH_SECRET:auth});
run(python,["-m","pip","install","-r","requirements-dev.txt"],resolve(root,"backend"));
if(!process.env.npm_execpath)throw new Error("Run this script using npm run setup.");
run(process.execPath,[process.env.npm_execpath,"ci","--no-audit","--no-fund"],resolve(root,"frontend"));
if(/^DB_DRIVER=sqlite\+aiosqlite\s*$/m.test(readFileSync(resolve(root,"backend/.env"),"utf8")))run(python,["-m","app.bootstrap"],resolve(root,"backend"));
else console.log("PostgreSQL selected: run alembic upgrade head in backend before starting.");
console.log("Setup complete. Run npm run dev, then open http://localhost:3000.");
