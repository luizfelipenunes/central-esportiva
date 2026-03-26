let eventosGlobais = [];
let filtroAtual = "todos";

function normalizar(texto){
return (texto || "").toLowerCase();
}

function pegarLogo(evento){

let t = normalizar(evento.titulo);
let e = normalizar(evento.esporte);

if(t.includes("vasco")){
return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
}

if(t.includes("celtics")){
return "https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png";
}

if(t.includes("seahawks")){
return "https://upload.wikimedia.org/wikipedia/commons/3/3a/American_football.svg";
}

if(e.includes("nba")){
return "https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png";
}

if(e.includes("nfl")){
return "https://upload.wikimedia.org/wikipedia/commons/3/3a/American_football.svg";
}

if(e.includes("automobilismo")){
return "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg";
}

return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
}

function linhaDataHora(e){
return `${e.data} • ${e.hora}`;
}

function isDiagnostico(e){
return e.tipo === "diagnostico";
}

function isHoje(e){
return e.dias_ate === 0;
}

function is7Dias(e){
return e.dias_ate >= 1 && e.dias_ate <= 7;
}

function is30Dias(e){
return e.dias_ate >= 1 && e.dias_ate <= 30;
}

function destaque(e){
let t = normalizar(e.titulo);

if(t.includes("vasco")) return 1;
if(t.includes("celtics")) return 1;
if(t.includes("seahawks")) return 1;

return e.prioridade || 999;
}

function ordenar(lista){
return [...lista].sort((a,b)=>{

let pa = destaque(a);
let pb = destaque(b);

if(pa !== pb) return pa - pb;

return (a.data_ordem || "").localeCompare(b.data_ordem || "");

});
}

function card(e){

let logo = pegarLogo(e);

let el = document.createElement("div");
el.className = "evento";

if(destaque(e) === 1){
el.classList.add("evento-destaque");
}

el.innerHTML = `
<div class="titulo">
<img src="${logo}" class="logo">
${e.titulo}
</div>
<div class="hora">${linhaDataHora(e)}</div>
<div class="transmissao">📺 ${e.transmissao}</div>
<div class="transmissao">${e.origem}</div>
`;

return el;
}

function renderHoje(){

let container = document.getElementById("hoje");
container.innerHTML = "";

let lista = eventosGlobais.filter(e => !isDiagnostico(e) && isHoje(e));
lista = ordenar(lista);

lista.forEach(e => container.appendChild(card(e)));
}

function render7Dias(){

let container = document.getElementById("agenda");
container.innerHTML = "";

let lista = eventosGlobais.filter(e => !isDiagnostico(e) && is7Dias(e));
lista = ordenar(lista);

lista.forEach(e => container.appendChild(card(e)));
}

function render30Dias(){

let container = document.getElementById("agenda-30");
container.innerHTML = "";

let lista = eventosGlobais.filter(e => !isDiagnostico(e) && is30Dias(e));

let grupos = {};

lista.forEach(e=>{
if(!grupos[e.origem]) grupos[e.origem]=[];
grupos[e.origem].push(e);
});

for(let comp in grupos){

let bloco = document.createElement("div");

bloco.innerHTML = `<h3 onclick="toggle('${comp}')">▼ ${comp}</h3>
<div id="grupo-${comp}" class="grupo"></div>`;

container.appendChild(bloco);

let div = document.getElementById(`grupo-${comp}`);

ordenar(grupos[comp]).forEach(e=>{
div.appendChild(card(e));
});
}
}

function toggle(id){
let el = document.getElementById(`grupo-${id}`);
if(!el) return;

el.style.display = el.style.display === "none" ? "block" : "none";
}

function renderDiagnostico(){

let lista = eventosGlobais.filter(e => isDiagnostico(e));

let box = document.getElementById("diagnosticos");
box.innerHTML = "";

lista.forEach(e=>{
let d = document.createElement("div");
d.innerText = e.titulo;
box.appendChild(d);
});
}

function toggleDiagnostico(){

let el = document.getElementById("diagnosticos-section");

el.style.display = el.style.display === "none" ? "block" : "none";
}

function init(){

renderHoje();
render7Dias();
render30Dias();
renderDiagnostico();

}

fetch("eventos.json?ts=" + Date.now())
.then(r=>r.json())
.then(data=>{
eventosGlobais = data;
init();
});
