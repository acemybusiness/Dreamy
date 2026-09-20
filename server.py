from __future__ import annotations

import io, json, os, random, re, time, uuid, zipfile
from pathlib import Path
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont

APP_VERSION="1.2.0"
BASE_DIR=Path(__file__).resolve().parent
OUTPUT_DIR=BASE_DIR/"outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

COMFY_URL=os.getenv("COMFY_URL","http://127.0.0.1:8188").rstrip("/")
OLLAMA_URL=os.getenv("OLLAMA_URL","http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL=os.getenv("OLLAMA_MODEL","llama3:latest")
COMFY_CHECKPOINT=os.getenv("COMFY_CHECKPOINT","").strip()
APP_DEBUG=os.getenv("APP_DEBUG","1")=="1"

app=Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"]=0

STYLE_CORE=(
    "dreamlike surreal fantasy landscape, cinematic luminous atmosphere, deep black negative space, "
    "ethereal aurora ribbons, glowing mist, floating geology, cascading waterfalls, mirrorlike reflective water, "
    "bioluminescent accents, rich indigo violet cyan and warm gold lighting, intricate natural textures, "
    "volumetric rays, elegant vertical composition, high detail, painterly photoreal fantasy, original scene"
)
NEGATIVE_CORE=(
    "text, logo, watermark, signature, letters, copied composition, duplicate objects, low detail, blurry, noisy, "
    "flat lighting, muddy colors, deformed geometry, frame, border, collage seams, jpeg artifacts"
)
DOUBLE_STACK_TEMPLATE=(
    "Create a completely original vertical double-stack fantasy landscape. Two distinct floating islands are arranged "
    "one above the other with clear depth separation. Each island has unique rock silhouettes, vegetation and waterfalls. "
    "The upper island contains a luminous pool and a small flowering tree. The lower island is larger and anchors the "
    "composition above a reflective water basin. Several waterfalls descend through mist and light. Do not copy any known "
    "artwork or reference image. Use an aurora-filled night sky, scattered stars, soft glowing particles, blue-violet "
    "shadows and warm golden reflections."
)
COMPONENT_LIBRARY=[
    ("sky_aurora","isolated fantasy night sky, aurora curtains, stars, glowing clouds, no land, no text"),
    ("upper_island","single isolated upper floating island, unusual rock silhouette, small luminous pool, flowering tree, waterfalls, centered object, simple dark background"),
    ("lower_island","single isolated lower floating island, larger dramatic rock mass, moss, flowers, waterfalls, centered object, simple dark background"),
    ("waterfalls_mist","isolated luminous waterfalls and drifting mist, elegant vertical flow, simple dark background"),
    ("reflection_pool","isolated calm reflective water pool with gold and violet light reflections, no land, simple dark background"),
    ("foreground_accents","isolated fantasy flowers, moss, glowing particles and tiny natural accents, simple dark background"),
]

def slugify(v:str)->str:
    return re.sub(r"[^a-zA-Z0-9_-]+","-",v.strip()).strip("-")[:64] or "dreamy-image"

def comfy_ok()->bool:
    try:
        return requests.get(f"{COMFY_URL}/system_stats",timeout=2).ok
    except Exception:
        return False

def ollama_ok()->bool:
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags",timeout=2).ok
    except Exception:
        return False

def get_checkpoints()->list[str]:
    try:
        r=requests.get(f"{COMFY_URL}/object_info/CheckpointLoaderSimple",timeout=5)
        return r.json()["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0] if r.ok else []
    except Exception:
        return []

def choose_checkpoint(requested:str|None=None)->str:
    if requested:return requested
    if COMFY_CHECKPOINT:return COMFY_CHECKPOINT
    ckpts=get_checkpoints()
    if not ckpts: raise RuntimeError("No ComfyUI checkpoint found. Put a local checkpoint in ComfyUI/models/checkpoints and restart ComfyUI.")
    for c in ckpts:
        if any(k in c.lower() for k in ("xl","sdxl","juggernaut","dream","realvis","lightning")): return c
    return ckpts[0]

def local_plan(description:str)->dict[str,Any]:
    desc=description.strip() or "two floating islands with waterfalls, aurora sky, reflective pool"
    return {
        "master_prompt":f"{DOUBLE_STACK_TEMPLATE} User concept: {desc}. {STYLE_CORE}",
        "components":[{"name":n,"prompt":f"{p}. Concept cues: {desc}. {STYLE_CORE}"} for n,p in COMPONENT_LIBRARY]
    }

def ollama_plan(description:str)->dict[str,Any]:
    fallback=local_plan(description)
    if not ollama_ok(): return fallback
    prompt=f"""You are a local prompt architect for original fantasy image generation.
Return JSON only with keys master_prompt and components.
Rules:
- Completely original scene; do not name artists, copyrighted characters, franchises, logos, or living artists.
- Do not copy a supplied composition; use only high-level visual traits.
- Vertical double-stack scene with two distinct floating islands, waterfalls, aurora sky and reflective basin.
- Components exactly: sky_aurora, upper_island, lower_island, waterfalls_mist, reflection_pool, foreground_accents.
- Preserve deep dark negative space, luminous blue/violet/cyan and warm gold highlights, dreamy volumetric light.
User description: {description}"""
    try:
        r=requests.post(f"{OLLAMA_URL}/api/generate",json={"model":OLLAMA_MODEL,"prompt":prompt,"stream":False,"format":"json"},timeout=120)
        parsed=json.loads(r.json().get("response","{}")) if r.ok else {}
        return parsed if parsed.get("master_prompt") and len(parsed.get("components",[]))>=2 else fallback
    except Exception:
        return fallback

def build_workflow(prompt,negative,width,height,seed,steps,cfg,checkpoint):
    return {
        "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":checkpoint}},
        "2":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["1",1]}},
        "3":{"class_type":"CLIPTextEncode","inputs":{"text":negative,"clip":["1",1]}},
        "4":{"class_type":"EmptyLatentImage","inputs":{"width":width,"height":height,"batch_size":1}},
        "5":{"class_type":"KSampler","inputs":{"seed":int(seed),"steps":int(steps),"cfg":float(cfg),"sampler_name":"dpmpp_2m","scheduler":"karras","denoise":1.0,"model":["1",0],"positive":["2",0],"negative":["3",0],"latent_image":["4",0]}},
        "6":{"class_type":"VAEDecode","inputs":{"samples":["5",0],"vae":["1",2]}},
        "7":{"class_type":"SaveImage","inputs":{"filename_prefix":"DreamySRL","images":["6",0]}},
    }

def generate_comfy(prompt,negative,width,height,seed,steps,cfg,checkpoint)->Image.Image:
    if not comfy_ok(): raise RuntimeError("ComfyUI is not reachable at "+COMFY_URL)
    submit=requests.post(f"{COMFY_URL}/prompt",json={"prompt":build_workflow(prompt,negative,width,height,seed,steps,cfg,checkpoint),"client_id":str(uuid.uuid4())},timeout=20)
    if not submit.ok: raise RuntimeError("ComfyUI rejected the workflow: "+submit.text[:500])
    pid=submit.json()["prompt_id"]
    deadline=time.time()+900
    while time.time()<deadline:
        h=requests.get(f"{COMFY_URL}/history/{pid}",timeout=10)
        entry=h.json().get(pid) if h.ok else None
        if entry and entry.get("outputs"):
            for out in entry["outputs"].values():
                imgs=out.get("images") or []
                if imgs:
                    m=imgs[0]
                    v=requests.get(f"{COMFY_URL}/view",params={"filename":m["filename"],"subfolder":m.get("subfolder",""),"type":m.get("type","output")},timeout=60)
                    if v.ok:return Image.open(io.BytesIO(v.content)).convert("RGB")
        time.sleep(1)
    raise TimeoutError("Timed out waiting for ComfyUI generation.")

def add_srl(img:Image.Image)->Image.Image:
    im=img.convert("RGBA"); layer=Image.new("RGBA",im.size,(0,0,0,0)); draw=ImageDraw.Draw(layer)
    w,h=im.size; fs=max(18,int(min(w,h)*0.035))
    try: font=ImageFont.truetype("DejaVuSerif-BoldItalic.ttf",fs)
    except Exception: font=ImageFont.load_default()
    text="SRL"; b=draw.textbbox((0,0),text,font=font); tw,th=b[2]-b[0],b[3]-b[1]
    x,y=w-tw-int(w*.025),h-th-int(h*.025)
    draw.text((x+2,y+2),text,font=font,fill=(0,0,0,130)); draw.text((x,y),text,font=font,fill=(255,245,225,190))
    return Image.alpha_composite(im,layer).convert("RGB")

def print_size_to_pixels(wi:float,hi:float,dpi:int):
    wi=max(1,min(wi,40)); hi=max(1,min(hi,40)); dpi=max(72,min(dpi,600))
    return round(wi*dpi),round(hi*dpi)

def gpu_base_size(tw:int,th:int,max_side:int=1536):
    ratio=tw/th
    if tw>=th: w=min(max_side,tw); h=round(w/ratio)
    else: h=min(max_side,th); w=round(h*ratio)
    return max(512,round(w/64)*64),max(512,round(h/64)*64)

def try_remove_background(img:Image.Image)->Image.Image:
    try:
        from rembg import remove
        return remove(img.convert("RGBA"))
    except Exception:
        return img.convert("RGBA")

def export_variants(img:Image.Image,stem:str,out:Path):
    paths={"png":out/f"{stem}.png","jpg":out/f"{stem}.jpg","webp":out/f"{stem}.webp","pdf":out/f"{stem}.pdf"}
    img.save(paths["png"],"PNG")
    img.save(paths["jpg"],"JPEG",quality=96,subsampling=0)
    img.save(paths["webp"],"WEBP",quality=96,method=6)
    img.convert("RGB").save(paths["pdf"],"PDF",resolution=300.0)
    return {k:p.name for k,p in paths.items()}

@app.get("/")
def index(): return render_template("index.html",version=APP_VERSION)

@app.get("/api/ping")
def ping(): return jsonify({"ok":True,"version":APP_VERSION})

@app.get("/api/status")
def status():
    return jsonify({"version":APP_VERSION,"comfy":comfy_ok(),"ollama":ollama_ok(),"ollama_model":OLLAMA_MODEL,"comfy_url":COMFY_URL,"checkpoints":get_checkpoints() if comfy_ok() else []})

@app.post("/api/generate")
def generate():
    p=request.get_json(force=True)
    desc=(p.get("description") or "").strip()
    wi=max(1,min(float(p.get("width_in",8)),40)); hi=max(1,min(float(p.get("height_in",12)),40)); dpi=max(72,min(int(p.get("dpi",300)),600))
    tw,th=print_size_to_pixels(wi,hi,dpi); width,height=gpu_base_size(tw,th)
    steps=max(12,min(int(p.get("steps",28)),60)); cfg=max(1,min(float(p.get("cfg",6.5)),15))
    seed=int(p.get("seed") or random.randint(1,2**31-1)); checkpoint=choose_checkpoint(p.get("checkpoint"))
    plan=ollama_plan(desc); run_id=f"{time.strftime('%Y%m%d-%H%M%S')}-{seed}"; out=OUTPUT_DIR/run_id; out.mkdir(parents=True,exist_ok=True)
    master=add_srl(generate_comfy(plan["master_prompt"],NEGATIVE_CORE,width,height,seed,steps,cfg,checkpoint))
    if master.size!=(tw,th): master=master.resize((tw,th),Image.Resampling.LANCZOS)
    files=export_variants(master,"Dreamy_DoubleStack_SRL",out)
    component_files=[]
    if bool(p.get("components",True)):
        for i,c in enumerate(plan.get("components",[])[:6]):
            ci=generate_comfy(c["prompt"]+". isolated asset, centered, generous empty space around subject",NEGATIVE_CORE,768,768,seed+i+101,max(18,steps-4),cfg,checkpoint)
            if bool(p.get("transparency",True)): ci=try_remove_background(ci)
            ci=add_srl(ci.convert("RGB")).convert("RGBA")
            name=slugify(c.get("name",f"component-{i+1}"))+".png"; ci.save(out/name,"PNG"); component_files.append(name)
    manifest={"app":"Dreamy DoubleStack SRL","app_version":APP_VERSION,"seed":seed,"checkpoint":checkpoint,"print_size_inches":[wi,hi],"dpi":dpi,"export_size_px":[tw,th],"master_prompt":plan["master_prompt"],"negative_prompt":NEGATIVE_CORE,"description":desc,"components":plan.get("components",[])}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    zp=out/"Dreamy_DoubleStack_SRL_package.zip"
    with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED) as z:
        for f in out.iterdir():
            if f.name!=zp.name:z.write(f,arcname=f.name)
    return jsonify({"ok":True,"run_id":run_id,"seed":seed,"checkpoint":checkpoint,"files":{k:f"/outputs/{run_id}/{v}" for k,v in files.items()},"components":[f"/outputs/{run_id}/{v}" for v in component_files],"manifest":f"/outputs/{run_id}/manifest.json","package":f"/outputs/{run_id}/{zp.name}"})

@app.get("/outputs/<run_id>/<path:filename>")
def output_file(run_id,filename): return send_from_directory(OUTPUT_DIR/slugify(run_id),filename,as_attachment=False)

@app.errorhandler(Exception)
def on_error(exc): return jsonify({"ok":False,"error":str(exc)}),500

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","5055")),debug=APP_DEBUG,use_reloader=APP_DEBUG)
