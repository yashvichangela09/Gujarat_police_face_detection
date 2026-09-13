"""
dashboard.py  -  AI Vehicle Intelligence Dashboard
Multi-camera cross-camera re-identification.
No live feed. Pure data dashboard.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os, json, re, threading, queue, time

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from backend import get_dashboard_data

try:
    from multi_camera_manager import MultiCameraManager
    import cross_camera_reid as reid
    LIVE_AVAILABLE = True
except Exception as _e:
    LIVE_AVAILABLE = False
    print(f"[dashboard] multi_camera unavailable: {_e}")

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR       = os.path.join(BASE_DIR, "output")
VEHICLE_CROP_DIR = os.path.join(BASE_DIR, "output", "vehicle_crops")

BG=     "#0b1120"; SIDEBAR="#111827"; CARD="#151f32"; CARD2="#1b263b"
BORDER= "#26354d"; TEXT="#f8fafc";    MUTED="#94a3b8"
CYAN=   "#22d3ee"; GREEN="#34d399";   YELLOW="#fbbf24"; RED="#fb7185"
PURPLE= "#a78bfa"; BLUE="#60a5fa";    ORANGE="#fb923c"

def load_json(path, default=None):
    if default is None: default = []
    try:
        if not os.path.exists(path): return default
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    except: return default

def safe_float(v, d=0.0):
    try: return float(v)
    except: return d

def fv(data, keys, default="--"):
    if not isinstance(data, dict): return default
    for k in keys:
        val=data.get(k)
        if val is not None and val!="": return val
    return default

def find_vehicle_image(vehicle_id, vehicle_data=None):
    vid=str(vehicle_id); exts=[".jpg",".jpeg",".png",".bmp"]
    if isinstance(vehicle_data,dict):
        for key in ("crop_path","image_path","vehicle_image","crop"):
            v=vehicle_data.get(key)
            if not v: continue
            v=str(v)
            if os.path.isabs(v) and os.path.exists(v): return v
            for base in (BASE_DIR,OUTPUT_DIR):
                p=os.path.join(base,v)
                if os.path.exists(p): return p
    for ext in exts:
        p=os.path.join(VEHICLE_CROP_DIR,vid+ext)
        if os.path.exists(p): return p
    if os.path.exists(VEHICLE_CROP_DIR):
        for fname in os.listdir(VEHICLE_CROP_DIR):
            if vid.lower() in fname.lower():
                fp=os.path.join(VEHICLE_CROP_DIR,fname)
                if os.path.isfile(fp) and fname.lower().endswith(tuple(exts)): return fp
    m=re.search(r"(\d+)$",vid)
    if m:
        n=int(m.group(1))
        for ext in exts:
            p=os.path.join(VEHICLE_CROP_DIR,f"vehicle_{n}{ext}")
            if os.path.exists(p): return p
    return None


class VehicleDashboard:
    def __init__(self, root):
        self.root=root
        self.root.title("AI Vehicle Intelligence Dashboard")
        self.root.geometry("1600x900"); self.root.minsize(1200,720)
        self.root.configure(bg=BG)

        self.vehicles={}; self.filtered_ids=[]
        self.selected_vehicle=None; self.current_photo=None
        self._events_log=[]
        self._frame_counts={}   # camera_id -> frame count

        # multi-camera manager
        self.manager = MultiCameraManager() if LIVE_AVAILABLE else None

        self._setup_style()
        self._build_ui()
        self.refresh_data()
        self._poll()

    def _setup_style(self):
        s=ttk.Style()
        try: s.theme_use("clam")
        except: pass
        s.configure("Treeview",background=CARD,foreground=TEXT,
            fieldbackground=CARD,rowheight=34,borderwidth=0,font=("Segoe UI",10))
        s.configure("Treeview.Heading",background=CARD2,foreground=CYAN,
            font=("Segoe UI",10,"bold"),borderwidth=0)
        s.map("Treeview",
            background=[("selected","#164e63")],
            foreground=[("selected","#ffffff")])

    def _build_ui(self):
        self._sidebar(); self._main_area()

    def _sidebar(self):
        sb=tk.Frame(self.root,bg=SIDEBAR,width=230)
        sb.pack(side="left",fill="y"); sb.pack_propagate(False)

        tk.Label(sb,text="AI VEHICLE",bg=SIDEBAR,fg=CYAN,
            font=("Segoe UI",16,"bold")).pack(pady=(26,2))
        tk.Label(sb,text="INTELLIGENCE SYSTEM",bg=SIDEBAR,fg=MUTED,
            font=("Segoe UI",7,"bold")).pack(pady=(0,4))
        self.sys_lbl=tk.Label(sb,text="SYSTEM ONLINE",bg=SIDEBAR,fg=GREEN,
            font=("Segoe UI",8,"bold"))
        self.sys_lbl.pack(pady=(0,16))

        tk.Frame(sb,bg=BORDER,height=1).pack(fill="x",padx=18,pady=(0,6))
        self._sbtn(sb,"Dashboard",          self._show_all)
        self._sbtn(sb,"Vehicle Search",     self._focus_search)

        tk.Frame(sb,bg=BORDER,height=1).pack(fill="x",padx=18,pady=8)
        tk.Label(sb,text="CAMERA MANAGEMENT",bg=SIDEBAR,fg=MUTED,
            font=("Segoe UI",7,"bold")).pack(anchor="w",padx=22,pady=(0,4))
        self._sbtn(sb,"Add Camera",         self._add_camera,    fg=GREEN)
        self._sbtn(sb,"Load 20-30 Cameras", self._load_camera_config, fg=GREEN)
        self._sbtn(sb,"Multi-Cam Summary",  self._multi_cam_summary, fg=PURPLE)
        self._sbtn(sb,"Stop All Cameras",   self._stop_all,      fg=RED)
        self._sbtn(sb,"Camera Status",      self._cam_status,    fg=CYAN)

        tk.Frame(sb,bg=BORDER,height=1).pack(fill="x",padx=18,pady=8)
        tk.Label(sb,text="TOOLS",bg=SIDEBAR,fg=MUTED,
            font=("Segoe UI",7,"bold")).pack(anchor="w",padx=22,pady=(0,4))
        self._sbtn(sb,"Tracking Data",      self._show_tracking)
        self._sbtn(sb,"Database",           self._show_database)
        self._sbtn(sb,"Refresh Data",       self.refresh_data,   fg=CYAN)

        tk.Frame(sb,bg=SIDEBAR).pack(expand=True)
        tk.Label(sb,text="AI Vehicle Recognition v1.0",bg=SIDEBAR,fg=MUTED,
            font=("Segoe UI",7)).pack(pady=(0,16))

    def _sbtn(self,parent,text,cmd,fg=None):
        tk.Button(parent,text=text,command=cmd,bg=SIDEBAR,fg=fg or MUTED,
            activebackground=CARD2,activeforeground=CYAN,
            relief="flat",bd=0,anchor="w",padx=22,pady=10,
            font=("Segoe UI",10,"bold"),cursor="hand2").pack(fill="x",padx=10,pady=2)

    def _main_area(self):
        self.main=tk.Frame(self.root,bg=BG)
        self.main.pack(side="left",fill="both",expand=True)
        self._header(); self._kpi_row(); self._content(); self._statusbar()

    def _header(self):
        h=tk.Frame(self.main,bg=BG)
        h.pack(fill="x",padx=26,pady=(20,6))
        tf=tk.Frame(h,bg=BG); tf.pack(side="left")
        tk.Label(tf,text="VEHICLE INTELLIGENCE",bg=BG,fg=TEXT,
            font=("Segoe UI",24,"bold")).pack(anchor="w")
        tk.Label(tf,text="Multi-camera detection  |  cross-camera tracking  |  plate recognition",
            bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",pady=(2,0))
        tk.Button(h,text="Refresh",command=self.refresh_data,
            bg=CARD2,fg=CYAN,activebackground="#22334d",activeforeground=CYAN,
            relief="flat",bd=0,padx=14,pady=8,
            font=("Segoe UI",9,"bold"),cursor="hand2").pack(side="right")

    def _kpi_row(self):
        row=tk.Frame(self.main,bg=BG)
        row.pack(fill="x",padx=26,pady=(0,10))
        self.kpi={}
        for name,val,accent,desc in [
            ("VEHICLES",      "0",    CYAN,   "unique vehicles"),
            ("PLATES",        "0",    PURPLE, "plates recognised"),
            ("CAMERAS",       "0",    GREEN,  "active cameras"),
            ("DETECTIONS",    "0",    YELLOW, "total observations"),
            ("VEHICLE TYPES", "0",    BLUE,   "classes"),
            ("STATUS",        "IDLE", ORANGE, "system mode"),
        ]:
            c=tk.Frame(row,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
            c.pack(side="left",fill="x",expand=True,padx=4)
            tk.Label(c,text=name,bg=CARD,fg=MUTED,
                font=("Segoe UI",8,"bold")).pack(anchor="w",padx=12,pady=(10,1))
            lbl=tk.Label(c,text=val,bg=CARD,fg=accent,font=("Segoe UI",20,"bold"))
            lbl.pack(anchor="w",padx=12)
            tk.Label(c,text=desc,bg=CARD,fg=MUTED,
                font=("Segoe UI",7)).pack(anchor="w",padx=12,pady=(0,10))
            self.kpi[name]=lbl

    def _content(self):
        body=tk.Frame(self.main,bg=BG)
        body.pack(fill="both",expand=True,padx=26,pady=(0,8))

        left=tk.Frame(body,bg=BG,width=270)
        left.pack(side="left",fill="y",padx=(0,10)); left.pack_propagate(False)
        self._events_panel(left)

        mid=tk.Frame(body,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
        mid.pack(side="left",fill="both",expand=True)
        self._table_panel(mid)

        right=tk.Frame(body,bg=CARD,width=330,
            highlightbackground=BORDER,highlightthickness=1)
        right.pack(side="right",fill="y",padx=(10,0)); right.pack_propagate(False)
        self._profile_panel(right)

    def _statusbar(self):
        self.status_bar=tk.Label(self.main,text="Initialising...",
            bg="#080d18",fg=MUTED,anchor="w",padx=14,pady=6,
            font=("Segoe UI",8))
        self.status_bar.pack(fill="x",side="bottom")

    # ── events panel ──────────────────────────────────────────────────────────

    def _events_panel(self,parent):
        # scan status
        sc=tk.Frame(parent,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
        sc.pack(fill="x",pady=(0,8))
        tk.Label(sc,text="SCAN STATUS",bg=CARD,fg=MUTED,
            font=("Segoe UI",8,"bold")).pack(anchor="w",padx=12,pady=(10,2))
        self.scan_lbl=tk.Label(sc,text="IDLE",bg=CARD,fg=MUTED,
            font=("Segoe UI",14,"bold"))
        self.scan_lbl.pack(anchor="w",padx=12)
        self.cam_count_lbl=tk.Label(sc,text="0 cameras active",bg=CARD,fg=MUTED,
            font=("Segoe UI",8))
        self.cam_count_lbl.pack(anchor="w",padx=12,pady=(0,8))

        # frames counter
        fc=tk.Frame(parent,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
        fc.pack(fill="x",pady=(0,8))
        tk.Label(fc,text="TOTAL FRAMES SCANNED",bg=CARD,fg=MUTED,
            font=("Segoe UI",8,"bold")).pack(anchor="w",padx=12,pady=(10,2))
        self.frames_lbl=tk.Label(fc,text="0",bg=CARD,fg=CYAN,
            font=("Segoe UI",20,"bold"))
        self.frames_lbl.pack(anchor="w",padx=12,pady=(0,10))
        self._total_frames=0

        # events log
        ec=tk.Frame(parent,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
        ec.pack(fill="both",expand=True)
        hdr=tk.Frame(ec,bg=CARD); hdr.pack(fill="x",padx=12,pady=(10,4))
        tk.Label(hdr,text="DETECTION EVENTS",bg=CARD,fg=YELLOW,
            font=("Segoe UI",9,"bold")).pack(side="left")
        tk.Button(hdr,text="clear",command=self._clear_events,
            bg=CARD,fg=MUTED,relief="flat",bd=0,
            font=("Segoe UI",8),cursor="hand2").pack(side="right")
        self.events_box=tk.Text(ec,bg="#080d18",fg=GREEN,
            relief="flat",font=("Consolas",8),state="disabled",wrap="word")
        self.events_box.pack(fill="both",expand=True,padx=12,pady=(0,10))

    def _log(self,msg):
        ts=time.strftime("%H:%M:%S"); line=f"[{ts}]  {msg}\n"
        self._events_log.append(line)
        if len(self._events_log)>400: self._events_log=self._events_log[-400:]
        self.events_box.configure(state="normal")
        self.events_box.insert("end",line); self.events_box.see("end")
        self.events_box.configure(state="disabled")

    def _clear_events(self):
        self._events_log=[]
        self.events_box.configure(state="normal"); self.events_box.delete("1.0","end")
        self.events_box.configure(state="disabled")

    # ── table panel ───────────────────────────────────────────────────────────

    def _table_panel(self,parent):
        sf=tk.Frame(parent,bg=CARD); sf.pack(fill="x",padx=14,pady=12)
        tk.Label(sf,text="DETECTED VEHICLES",bg=CARD,fg=TEXT,
            font=("Segoe UI",11,"bold")).pack(side="left")
        tk.Label(sf,text="Search:",bg=CARD,fg=MUTED,
            font=("Segoe UI",9)).pack(side="right",padx=(0,4))
        self.search_var=tk.StringVar()
        e=tk.Entry(sf,textvariable=self.search_var,bg=BG,fg=TEXT,
            insertbackground=CYAN,relief="flat",font=("Segoe UI",9),width=20)
        e.pack(side="right",ipady=7); e.bind("<KeyRelease>",lambda _:self._search())

        tf=tk.Frame(parent,bg=CARD)
        tf.pack(fill="both",expand=True,padx=14,pady=(0,14))

        cols=("id","type","color","plate","plate_pct","det_pct","cameras","frames")
        heads={"id":"VEHICLE ID","type":"TYPE","color":"COLOR",
               "plate":"NUMBER PLATE","plate_pct":"PLATE %",
               "det_pct":"DET %","cameras":"CAMERAS SEEN","frames":"FRAMES"}
        widths={"id":105,"type":80,"color":75,"plate":120,
                "plate_pct":65,"det_pct":65,"cameras":110,"frames":65}

        self.tree=ttk.Treeview(tf,columns=cols,show="headings")
        for c in cols:
            self.tree.heading(c,text=heads[c])
            self.tree.column(c,width=widths[c],anchor="center")
        vsb=ttk.Scrollbar(tf,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left",fill="both",expand=True); vsb.pack(side="right",fill="y")
        self.tree.bind("<<TreeviewSelect>>",self._on_select)

    # ── profile panel ─────────────────────────────────────────────────────────

    def _profile_panel(self,parent):
        tk.Label(parent,text="VEHICLE PROFILE",bg=CARD,fg=TEXT,
            font=("Segoe UI",11,"bold")).pack(anchor="w",padx=16,pady=(16,2))
        self.det_id_lbl=tk.Label(parent,text="Select a vehicle",
            bg=CARD,fg=CYAN,font=("Segoe UI",17,"bold"))
        self.det_id_lbl.pack(anchor="w",padx=16,pady=(0,10))
        self.img_lbl=tk.Label(parent,
            text="VEHICLE IMAGE\n\nSelect a vehicle",
            bg="#080d18",fg=MUTED,font=("Segoe UI",9),width=32,height=9)
        self.img_lbl.pack(padx=16,fill="x")
        df=tk.Frame(parent,bg=CARD)
        df.pack(fill="both",expand=True,padx=16,pady=10)
        self.det_vals={}
        for label,key in [
            ("Vehicle Type",    "vehicle_type"),
            ("Color",           "color"),
            ("Number Plate",    "number_plate"),
            ("Plate Conf",      "plate_confidence"),
            ("Detection Conf",  "confidence"),
            ("Tracking ID",     "tracking_id"),
            ("Cameras Seen",    "cameras_seen"),
            ("Frames Tracked",  "frames_tracked"),
            ("First Frame",     "first_frame"),
            ("Last Frame",      "last_frame"),
            ("Bounding Box",    "bounding_box"),
        ]:
            row=tk.Frame(df,bg=CARD); row.pack(fill="x",pady=2)
            tk.Label(row,text=label,bg=CARD,fg=MUTED,
                font=("Segoe UI",8)).pack(side="left")
            v=tk.Label(row,text="--",bg=CARD,fg=TEXT,font=("Segoe UI",8,"bold"))
            v.pack(side="right"); self.det_vals[key]=v

    # ── refresh ───────────────────────────────────────────────────────────────

    def refresh_data(self):
        try:
            # try live registry first
            if LIVE_AVAILABLE and self.manager:
                live = self.manager.get_all_vehicles()
                if live:
                    self.vehicles={}
                    for v in live:
                        vid=v["vehicle_id"]
                        route = reid.get_vehicle_route(vid)
                        self.vehicles[vid]={
                            "vehicle_id":  vid,
                            "tracking_id": vid,
                            "vehicle_type":v.get("vehicle_type","Unknown"),
                            "color":       v.get("color","Unknown"),
                            "number_plate":v.get("number_plate","UNKNOWN"),
                            "plate_confidence": v.get("plate_conf",0),
                            "detection_confidence": 0,
                            "cameras_seen": ", ".join(v.get("cameras_seen",[])),
                            "frames_tracked": v.get("frames_seen",0),
                            "crop_path":   v.get("crop_path",""),
                            "route":       route,
                        }
                    self._populate(); self._update_kpis(); return

            # fallback: load from JSON files
            data=get_dashboard_data(); self.vehicles={}
            for v in data.get("vehicles",[]):
                if isinstance(v,dict) and v.get("vehicle_id"):
                    self.vehicles[str(v["vehicle_id"])]=v

            tr=load_json(os.path.join(OUTPUT_DIR,"tracking_records.json"),[])
            by_id={}
            for r in tr:
                vid=r.get("vehicle_id")
                if vid: by_id.setdefault(vid,[]).append(r)
            for vid,recs in by_id.items():
                if vid in self.vehicles:
                    self.vehicles[vid]["frames_tracked"]=len(recs)
                    self.vehicles[vid]["first_frame"]=recs[0].get("frame","--")
                    self.vehicles[vid]["last_frame"]=recs[-1].get("frame","--")
                    self.vehicles[vid]["bounding_box"]=recs[-1].get("bounding_box","--")

            self._populate(); self._update_kpis()
            db=data.get("database",{})
            dbt="ONLINE" if db.get("connected") else "OFFLINE"
            self._setstatus(
                f"SYSTEM ONLINE  |  {len(self.vehicles)} vehicles  |  DB {dbt}  |  {time.strftime('%H:%M:%S')}",GREEN)
        except Exception as e:
            self._setstatus(f"ERROR: {e}",RED)

    def _update_kpis(self):
        total=len(self.vehicles)
        plates=sum(1 for v in self.vehicles.values()
            if str(fv(v,["number_plate","plate"],"UNKNOWN")).upper()
               not in ("UNKNOWN","NOT DETECTED","NONE",""))
        types={str(fv(v,["vehicle_type","type"],"")) for v in self.vehicles.values()}-{""}
        tr=load_json(os.path.join(OUTPUT_DIR,"tracking_records.json"),[])
        obs=len(tr)
        active_cams=self.manager.active_count() if self.manager else 0

        self.kpi["VEHICLES"].config(text=str(total))
        self.kpi["PLATES"].config(text=str(plates))
        self.kpi["CAMERAS"].config(text=str(active_cams))
        self.kpi["DETECTIONS"].config(text=str(obs))
        self.kpi["VEHICLE TYPES"].config(text=str(len(types)))
        self.cam_count_lbl.config(
            text=f"{active_cams} camera{'s' if active_cams!=1 else ''} active",
            fg=GREEN if active_cams>0 else MUTED)

    def _set_mode(self,label,color):
        self.kpi["STATUS"].config(text=label,fg=color)
        self.sys_lbl.config(text=label,fg=color)
        self.scan_lbl.config(text=label,fg=color)

    # ── table ─────────────────────────────────────────────────────────────────

    def _populate(self,ids=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        if ids is None: ids=sorted(self.vehicles.keys())
        self.filtered_ids=ids
        for vid in ids:
            v=self.vehicles[vid]
            vt=fv(v,["vehicle_type","type"],"Unknown")
            co=fv(v,["color","vehicle_color"],"Unknown")
            pl=fv(v,["number_plate","plate"],"UNKNOWN")
            pc=safe_float(fv(v,["plate_confidence","plate_conf"],0))
            dc=safe_float(fv(v,["detection_confidence","confidence"],0))
            cams=v.get("cameras_seen","--")
            if isinstance(cams,list): cams=", ".join(cams)
            fr=v.get("frames_tracked",0)
            self.tree.insert("","end",iid=vid,
                values=(vid,vt,co,pl,f"{pc:.1f}%",f"{dc:.1f}%",cams,fr))

    def _search(self):
        q=self.search_var.get().strip().lower()
        if not q: self._populate(); return
        res=[vid for vid,v in self.vehicles.items()
             if q in " ".join([str(vid),
                 str(fv(v,["vehicle_type","type"],"")),
                 str(fv(v,["color","vehicle_color"],"")),
                 str(fv(v,["number_plate","plate"],""))]).lower()]
        self._populate(res)

    # ── profile ───────────────────────────────────────────────────────────────

    def _on_select(self,_=None):
        sel=self.tree.selection()
        if not sel: return
        vid=sel[0]; self.selected_vehicle=vid
        self._show_profile(vid,self.vehicles.get(vid,{}))

    def _show_profile(self,vid,data):
        self.det_id_lbl.config(text=vid)
        self._dv("vehicle_type",   fv(data,["vehicle_type","type"],"Unknown"))
        self._dv("color",          fv(data,["color","vehicle_color"],"Unknown"))
        self._dv("number_plate",   fv(data,["number_plate","plate"],"UNKNOWN"))
        pc=safe_float(fv(data,["plate_confidence","plate_conf"],0))
        dc=safe_float(fv(data,["detection_confidence","confidence"],0))
        self._dv("plate_confidence",f"{pc:.2f}%")
        self._dv("confidence",      f"{dc:.2f}%")
        self._dv("tracking_id",    fv(data,["tracking_id"],vid))
        cams=data.get("cameras_seen","--")
        if isinstance(cams,list): cams=", ".join(cams)
        self._dv("cameras_seen",   cams)
        self._dv("frames_tracked", data.get("frames_tracked","--"))
        self._dv("first_frame",    data.get("first_frame","--"))
        self._dv("last_frame",     data.get("last_frame","--"))
        bb=data.get("bounding_box","--")
        if isinstance(bb,dict):
            bb=f"({bb.get('x1',0)},{bb.get('y1',0)}) -> ({bb.get('x2',0)},{bb.get('y2',0)})"
        self._dv("bounding_box",str(bb))
        # journey / route display (overrides bounding-box label when present)
        route=data.get("route") or data.get("camera_route")
        if route:
            if isinstance(route,list):
                route=" → ".join(str(r) for r in route)
            self._dv("bounding_box", f"ROUTE: {route}")
        self._load_img(vid,data)

    def _dv(self,key,val):
        if key in self.det_vals: self.det_vals[key].config(text=str(val))

    def _load_img(self,vid,data=None):
        self.current_photo=None
        if not PIL_AVAILABLE:
            self.img_lbl.config(image="",text="pip install pillow",
                bg="#080d18",fg=MUTED); return
        path=find_vehicle_image(vid,data)
        if not path:
            self.img_lbl.config(image="",text=f"NO IMAGE\n{vid}",
                bg="#080d18",fg=MUTED,width=32,height=9); return
        try:
            img=Image.open(path); img.thumbnail((310,175))
            photo=ImageTk.PhotoImage(img); self.current_photo=photo
            self.img_lbl.config(image=photo,text="",bg="#080d18",width=310,height=175)
            self.img_lbl.image=photo
        except Exception as e:
            self.img_lbl.config(image="",text=f"IMG ERROR\n{e}",bg="#080d18",fg=RED)

    # ── camera controls ───────────────────────────────────────────────────────

    def _add_camera(self):
        if not LIVE_AVAILABLE:
            messagebox.showwarning("Unavailable","multi_camera_manager not loaded."); return

        # ask for camera ID
        cam_id=simpledialog.askstring("Camera ID",
            "Enter a name/ID for this camera:\n(e.g.  CAM_01  or  GATE_NORTH)",
            initialvalue=f"CAM_{len(self.manager.workers)+1:02d}")
        if not cam_id: return

        # ask for source
        source=simpledialog.askstring("Camera Source",
            f"Source for {cam_id}:\n\n"
            "  0, 1, 2 ...  webcam index\n"
            "  rtsp://user:pass@ip:554/stream\n"
            "  /path/to/video.mp4",
            initialvalue="0")
        if source is None: return
        source=source.strip()
        source=int(source) if source.isdigit() else source

        self.manager.add_camera(cam_id, source)
        self._log(f"Camera added: {cam_id}  source={source}")
        self._set_mode("SCANNING",GREEN)
        self._setstatus(f"Camera {cam_id} started  source={source}",GREEN)

    def _stop_all(self):
        if not LIVE_AVAILABLE: return
        self.manager.stop_all()
        self._log("All cameras stopped")
        self._set_mode("IDLE",MUTED)
        self._setstatus("All cameras stopped",YELLOW)

    def _cam_status(self):
        if not LIVE_AVAILABLE:
            messagebox.showinfo("Status","multi_camera_manager not loaded."); return
        statuses=self.manager.camera_statuses()
        if not statuses:
            messagebox.showinfo("Camera Status","No cameras added yet.\n\nClick 'Add Camera' to start."); return
        lines=["CAMERA STATUS\n"]
        for cid,st in statuses.items():
            if isinstance(st,dict):
                fc=st.get("frames",0); stt=st.get("status","?")
                lines.append(f"  {cid:15s}  {stt:10s}  frames={fc}")
            else:
                fc=self.manager.workers[cid].frame_count
                lines.append(f"  {cid:15s}  {st:10s}  frames={fc}")
        lines.append(f"\nGlobal vehicles tracked: {self.manager.total_vehicles()}")
        messagebox.showinfo("Camera Status","\n".join(lines))

    def _load_camera_config(self):
        """Load a JSON config with 20-30 cameras and start them all."""
        if not LIVE_AVAILABLE:
            messagebox.showwarning("Unavailable","multi_camera_manager not loaded."); return
        from tkinter import filedialog
        path=filedialog.askopenfilename(
            title="Select camera config JSON",
            filetypes=[("JSON files","*.json"),("All files","*.*")],
            initialdir=BASE_DIR)
        if not path: return
        try:
            n=self.manager.add_cameras_from_json(path)
            self._log(f"Loaded {n} cameras from {os.path.basename(path)}")
            self._set_mode("SCANNING",GREEN)
            self._setstatus(f"{n} cameras started from config",GREEN)
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Config Error",str(e))

    def _multi_cam_summary(self):
        """Show vehicles confirmed on 2+ cameras (cross-camera re-ID proof)."""
        if not LIVE_AVAILABLE:
            messagebox.showinfo("Summary","multi_camera_manager not loaded."); return
        stats=self.manager.multi_camera_summary()
        lines=["MULTI-CAMERA RE-IDENTIFICATION\n"]
        lines.append(f"Registry vehicles      : {stats['registry_vehicles']}")
        lines.append(f"Seen on 2+ cameras     : {stats['seen_on_2plus_cameras']}")
        lines.append("")
        if stats["seen_on_2plus_vehicles"]:
            lines.append("VEHICLES TRACKED ACROSS CAMERAS:")
            for v in stats["seen_on_2plus_vehicles"][:20]:
                cams=", ".join(v["cameras"])
                lines.append(f"  {v['vehicle_id']:10s} {v['vehicle_type']:12s} "
                             f"{v['color']:8s} {v['number_plate']:12s} "
                             f"[{v['cameras_count']} cams] {cams}")
        else:
            lines.append("No vehicle seen on 2+ cameras yet.")
        lines.append("")
        lines.append("Vehicle types:")
        for t,c in stats["vehicle_types"].items():
            lines.append(f"  {t}: {c}")
        messagebox.showinfo("Multi-Camera Summary","\n".join(lines))

    # ── polling ───────────────────────────────────────────────────────────────

    def _poll(self):
        if LIVE_AVAILABLE and self.manager:
            events=self.manager.get_events(max_events=80)
            needs_refresh=False
            for evt in events:
                t=evt.get("type")
                if t=="detection":
                    self._total_frames+=1
                    self.frames_lbl.config(text=str(self._total_frames))
                    if evt.get("is_new"):
                        cid=evt.get("camera_id","?")
                        vid=evt.get("vehicle_id","?")
                        vt =evt.get("vehicle_type","?")
                        co =evt.get("color","?")
                        pl =evt.get("number_plate","UNKNOWN")
                        self._log(f"NEW  [{cid}]  {vid}  {vt}  {co}  plate={pl}")
                        needs_refresh=True
                    elif self._total_frames % 30 == 0:
                        needs_refresh=True
                elif t=="camera_online":
                    self._log(f"CAMERA ONLINE  {evt.get('camera_id')}  src={evt.get('source')}")
                    needs_refresh=True
                elif t=="camera_offline":
                    self._log(f"CAMERA OFFLINE  {evt.get('camera_id')}")
                    needs_refresh=True
                elif t=="merge":
                    self._log(f"MERGED  {evt.get('merged_from')} → {evt.get('vehicle_id')}  "
                              f"cams={','.join(evt.get('cameras') or [])}")
                    needs_refresh=True
                elif t=="error":
                    self._log(f"ERROR  [{evt.get('camera_id')}]  {evt.get('msg')}")

            if needs_refresh:
                self.refresh_data()

        self.root.after(150,self._poll)

    # ── tools ─────────────────────────────────────────────────────────────────

    def _show_all(self):
        self.search_var.set(""); self._populate()
        self._setstatus("DASHBOARD VIEW  all vehicles",GREEN)

    def _focus_search(self):
        self.search_var.set("")
        self._setstatus("VEHICLE SEARCH  type in search box",CYAN)

    def _show_tracking(self):
        tr=load_json(os.path.join(OUTPUT_DIR,"tracking_records.json"),[])
        n_cams=len(self.manager.workers) if self.manager else 0
        messagebox.showinfo("Tracking Data",
            f"Unique vehicles  : {len(self.vehicles)}\n"
            f"Active cameras   : {n_cams}\n"
            f"Tracking records : {len(tr)}")

    def _show_database(self):
        p=os.path.join(OUTPUT_DIR,"vehicle_database.db")
        if os.path.exists(p):
            messagebox.showinfo("Vehicle Database",
                f"STATUS: ONLINE\n\n{p}\n\n"
                f"Size: {os.path.getsize(p)//1024} KB\n"
                f"Vehicles indexed: {len(self.vehicles)}")
        else:
            messagebox.showwarning("Database","Database file not found.")

    def _setstatus(self,text,color=None):
        kw={"text":text}
        if color: kw["fg"]=color
        self.status_bar.config(**kw)


if __name__=="__main__":
    root=tk.Tk()
    VehicleDashboard(root)
    root.mainloop()