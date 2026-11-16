import {Suspense} from "react";
import {NotebookScreen} from "@/components/screens/NotebookScreen";
export default function NotebookPage(){return <Suspense fallback={<div className="screen-loader">Loading notebook…</div>}><NotebookScreen/></Suspense>;}
