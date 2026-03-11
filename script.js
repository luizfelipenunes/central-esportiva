let eventosGlobais = [];

function pegarLogo(evento){

let titulo = (evento.titulo || "").toLowerCase();
let esporte = (evento.esporte || "").toLowerCase();

if(titulo.includes("vasco")){
return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
}

if(titulo.includes("celtics") || esporte.includes("nba")){
return "https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png";
}

if(titulo.includes("seahawks") || esporte.includes("nfl")){
return "https://upload.wikimedia.org/wikipedia/commons/3/3a/American_football.svg";
}

if(esporte.includes("automobilismo")){
return "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg";
}

if(esporte.includes("futebol")){
return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
}

if(esporte.includes("tenis")){
return "https://upload.wikimedia.org/wikipedia/commons/3/3e/Tennis_Racket_and_Ball.svg";
}

return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
}

function atualizarStatus(){
let status = document.getElementById("status-dados");

if(!status) return;

if(eventosGlobais.length === 0){
status.innerText = "Nenhum evento carregado.";
return;
}

status.innerText = `Eventos carregados: ${eventosGlobais.length} • Primeiro evento: ${eventosGlobais[0].titulo}`;
}

function linhaDataHora(evento){
let data = evento.data || "";
let hora = evento.hora || "";

if(data && hora){
return `${data} • ${hora}`;
}

if(data){
return data;
}

if(hora){
return hora;
}

return "";
}

function mostrarEventoDoDia(){

let destaque = document.getElementById("destaque");

if(!destaque) return;

if(eventosGlobais.length === 0){
destaque.innerHTML = "<p>Nenhum evento hoje.</p>";
return;
}

let evento = eventosGlobais[0];
let logo = pegarLogo(evento);

destaque.innerHTML = `
<div class="evento destaque">
<div class="titulo">
<img src="${logo}" class="logo" onerror="this.style.display='none'">
${evento.titulo}
</div>
<div class="hora">${linhaDataHora(evento)}</div>
<div class="transmissao">📺 ${evento.transmissao || "A confirmar"}</div>
<div class="transmissao">Fonte: ${evento.origem || "automática"}</div>
</div>
`;
}

function mostrarEventos(filtro){

let agenda = document.getElementById("agenda");
agenda.innerHTML = "";

let eventosFiltrados = eventosGlobais;

if(filtro !== "todos"){
eventosFiltrados = eventosGlobais.filter(evento =>
(evento.esporte || "").toLowerCase() === filtro.toLowerCase()
);
}

if(eventosFiltrados.length === 0){
agenda.innerHTML = "<p>Nenhum evento encontrado.</p>";
return;
}

eventosFiltrados.sort((a,b)=>{
let pa = a.prioridade || 99;
let pb = b.prioridade || 99;

if(pa !== pb){
return pa - pb;
}

let da = a.data_ordem || "9999-99-99T99:99:99";
let db = b.data_ordem || "9999-99-99T99:99:99";
return da.localeCompare(db);
});

eventosFiltrados.forEach(evento => {
let logo = pegarLogo(evento);

let card = document.createElement("div");
card.className = "evento";

card.innerHTML = `
<div class="titulo">
<img src="${logo}" class="logo" onerror="this.style.display='none'">
${evento.titulo}
</div>
<div class="hora">${linhaDataHora(evento)}</div>
<div class="transmissao">📺 ${evento.transmissao || "A confirmar"}</div>
<div class="transmissao">Fonte: ${evento.origem || "automática"}</div>
`;

agenda.appendChild(card);
});
}

function filtrar(esporte){
mostrarEventos(esporte);
}

fetch("eventos.json?ts=" + Date.now())
.then(response => response.json())
.then(data => {
eventosGlobais = Array.isArray(data) ? data : [];
atualizarStatus();
mostrarEventoDoDia();
mostrarEventos("todos");
})
.catch(error => {
console.error("Erro ao carregar eventos:", error);
let status = document.getElementById("status-dados");
if(status){
status.innerText = "Erro ao carregar eventos.";
}
});
