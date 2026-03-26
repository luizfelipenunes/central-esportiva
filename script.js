let eventosGlobais = [];
let filtroAtual = "todos";

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

const reais = eventosGlobais.filter(e => e.tipo !== "diagnostico");

if(reais.length === 0){
status.innerText = "Nenhum evento carregado.";
return;
}

status.innerText = `Eventos carregados: ${reais.length} • Primeiro evento: ${reais[0].titulo}`;
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

function filtrarEventosBase(filtro){
let base = eventosGlobais.filter(e => e.tipo !== "diagnostico");

if(filtro === "todos"){
return base;
}

return base.filter(evento =>
(evento.esporte || "").toLowerCase() === filtro.toLowerCase()
);
}

function ordenarEventos(lista){
return [...lista].sort((a,b)=>{
let pa = a.prioridade || 999;
let pb = b.prioridade || 999;

if(pa !== pb){
return pa - pb;
}

let da = a.data_ordem || "9999-99-99T99:99:99";
let db = b.data_ordem || "9999-99-99T99:99:99";
return da.localeCompare(db);
});
}

function criarCardEvento(evento){
let logo = pegarLogo(evento);

let card = document.createElement("div");
card.className = "evento";

if((evento.titulo || "").toLowerCase().includes("vasco")){
card.classList.add("evento-destaque");
}

card.innerHTML = `
<div class="titulo">
<img src="${logo}" class="logo" onerror="this.style.display='none'">
${evento.titulo}
</div>
<div class="hora">${linhaDataHora(evento)}</div>
<div class="transmissao">📺 ${evento.transmissao || "A confirmar"}</div>
<div class="transmissao">Fonte: ${evento.origem || "automática"}</div>
`;

return card;
}

function mostrarEventosDoDia(){
let container = document.getElementById("hoje");
if(!container) return;

container.innerHTML = "";

let eventos = filtrarEventosBase(filtroAtual).filter(e => e.dias_ate === 0);
eventos = ordenarEventos(eventos);

if(eventos.length === 0){
container.innerHTML = "<p>Nenhum evento hoje.</p>";
return;
}

eventos.forEach(evento => {
container.appendChild(criarCardEvento(evento));
});
}

function mostrarProximos7Dias(){
let agenda = document.getElementById("agenda");
if(!agenda) return;

agenda.innerHTML = "";

let eventos = filtrarEventosBase(filtroAtual).filter(e => {
return typeof e.dias_ate === "number" && e.dias_ate >= 1 && e.dias_ate <= 7;
});

eventos = ordenarEventos(eventos);

if(eventos.length === 0){
agenda.innerHTML = "<p>Nenhum evento nos próximos 7 dias.</p>";
return;
}

eventos.forEach(evento => {
agenda.appendChild(criarCardEvento(evento));
});
}

function mostrarProximos30Dias(){
let agenda30 = document.getElementById("agenda-30");
if(!agenda30) return;

agenda30.innerHTML = "";

let eventos = filtrarEventosBase(filtroAtual).filter(e => {
return typeof e.dias_ate === "number" && e.dias_ate >= 1 && e.dias_ate <= 30;
});

eventos = ordenarEventos(eventos);

if(eventos.length === 0){
agenda30.innerHTML = "<p>Nenhum evento nos próximos 30 dias.</p>";
return;
}

eventos.forEach(evento => {
agenda30.appendChild(criarCardEvento(evento));
});
}

function mostrarDiagnosticos(){
let diagnosticos = document.getElementById("diagnosticos");
let secao = document.getElementById("diagnosticos-section");

if(!diagnosticos || !secao) return;

const lista = eventosGlobais.filter(e => e.tipo === "diagnostico");

diagnosticos.innerHTML = "";

if(lista.length === 0){
secao.style.display = "none";
return;
}

secao.style.display = "block";

lista.forEach(evento => {
let card = document.createElement("div");
card.className = "evento";
card.innerHTML = `
<div class="titulo">${evento.titulo}</div>
<div class="transmissao">Fonte: ${evento.origem || "diagnostico"}</div>
`;
diagnosticos.appendChild(card);
});
}

function renderizarTudo(){
atualizarStatus();
mostrarEventosDoDia();
mostrarProximos7Dias();
mostrarProximos30Dias();
mostrarDiagnosticos();
}

function filtrar(esporte){
filtroAtual = esporte;
renderizarTudo();
}

function alternarProximos30Dias(){
let secao = document.getElementById("secao-30-dias");
let botao = document.getElementById("btn-30-dias");

if(!secao || !botao) return;

if(secao.style.display === "none"){
secao.style.display = "block";
botao.innerText = "Ocultar eventos dos próximos 30 dias";
} else {
secao.style.display = "none";
botao.innerText = "Ver eventos dos próximos 30 dias";
}
}

fetch("eventos.json?ts=" + Date.now())
.then(response => response.json())
.then(data => {
eventosGlobais = Array.isArray(data) ? data : [];
renderizarTudo();
})
.catch(error => {
console.error("Erro ao carregar eventos:", error);
let status = document.getElementById("status-dados");
if(status){
status.innerText = "Erro ao carregar eventos.";
}
});
