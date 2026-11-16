import {spawnSync} from "node:child_process";
import {resolve,dirname} from "node:path";
import {fileURLToPath} from "node:url";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const python=resolve(root,"backend/.venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");
const result=spawnSync(python,["-m","pytest","-q"],{cwd:resolve(root,"backend"),stdio:"inherit",windowsHide:true});
if(result.error)throw result.error;process.exitCode=result.status||0;
