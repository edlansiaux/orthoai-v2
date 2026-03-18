import { useState, useEffect, useCallback, useRef } from "react";
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

// ── API ────────────────────────────────────────────────────────────────────────
const API = import.meta?.env?.VITE_API_URL || "";

async function apiFetch(path, opts = {}) {
  const r = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!r.ok) throw new Error(`API ${r.status}: ${r.statusText}`);
  return r.json();
}

// ── Design tokens ──────────────────────────────────────────────────────────────
const C = {
  bg:         "#060a13",
  surface:    "#0c1423",
  surfaceAlt: "#111827",
  border:     "#1a2535",
  borderHi:   "#243044",
  text:       "#e2e8f0",
  muted:      "#7b8ba5",
  dim:        "#4a5568",
  accent:     "#22d3ee",
  accentDark: "#0e7490",
  critical:   "#ef4444",
  warning:    "#f59e0b",
  success:    "#22c55e",
  info:       "#3b82f6",
  gradeA:     "#22c55e",
  gradeB:     "#22d3ee",
  gradeC:     "#f59e0b",
  gradeD:     "#ef4444",
  gradeF:     "#dc2626",
  stub:       "#f59e0b",
};
const F  = "'JetBrains Mono', monospace";
const F2 = "'Outfit', sans-serif";
const gc = g => ({ A:C.gradeA, B:C.gradeB, C:C.gradeC, D:C.gradeD, F:C.gradeF }[g] || C.muted);
const card  = (x={}) => ({ background:C.surface, border:`1px solid ${C.border}`, borderRadius:10, padding:12, ...x });
const lbl   = (x={}) => ({ fontSize:9, fontFamily:F, color:C.muted, letterSpacing:"0.08em", textTransform:"uppercase", ...x });
const val   = (x={}) => ({ fontSize:22, fontWeight:700, color:C.text, fontFamily:F, lineHeight:1, ...x });
const badge = (color, x={}) => ({ display:"inline-flex", alignItems:"center", gap:4, padding:"2px 8px", borderRadius:6, background:`${color}12`, border:`1px solid ${color}28`, color, fontSize:9, fontFamily:F, fontWeight:600, ...x });
const btn   = (color=C.accent) => ({ background:`${color}18`, border:`1px solid ${color}30`, color, borderRadius:6, cursor:"pointer", fontFamily:F, fontSize:9, padding:"4px 10px", fontWeight:600 });
const sev   = { critical:{color:C.critical,icon:"🔴",label:"Critique"}, warning:{color:C.warning,icon:"🟡",label:"Attention"}, info:{color:C.info,icon:"🔵",label:"Info"} };

// ── Stub engine banner ─────────────────────────────────────────────────────────
function StubBanner({ engine }) {
  const [show, setShow] = useState(true);
  if (!show || engine === "OrthalytixScorer") return null;
  return (
    <div style={{ background:`${C.stub}14`, border:`1px solid ${C.stub}30`, borderRadius:8, padding:"8px 14px", margin:"8px 12px 0", display:"flex", justifyContent:"space-between", alignItems:"center", gap:12 }}>
      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
        <span style={{ fontSize:13 }}>⚠️</span>
        <span style={{ fontSize:9, fontFamily:F, color:C.stub }}>
          <b>STUB ENGINE</b> — scores non calibrés à des fins de démonstration.{" "}
          <a href="https://orthalytix.com/orthoai" target="_blank" rel="noreferrer"
             style={{ color:C.stub, textDecoration:"underline" }}>
            Obtenir une licence Orthalytix
          </a>{" "}pour des scores cliniques.
        </span>
      </div>
      <button onClick={() => setShow(false)} style={{ ...btn(C.stub), padding:"2px 6px" }}>✕</button>
    </div>
  );
}

// ── Gauge ──────────────────────────────────────────────────────────────────────
function Gauge({ value=0, label="", size=100, stroke=7 }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const color = value>=90?C.gradeA:value>=75?C.gradeB:value>=60?C.gradeC:value>=40?C.gradeD:C.gradeF;
  return (
    <svg width={size} height={size} style={{ display:"block", margin:"0 auto" }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={C.border} strokeWidth={stroke}/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={stroke}
        strokeDasharray={circ} strokeDashoffset={circ*(1-value/100)}
        strokeLinecap="round" transform={`rotate(-90 ${size/2} ${size/2})`}
        style={{ filter:`drop-shadow(0 0 6px ${color}60)`, transition:"stroke-dashoffset 0.8s ease" }}/>
      <text x={size/2} y={size/2-4}  textAnchor="middle" fill={color} fontSize={size>90?18:13} fontWeight={700} fontFamily={F}>{Math.round(value)}</text>
      <text x={size/2} y={size/2+12} textAnchor="middle" fill={C.muted} fontSize={8} fontFamily={F}>{label}</text>
    </svg>
  );
}

// ── Sub-score bar ──────────────────────────────────────────────────────────────
function SubBar({ label, value, color }) {
  return (
    <div style={{ marginBottom:6 }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:3 }}>
        <span style={{ fontSize:9, fontFamily:F, color:C.muted }}>{label}</span>
        <span style={{ fontSize:9, fontFamily:F, color:color||C.text, fontWeight:600 }}>{Math.round(value)}</span>
      </div>
      <div style={{ height:3, background:C.border, borderRadius:2, overflow:"hidden" }}>
        <div style={{ height:"100%", width:`${value}%`, background:color||C.accent, borderRadius:2, transition:"width 0.6s ease", boxShadow:`0 0 4px ${color||C.accent}60` }}/>
      </div>
    </div>
  );
}

// ── 3D Arch (Three.js via CDN) ─────────────────────────────────────────────────
function ArchView({ movements=[], selectedFdi, onSelect, phase=3 }) {
  const ref      = useRef(null);
  const sceneRef = useRef(null);

  useEffect(() => {
    if (!ref.current || phase < 2) return;
    const init = () => {
      const THREE = window.THREE;
      if (!THREE || sceneRef.current) return;
      const W = ref.current.clientWidth, H = 220;
      const renderer = new THREE.WebGLRenderer({ antialias:true, alpha:true });
      renderer.setSize(W, H); renderer.setPixelRatio(window.devicePixelRatio);
      ref.current.appendChild(renderer.domElement);
      const scene  = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(50, W/H, 0.1, 200);
      camera.position.set(0, -10, 55); camera.lookAt(0,0,0);
      scene.add(new THREE.AmbientLight(0xffffff, 0.4));
      const dl = new THREE.DirectionalLight(0xffffff, 0.8); dl.position.set(10,20,30); scene.add(dl);
      scene.add(new THREE.PointLight(0x22d3ee, 0.4, 80));
      const toothMeshes = {};
      const upper = movements.filter(m=>m.fdi>=11&&m.fdi<=28).map(m=>m.fdi).sort();
      const lower = movements.filter(m=>m.fdi>=31&&m.fdi<=48).map(m=>m.fdi).sort();
      const addTooth = (fdi, x, y, z, isUpper) => {
        const n = fdi%10;
        const geo = n<=2 ? new THREE.CylinderGeometry(1.2,1.4,3.5,12)
                  : n==3 ? new THREE.CylinderGeometry(1.4,1.6,3.8,12)
                  : n<=5 ? new THREE.SphereGeometry(1.6,12,8)
                         : new THREE.BoxGeometry(2.8,3.0,2.0);
        const isSel = fdi===selectedFdi;
        const mat = new THREE.MeshPhongMaterial({
          color: isSel ? 0x22d3ee : (isUpper ? 0xf5efe6 : 0xeee0d0),
          emissive: isSel ? 0x0e7490 : 0x000000,
          shininess:80, transparent:true, opacity:0.95,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x,y,z); mesh.userData={fdi}; scene.add(mesh); toothMeshes[fdi]=mesh;
      };
      upper.forEach((fdi,i) => { const t=Math.PI*(i/Math.max(upper.length-1,1)-0.5); addTooth(fdi, 26*Math.sin(t), 16*Math.cos(t)*0.5, 2, true); });
      lower.forEach((fdi,i) => { const t=Math.PI*(i/Math.max(lower.length-1,1)-0.5); addTooth(fdi, 23*Math.sin(t), 14*Math.cos(t)*0.5, -10, false); });
      const raycaster=new THREE.Raycaster(), mouse=new THREE.Vector2();
      renderer.domElement.addEventListener("click", e => {
        const rect=renderer.domElement.getBoundingClientRect();
        mouse.x=((e.clientX-rect.left)/rect.width)*2-1;
        mouse.y=-((e.clientY-rect.top)/rect.height)*2+1;
        raycaster.setFromCamera(mouse,camera);
        const hits=raycaster.intersectObjects(Object.values(toothMeshes));
        if (hits.length>0) onSelect?.(hits[0].object.userData.fdi);
      });
      let angle=0;
      const animate=()=>{ requestAnimationFrame(animate); angle+=0.003; camera.position.x=Math.sin(angle)*5; camera.position.y=-10+Math.cos(angle*0.5)*2; camera.lookAt(0,0,0); renderer.render(scene,camera); };
      animate();
      sceneRef.current={renderer,scene,toothMeshes};
    };
    if (!document.getElementById("three-js")) {
      const s=document.createElement("script"); s.id="three-js";
      s.src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js";
      s.onload=init; document.head.appendChild(s);
    } else if (window.THREE) { init(); }
    else { document.getElementById("three-js").addEventListener("load",init); }
    return () => { if(sceneRef.current){sceneRef.current.renderer.dispose(); sceneRef.current=null; if(ref.current) ref.current.innerHTML="";} };
  }, [movements, phase]);

  return (
    <div ref={ref} style={{ width:"100%", height:220, borderRadius:8, overflow:"hidden", background:"rgba(6,10,19,0.6)", cursor:"pointer" }}>
      {phase < 2 && <div style={{ height:220, display:"flex", alignItems:"center", justifyContent:"center", color:C.muted, fontSize:9, fontFamily:F }}>Chargement 3D…</div>}
    </div>
  );
}

// ── Frame Timeline ─────────────────────────────────────────────────────────────
function FrameTimeline({ frames=[], movements=[] }) {
  const [idx, setIdx]       = useState(0);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing || !frames.length) return;
    const t = setInterval(() => setIdx(i => { if (i>=frames.length-1){setPlaying(false);return i;} return i+1; }), 60);
    return () => clearInterval(t);
  }, [playing, frames.length]);
  if (!frames.length) return null;
  const frame = frames[idx];
  const pct   = Math.round((frame?.progress||0)*100);
  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
        <div style={lbl()}>Simulation traitement — {frames.length} frames</div>
        <div style={{ display:"flex", gap:4 }}>
          <button onClick={()=>{setIdx(0);setPlaying(false);}}          style={{...btn(C.dim),padding:"3px 8px",fontSize:9}}>⏮</button>
          <button onClick={()=>setPlaying(p=>!p)}                       style={{...btn(C.accent),padding:"3px 10px",fontSize:11}}>{playing?"⏸":"▶"}</button>
          <button onClick={()=>{setIdx(frames.length-1);setPlaying(false);}} style={{...btn(C.dim),padding:"3px 8px",fontSize:9}}>⏭</button>
        </div>
      </div>
      <div style={{ marginBottom:6 }}>
        <div style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
          <span style={{ fontSize:9, fontFamily:F, color:C.accent }}>Aligneur {frame?.aligner_number||0}</span>
          <span style={{ fontSize:9, fontFamily:F, color:C.muted }}>{frame?.notes}</span>
          <span style={{ fontSize:9, fontFamily:F, color:C.text }}>{pct}%</span>
        </div>
        <div style={{ height:4, background:C.border, borderRadius:2 }}>
          <div style={{ height:"100%", width:`${pct}%`, background:`linear-gradient(90deg,${C.accentDark},${C.accent})`, borderRadius:2, transition:"width 0.05s linear" }}/>
        </div>
      </div>
      <input type="range" min={0} max={frames.length-1} value={idx}
        onChange={e=>{ setIdx(Number(e.target.value)); setPlaying(false); }}
        style={{ width:"100%", accentColor:C.accent, marginBottom:8 }}/>
      {/* Per-tooth progress bars — first 6 */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:4 }}>
        {movements.slice(0,6).map(mv => {
          const tf = frame?.teeth?.[String(mv.fdi)] || frame?.teeth?.[mv.fdi];
          const prog = tf ? Math.min(100, Math.round((frame.progress||0)*100)) : 0;
          return (
            <div key={mv.fdi} style={{ fontSize:8, fontFamily:F, color:C.muted }}>
              <div style={{ display:"flex", justifyContent:"space-between" }}>
                <span>{mv.name||`FDI-${mv.fdi}`}</span><span style={{ color:C.accent }}>{prog}%</span>
              </div>
              <div style={{ height:2, background:C.border, borderRadius:1, marginTop:2 }}>
                <div style={{ height:"100%", width:`${prog}%`, background:C.accent, borderRadius:1 }}/>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Movements table ────────────────────────────────────────────────────────────
function MovementsTable({ movements=[], selected, onSelect }) {
  const cols = ["FDI","Nom","Tx","Ty","Tz","Rx","Ry","Rz","Pred%","Att","IPR","Ext"];
  return (
    <div style={{ overflowX:"auto" }}>
      <table style={{ width:"100%", borderCollapse:"collapse", fontSize:9, fontFamily:F }}>
        <thead>
          <tr>{cols.map(c=><th key={c} style={{ textAlign:"left", padding:"4px 6px", color:C.muted, borderBottom:`1px solid ${C.border}`, whiteSpace:"nowrap" }}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {movements.map(mv => {
            const isSel = mv.fdi===selected;
            return (
              <tr key={mv.fdi} onClick={()=>onSelect(mv.fdi)}
                style={{ cursor:"pointer", background:isSel?`${C.accent}12`:"transparent", borderBottom:`1px solid ${C.border}` }}>
                <td style={{ padding:"4px 6px", color:isSel?C.accent:C.text, fontWeight:isSel?700:400 }}>{mv.fdi}</td>
                <td style={{ padding:"4px 6px", color:C.muted, whiteSpace:"nowrap" }}>{mv.name}</td>
                {["tx","ty","tz","rx","ry","rz"].map(k=>(
                  <td key={k} style={{ padding:"4px 6px", color:Math.abs(mv[k])>2?C.warning:C.text, textAlign:"right" }}>{mv[k]?.toFixed(1)}</td>
                ))}
                <td style={{ padding:"4px 6px", textAlign:"right", color:mv.predictability<60?C.warning:C.success }}>{mv.predictability?.toFixed(0)}</td>
                <td style={{ padding:"4px 6px", textAlign:"center" }}>{mv.needs_attachment?"✓":""}</td>
                <td style={{ padding:"4px 6px", textAlign:"center" }}>{mv.needs_ipr?"✓":""}</td>
                <td style={{ padding:"4px 6px", textAlign:"center", color:mv.is_extrusion?C.critical:"" }}>{mv.is_extrusion?"↑":""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Checklist ──────────────────────────────────────────────────────────────────
function Checklist({ score }) {
  if (!score) return null;
  const items = [
    { label:"Score biomécanique ≥ 75",     done:score.biomechanics>=75   },
    { label:"Staging validé",              done:score.staging>=70        },
    { label:"Attachements planifiés",      done:score.attachments>=80    },
    { label:"IPR documentée",              done:score.ipr>=80            },
    { label:"Occlusion finale vérifiée",   done:score.occlusion>=75      },
    { label:"Prédictabilité acceptable",   done:score.predictability>=70 },
    { label:"Aucun finding critique",      done:score.findings.filter(f=>f.severity==="critical").length===0 },
    { label:"Grade ≥ B",                   done:["A","B"].includes(score.grade) },
    { label:"Protocole de révision fait",  done:score.overall>=80        },
    { label:"Validation clinicien",        done:false                    },
  ];
  const done = items.filter(i=>i.done).length;
  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:10 }}>
        <div style={lbl()}>Pré-approbation plan</div>
        <div style={{ fontSize:9, fontFamily:F, color:done===items.length?C.success:C.muted }}>{done}/{items.length}</div>
      </div>
      <div style={{ height:3, background:C.border, borderRadius:2, marginBottom:12 }}>
        <div style={{ height:"100%", width:`${done/items.length*100}%`, background:C.success, borderRadius:2, transition:"width 0.4s" }}/>
      </div>
      {items.map((it,i)=>(
        <div key={i} style={{ display:"flex", alignItems:"center", gap:8, padding:"5px 0", borderBottom:`1px solid ${C.border}` }}>
          <div style={{ width:14, height:14, borderRadius:3, border:`1px solid ${it.done?C.success:C.dim}`, background:it.done?`${C.success}20`:"transparent", display:"flex", alignItems:"center", justifyContent:"center", fontSize:9 }}>
            {it.done ? "✓" : ""}
          </div>
          <span style={{ fontSize:10, fontFamily:F2, color:it.done?C.text:C.muted }}>{it.label}</span>
        </div>
      ))}
    </div>
  );
}

// ── Training section ───────────────────────────────────────────────────────────
function Training({ data }) {
  const { dgcnn={}, charm={}, training_curves=[], engine, weights_included } = data||{};
  return (
    <div>
      <div style={{ ...card({ marginBottom:10, background:`${C.warning}08`, border:`1px solid ${C.warning}25` }) }}>
        <div style={{ fontSize:9, fontFamily:F, color:C.warning, marginBottom:4 }}>⚠️ Poids non inclus dans le repo open-source</div>
        <div style={{ fontSize:9, fontFamily:F2, color:C.muted }}>
          Architecture DGCNN + CHaRM publiée (MIT). Poids pré-entraînés disponibles via{" "}
          <a href="https://orthalytix.com/orthoai" target="_blank" rel="noreferrer" style={{ color:C.accent }}>licence Orthalytix</a>.
        </div>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:12 }}>
        {[
          { title:"DGCNN_Seg", items:[["Params",`${(dgcnn.params||60705).toLocaleString()}`],["Best mIoU",`${((dgcnn.best_miou||0.814)*100)|0}%`],["TIR",`${((dgcnn.best_tir||0.812)*100)|0}%`],["Status",dgcnn.status||"–"]] },
          { title:"CHaRM",     items:[["MEDE",`${charm.mede_mm||1.38}mm`],["MSR",`${charm.msr_pct||64.2}%`],["GPU",`0.31s`],["Status",charm.status||"–"]] },
        ].map(({ title, items }) => (
          <div key={title} style={card()}>
            <div style={{ fontSize:10, fontFamily:F, color:C.accent, fontWeight:700, marginBottom:8 }}>{title}</div>
            {items.map(([k,v])=>(
              <div key={k} style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
                <span style={{ fontSize:9, fontFamily:F, color:C.muted }}>{k}</span>
                <span style={{ fontSize:9, fontFamily:F, color:C.text }}>{v}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
      <div style={{ fontSize:9, fontFamily:F, color:C.dim, textAlign:"center" }}>
        arXiv:2603.00124v2 · DGCNN (Wang 2019) + CHaRM (Rodríguez-Ortega 2025) · STaR-AI / CHU de Lille
      </div>
    </div>
  );
}

// ── Patient card ───────────────────────────────────────────────────────────────
function PatientCard({ p, active, onClick }) {
  const comp = { simple:C.success, moderate:C.warning, complex:C.critical }[p.complexity]||C.muted;
  return (
    <div onClick={onClick} style={{ ...card({ cursor:"pointer", border:`1px solid ${active?C.accent:C.border}`, background:active?`${C.accent}08`:C.surface, transition:"all 0.2s" }) }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:4 }}>
        <div style={{ fontSize:11, fontFamily:F2, fontWeight:600, color:active?C.accent:C.text }}>{p.patient_name}</div>
        <div style={{ ...badge(comp), fontSize:7 }}>{p.complexity}</div>
      </div>
      <div style={{ fontSize:9, fontFamily:F2, color:C.muted, marginBottom:2 }}>{p.case_type}</div>
      <div style={{ fontSize:8, fontFamily:F, color:C.dim }}>{p.num_stages} étapes · {p.n_teeth} dents</div>
    </div>
  );
}

// ── Pipeline status ────────────────────────────────────────────────────────────
function Pipeline({ phase }) {
  const steps = ["Scan","Landmarks","DGCNN","Analyse"];
  return (
    <div style={{ display:"flex", gap:0, alignItems:"center" }}>
      {steps.map((s,i) => {
        const done   = phase > i;
        const active = phase === i;
        return (
          <div key={s} style={{ display:"flex", alignItems:"center" }}>
            <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:2 }}>
              <div style={{ width:20, height:20, borderRadius:"50%", border:`1.5px solid ${done?C.success:active?C.accent:C.border}`, background:done?`${C.success}20`:active?`${C.accent}20`:"transparent", display:"flex", alignItems:"center", justifyContent:"center", fontSize:8, color:done?C.success:active?C.accent:C.dim, transition:"all 0.4s" }}>
                {done ? "✓" : i+1}
              </div>
              <span style={{ fontSize:7, fontFamily:F, color:done?C.success:active?C.accent:C.dim, whiteSpace:"nowrap" }}>{s}</span>
            </div>
            {i<steps.length-1 && <div style={{ width:20, height:1, background:phase>i?C.success:C.border, margin:"0 2px", transition:"background 0.4s" }}/>}
          </div>
        );
      })}
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────────
export default function App() {
  const [section,    setSection]    = useState("dashboard");
  const [patientId,  setPatientId]  = useState("patient_001");
  const [data,       setData]       = useState(null);
  const [patients,   setPatients]   = useState([]);
  const [trainData,  setTrainData]  = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);
  const [phase,      setPhase]      = useState(0);
  const [selFdi,     setSelFdi]     = useState(null);
  const [findFilter, setFindFilter] = useState("all");

  const score     = data?.score;
  const movements = data?.movements || [];
  const findings  = score?.findings || [];
  const frames    = data?.frames    || [];
  const engine    = data?.metadata?.engine || trainData?.engine || "StubScorer";

  // Load patients + training on mount
  useEffect(() => {
    apiFetch("/api/patients").then(d=>setPatients(d.patients||[])).catch(()=>{});
    apiFetch("/api/training/status").then(setTrainData).catch(()=>{});
  }, []);

  // Load patient data
  const loadPatient = useCallback(async (id) => {
    setLoading(true); setError(null); setPhase(0); setSelFdi(null);
    setTimeout(()=>setPhase(1), 500);
    setTimeout(()=>setPhase(2), 1200);
    setTimeout(()=>setPhase(3), 2000);
    try {
      setData(await apiFetch(`/api/patients/${id}`));
    } catch(e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { if (patientId) loadPatient(patientId); }, [patientId]);

  const gradeColor  = score ? gc(score.grade) : C.muted;
  const n_crit      = findings.filter(f=>f.severity==="critical").length;
  const n_warn      = findings.filter(f=>f.severity==="warning").length;
  const visFindings = findFilter==="all" ? findings : findings.filter(f=>f.severity===findFilter);
  const selMv       = movements.find(m=>m.fdi===selFdi);

  const NAV = [
    ["dashboard","🗂 Dashboard"],
    ["frames",   "🎬 Simulation"],
    ["movements","📊 Mouvements"],
    ["alerts",   `⚠️ Alertes${n_crit>0?` (${n_crit})`:n_warn>0?` (${n_warn})`:""}`],
    ["checklist","✅ Checklist"],
    ["training", "🧠 Entraînement"],
  ];

  return (
    <div style={{ minHeight:"100vh", background:C.bg, color:C.text, fontFamily:F2 }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet"/>
      <style>{`*{box-sizing:border-box;margin:0}::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:${C.border};border-radius:4px}@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}input[type=range]{height:4px}`}</style>

      {/* Header */}
      <header style={{ padding:"8px 16px", display:"flex", justifyContent:"space-between", alignItems:"center", borderBottom:`1px solid ${C.border}`, background:"rgba(6,10,19,0.95)", backdropFilter:"blur(12px)", position:"sticky", top:0, zIndex:50 }}>
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ width:32, height:32, borderRadius:8, background:`linear-gradient(135deg,${C.accentDark},${C.accent})`, display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 }}>🦷</div>
          <div>
            <div style={{ fontSize:14, fontWeight:800, letterSpacing:"-0.02em" }}>
              OrthoAI <span style={{ color:C.accent, fontFamily:F, fontSize:9, fontWeight:600 }}>v2</span>
            </div>
            <div style={{ fontSize:8, color:C.dim, fontFamily:F }}>DGCNN · CHaRM · Multi-agents · arXiv:2603.00124v2</div>
          </div>
          {score && <div style={{ marginLeft:8, ...badge(gradeColor,{padding:"4px 10px",fontSize:10}) }}>Grade {score.grade} — {score.overall}/100</div>}
        </div>
        <nav style={{ display:"flex", gap:2 }}>
          {NAV.map(([id,label])=>(
            <button key={id} onClick={()=>setSection(id)}
              style={{ ...btn(section===id?C.accent:C.dim), background:section===id?`${C.accent}20`:"transparent", border:section===id?`1px solid ${C.accent}40`:"1px solid transparent", borderRadius:6, padding:"5px 10px", fontSize:9 }}>
              {label}
            </button>
          ))}
        </nav>
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <Pipeline phase={phase}/>
        </div>
      </header>

      {/* Stub banner */}
      <StubBanner engine={engine}/>

      {error && <div style={{ margin:"8px 12px", padding:"8px 12px", background:`${C.critical}15`, border:`1px solid ${C.critical}30`, borderRadius:8, fontSize:10, fontFamily:F, color:C.critical }}>Erreur: {error}</div>}

      {/* Content */}
      <main style={{ padding:"12px 16px", maxWidth:1400, margin:"0 auto" }}>

        {/* ── Dashboard ─────────────────────────────────────────────────────── */}
        {section==="dashboard" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10, animation:"fadeIn 0.3s ease" }}>

            {/* Score col */}
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              <div style={card()}>
                <div style={lbl({marginBottom:8})}>Score global</div>
                {score ? (
                  <>
                    <Gauge value={score.overall} label={`Grade ${score.grade}`} size={110}/>
                    <div style={{ marginTop:12 }}>
                      <SubBar label="Biomécanique"   value={score.biomechanics}   color={score.biomechanics>=75?C.success:C.warning}/>
                      <SubBar label="Staging"        value={score.staging}        color={C.accent}/>
                      <SubBar label="Attachements"   value={score.attachments}    color={C.info}/>
                      <SubBar label="IPR"            value={score.ipr}            color={C.info}/>
                      <SubBar label="Occlusion"      value={score.occlusion}      color={C.success}/>
                      <SubBar label="Prédictabilité" value={score.predictability} color={C.warning}/>
                    </div>
                  </>
                ) : <div style={{ height:110, display:"flex", alignItems:"center", justifyContent:"center", color:C.dim, fontSize:9, fontFamily:F }}>Chargement…</div>}
              </div>

              {/* Stats */}
              {data && (
                <div style={card()}>
                  <div style={lbl({marginBottom:8})}>Plan</div>
                  {[["Étapes",data.num_stages],["Durée",`${data.duration_months} mois`],["Dents",movements.length],["Critiques",`${n_crit}`],["Avertissements",`${n_warn}`]].map(([k,v])=>(
                    <div key={k} style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
                      <span style={{ fontSize:9, fontFamily:F, color:C.muted }}>{k}</span>
                      <span style={{ fontSize:9, fontFamily:F, color:C.text }}>{v}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 3D col */}
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              <div style={card()}>
                <div style={lbl({marginBottom:6})}>Visualisation 3D — cliquer pour sélectionner</div>
                <ArchView movements={movements} selectedFdi={selFdi} onSelect={setSelFdi} phase={phase}/>
                {selMv && (
                  <div style={{ marginTop:8, padding:8, background:C.surfaceAlt, borderRadius:6 }}>
                    <div style={{ fontSize:10, fontFamily:F, color:C.accent, fontWeight:700, marginBottom:6 }}>{selMv.name}</div>
                    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:4 }}>
                      {["tx","ty","tz","rx","ry","rz"].map(k=>(
                        <div key={k} style={{ textAlign:"center" }}>
                          <div style={{ fontSize:7, fontFamily:F, color:C.muted, marginBottom:2 }}>{k.toUpperCase()}</div>
                          <div style={{ fontSize:11, fontFamily:F, color:Math.abs(selMv[k])>2?C.warning:C.text, fontWeight:600 }}>{selMv[k]?.toFixed(1)}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ display:"flex", gap:4, marginTop:6, flexWrap:"wrap" }}>
                      {selMv.needs_attachment && <span style={badge(C.info)}>Attachment</span>}
                      {selMv.needs_ipr        && <span style={badge(C.warning)}>IPR</span>}
                      {selMv.is_extrusion     && <span style={badge(C.critical)}>Extrusion</span>}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Patients + findings col */}
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              <div style={card()}>
                <div style={lbl({marginBottom:8})}>Patients preset</div>
                <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  {patients.map(p=><PatientCard key={p.patient_id} p={p} active={patientId===p.patient_id} onClick={()=>setPatientId(p.patient_id)}/>)}
                </div>
              </div>
              {findings.filter(f=>["critical","warning"].includes(f.severity)).slice(0,3).map((f,i)=>(
                <div key={i} style={{ ...card({ border:`1px solid ${sev[f.severity]?.color}30`, background:`${sev[f.severity]?.color}08` }) }}>
                  <div style={{ fontSize:9, fontFamily:F, color:sev[f.severity]?.color, fontWeight:600, marginBottom:3 }}>{sev[f.severity]?.icon} {f.title}</div>
                  <div style={{ fontSize:8, fontFamily:F2, color:C.muted }}>{f.description}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Simulation ────────────────────────────────────────────────────── */}
        {section==="frames" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, animation:"fadeIn 0.3s ease" }}>
            <div style={card()}>
              <FrameTimeline frames={frames} movements={movements}/>
            </div>
            <div style={card()}>
              <div style={lbl({marginBottom:8})}>Distribution des mouvements</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={movements.slice(0,12).map(m=>({ name:m.fdi, Tx:Math.abs(m.tx), Rz:Math.abs(m.rz) }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
                  <XAxis dataKey="name" tick={{fill:C.muted,fontSize:8}} stroke={C.border}/>
                  <YAxis tick={{fill:C.muted,fontSize:8}} stroke={C.border}/>
                  <Tooltip contentStyle={{background:C.surface,border:`1px solid ${C.border}`,borderRadius:6,fontSize:9}}/>
                  <Bar dataKey="Tx" fill={C.accent}    radius={[3,3,0,0]}/>
                  <Bar dataKey="Rz" fill={C.accentDark} radius={[3,3,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* ── Movements ─────────────────────────────────────────────────────── */}
        {section==="movements" && (
          <div style={{ ...card(), animation:"fadeIn 0.3s ease" }}>
            <div style={lbl({marginBottom:10})}>Tableau des mouvements 6-DoF</div>
            <MovementsTable movements={movements} selected={selFdi} onSelect={setSelFdi}/>
          </div>
        )}

        {/* ── Alerts ────────────────────────────────────────────────────────── */}
        {section==="alerts" && (
          <div style={{ animation:"fadeIn 0.3s ease" }}>
            <div style={{ display:"flex", gap:6, marginBottom:10 }}>
              {["all","critical","warning","info"].map(f=>(
                <button key={f} onClick={()=>setFindFilter(f)} style={{ ...btn(findFilter===f?C.accent:C.dim), background:findFilter===f?`${C.accent}20`:"transparent", textTransform:"capitalize" }}>{f}</button>
              ))}
            </div>
            {visFindings.length === 0 && (
              <div style={{ textAlign:"center", padding:40, color:C.dim, fontSize:10, fontFamily:F }}>Aucun finding{findFilter!=="all"?` de type ${findFilter}`:""}</div>
            )}
            <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
              {visFindings.map((f,i)=>(
                <div key={i} style={{ ...card({ border:`1px solid ${sev[f.severity]?.color}25`, background:`${sev[f.severity]?.color}06` }) }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:4 }}>
                    <div style={{ fontSize:10, fontFamily:F, color:sev[f.severity]?.color, fontWeight:700 }}>{sev[f.severity]?.icon} {f.title}</div>
                    <span style={badge(sev[f.severity]?.color)}>{sev[f.severity]?.label}</span>
                  </div>
                  <div style={{ fontSize:9, fontFamily:F2, color:C.muted, marginBottom:4 }}>{f.description}</div>
                  <div style={{ fontSize:8, fontFamily:F2, color:C.dim, fontStyle:"italic" }}>→ {f.recommendation}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Checklist ─────────────────────────────────────────────────────── */}
        {section==="checklist" && (
          <div style={{ ...card({ maxWidth:520, margin:"0 auto" }), animation:"fadeIn 0.3s ease" }}>
            <Checklist score={score}/>
          </div>
        )}

        {/* ── Training ──────────────────────────────────────────────────────── */}
        {section==="training" && (
          <div style={{ maxWidth:700, margin:"0 auto", animation:"fadeIn 0.3s ease" }}>
            <div style={card({marginBottom:8})}>
              <div style={{ fontSize:9, fontFamily:F, color:C.muted, marginBottom:6, lineHeight:1.6 }}>
                DGCNN_Seg (60,705 params, k=20) + CHaRM (PointMLP emb=128) · Dataset: 3DTeethLand MICCAI 2024
                <br/>Entraîner: <span style={{ color:C.accent }}>ORTHOAI_LICENSE_KEY=xxx python scripts/train.py</span> (requires commercial engine)
              </div>
            </div>
            <Training data={trainData}/>
          </div>
        )}

      </main>
    </div>
  );
}
