"use client";
import {Camera, ImagePlus, X} from "lucide-react";
import {useEffect, useRef, useState} from "react";

async function resizePhoto(file: File): Promise<string> {
  if (!/image\/(jpeg|png|webp)/.test(file.type)) throw new Error("Choose a JPEG, PNG or WebP photo.");
  const url = URL.createObjectURL(file);
  try {
    const image = new Image();
    image.src = url;
    await image.decode();
    const canvas = document.createElement("canvas");
    let scale = Math.min(1, 1400 / Math.max(image.width, image.height));
    for (let attempt = 0; attempt < 5; attempt++) {
      canvas.width = Math.max(1, Math.round(image.width * scale));
      canvas.height = Math.max(1, Math.round(image.height * scale));
      const context = canvas.getContext("2d");
      if (!context) throw new Error("This browser cannot prepare the photo.");
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const data = canvas.toDataURL("image/jpeg", .8 - attempt * .07);
      if (data.length < 1_000_000) return data;
      scale *= .75;
    }
    throw new Error("This photo is too large. Try a smaller image.");
  } finally { URL.revokeObjectURL(url); }
}

export function PhotoPicker({photo,onChange,disabled=false}:{photo:string|null;onChange:(photo:string|null)=>void;disabled?:boolean}) {
  const upload = useRef<HTMLInputElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream|null>(null);
  const [cameraOpen,setCameraOpen] = useState(false);
  const [error,setError] = useState("");
  function closeCamera() {stream.current?.getTracks().forEach(track=>track.stop());stream.current=null;setCameraOpen(false);}
  useEffect(()=>{if(cameraOpen&&video.current&&stream.current)video.current.srcObject=stream.current;},[cameraOpen]);
  useEffect(()=>()=>{stream.current?.getTracks().forEach(track=>track.stop());},[]);
  async function openCamera() {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia) {setError("This browser cannot open a camera. Use Upload a photo instead.");return;}
    try {stream.current=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:"environment"}}});setCameraOpen(true);}
    catch {setError("Camera access was denied or no camera is available. Check browser permissions or upload a photo.");}
  }
  async function takeSnap() {
    const element=video.current;
    if (!element?.videoWidth) {setError("Camera is still starting. Try again in a moment.");return;}
    const canvas=document.createElement("canvas");canvas.width=element.videoWidth;canvas.height=element.videoHeight;
    canvas.getContext("2d")?.drawImage(element,0,0);
    try {
      const blob=await new Promise<Blob>((resolve,reject)=>canvas.toBlob(value=>value?resolve(value):reject(new Error("Could not capture the photo.")),"image/jpeg",.9));
      onChange(await resizePhoto(new File([blob],"snap.jpg",{type:"image/jpeg"})));
      closeCamera();
    } catch(cause) {setError(cause instanceof Error?cause.message:"Could not capture the photo.");}
  }
  async function select(file?: File) {
    if (!file) return;
    setError("");
    try { onChange(await resizePhoto(file)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not read the photo."); }
  }
  return <div className="photo-picker"><input ref={upload} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={event=>{void select(event.target.files?.[0]);event.target.value="";}}/><div className="photo-picker-actions"><button type="button" className="secondary-button" disabled={disabled||cameraOpen} onClick={()=>void openCamera()}><Camera size={16}/>Take a snap</button><button type="button" className="secondary-button" disabled={disabled||cameraOpen} onClick={()=>upload.current?.click()}><ImagePlus size={16}/>Upload a photo</button></div>{cameraOpen&&<div className="camera-preview"><video ref={video} autoPlay playsInline muted aria-label="Live camera preview"/><div><button type="button" className="primary-button" onClick={()=>void takeSnap()} disabled={disabled}>Capture photo</button><button type="button" className="secondary-button" onClick={closeCamera}>Cancel</button></div></div>}{photo&&<div className="photo-preview"><img src={photo} alt="Attached photo preview"/><button type="button" className="icon-button" aria-label="Remove photo" disabled={disabled} onClick={()=>onChange(null)}><X size={16}/></button></div>}{error&&<p role="alert" className="form-error">{error}</p>}</div>;
}
