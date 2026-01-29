const loggedIn = localStorage.getItem("ds_logged") === "true";
const state = { scanning:false };

const el = {
    file: fileInput,
    drop: drop-zone,
    preview: preview-area,
    img: image-preview,
    scanner: upload-container,
    progress: main-progress,
    gauge: gauge-progress,
    percent: gauge-percent,
    logs: results-grid,
    history: history-container,
    status: main-status,
    session: session-status,
    lock: history-lock
};

window.onload = () => {
    el.session.textContent = loggedIn ? "Secure Mode" : "Guest Mode";
    el.lock.textContent = loggedIn ? "🔓" : "🔒";
};

/* Drag + Hover */
["dragover","dragleave","drop"].forEach(e=>{
    el.drop.addEventListener(e,ev=>{
        ev.preventDefault();
        el.drop.classList.toggle("drag-active",e==="dragover");
    });
});

el.drop.onclick = () => el.file.click();
el.file.onchange = () => handleFile(el.file.files[0]);
el.drop.addEventListener("drop",e=>handleFile(e.dataTransfer.files[0]));

function handleFile(file){
    if(!file||state.scanning) return;
    state.scanning=true;
    el.status.textContent="Analyzing image…";

    const r=new FileReader();
    r.onload=e=>{
        el.img.src=e.target.result;
        el.preview.classList.remove("hidden");
    };
    r.readAsDataURL(file);

    simulateScan();
}

function simulateScan(){
    let p=0;
    const i=setInterval(()=>{
        p+=4;
        el.progress.style.width=p+"%";
        if(p>=100){clearInterval(i);finishScan();}
    },80);
}

function finishScan(){
    animateGauge(85);
    addLog("GAN Detector","SAFE");
    addLog("Metadata Core","SAFE");
    if(loggedIn) addHistory(el.img.src);
    state.scanning=false;
}

function animateGauge(v){
    el.gauge.style.strokeDashoffset=126-(126*v/100);
    let c=0;
    const t=setInterval(()=>{
        el.percent.textContent=++c;
        if(c>=v) clearInterval(t);
    },20);
}

function addLog(n,s){
    const d=document.createElement("div");
    d.className="log-item";
    d.innerHTML=`<span>${n}</span><span>${s}</span>`;
    el.logs.appendChild(d);
}

function addHistory(src){
    const d=document.createElement("div");
    d.className="history-item";
    d.innerHTML=`<img src="${src}">`;
    const p=el.history.querySelector(".placeholder");
    p?p.replaceWith(d):el.history.prepend(d);
}
