import {Suspense} from "react";
import {ProfileScreen} from "@/components/screens/ProfileScreen";
export default function ProfilePage(){return <Suspense fallback={<div className="screen-loader">Loading settings…</div>}><ProfileScreen/></Suspense>;}
