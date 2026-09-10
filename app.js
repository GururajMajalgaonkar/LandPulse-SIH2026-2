document.addEventListener("DOMContentLoaded", async ()=>{
  const mapEl=document.getElementById("map");
  if(!mapEl) return;

  const map=L.map("map").setView([19.93,75.65],9);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
    attribution:"© OpenStreetMap contributors"
  }).addTo(map);

  const data=await fetch("/api/map").then(r=>r.json());
  const bounds=[];

  data.forEach(p=>{
    if(p.lat==null || p.lng==null) return;
    bounds.push([p.lat,p.lng]);

    const color=p.risk==="High"?"#c94a4a":p.risk==="Medium"?"#d89b2b":"#0b7568";
    const icon=L.divIcon({
      className:"",
      html:`<div style="width:18px;height:18px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 1px 5px #777;cursor:pointer"></div>`,
      iconSize:[18,18]
    });

    const compensation=Number(p.compensation||0).toLocaleString("en-IN");
    const popup=`
      <div style="min-width:260px;font-family:system-ui">
        <div style="font-size:16px;font-weight:800;margin-bottom:8px">${p.survey_no}</div>
        <div style="font-size:12px;color:#64747d;margin-bottom:10px">${p.village}, ${p.district}, ${p.state}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;font-size:12px">
          <div><b>Land Owner</b><br>${p.owner_name||"Not available"}</div>
          <div><b>Area</b><br>${p.area||0} ha</div>
          <div><b>Compensation</b><br>₹${compensation}</div>
          <div><b>Payment</b><br>${p.payment_status||"Pending"}</div>
          <div><b>Project</b><br>${p.project_name||"Not assigned"}</div>
          <div><b>Risk</b><br><b>${p.risk||"Low"}</b></div>
        </div>
        <div style="margin-top:10px;padding-top:9px;border-top:1px solid #e2e9ec">
          <b>Status:</b> ${p.status||"Unknown"}<br>
          <a href="/parcel/${p.id}" style="display:inline-block;margin-top:8px;font-weight:700;color:#0b7568">Open Complete Case →</a>
        </div>
      </div>`;

    L.marker([p.lat,p.lng],{icon}).addTo(map).bindPopup(popup);
  });

  if(bounds.length) map.fitBounds(bounds,{padding:[25,25]});
});

setTimeout(()=>document.querySelectorAll(".toast").forEach(x=>x.remove()),3500);
