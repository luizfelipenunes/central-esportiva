let eventosGlobais = [];

function pegarLogo(evento){

let titulo = evento.titulo.toLowerCase();
let esporte = evento.esporte.toLowerCase();

/* Times */

if(titulo.includes("vasco")){
return "https://upload.wikimedia.org/wikipedia/commons/9/9a/CR_Vasco_da_Gama_logo.svg";
}

if(titulo.includes("celtics")){
return "https://upload.wikimedia.org/wikipedia/en/8/8f/Boston_Celtics.svg";
}

if(titulo.includes("seahawks")){
return "https://upload.wikimedia.org/wikipedia/en/8/8e/Seattle_Seahawks_logo.svg";
}

/* Esportes */

if(esporte.includes("automobilismo")){
return "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg";
}

if(esporte.includes("futebol")){
return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
}

if(esporte.includes("nba")){
return "https://upload.wikimedia.org/wikipedia/en/0/03/National_Basketball_Association_logo.svg";
}

if(esporte.includes("nfl")){
return "https://upload.wikimedia.org/wikipedia/en/a/a2/National_Football_League_logo.svg";
}

if(esporte.includes("tenis")){
return "https://upload.wikimedia.org/wikipedia/commons/3/3e/Tennis_Racket_and_Ball.svg";
}

return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";

}

fetch("eventos.json")
.then(response => response.json())
.then(data => {

eventosGlobais = data;

mostrarEventoDoDia();
mostrarEventos("todos");

});

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
<img src="${logo}" class="logo" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg'">
${evento.titulo}
</div>
<div class="hora">${evento.data}</div>
<div class="transmissao">📺 ${evento.transmissao}</div>
</div>
`;

}

function mostrarEventos(filtro){

let agenda = document.getElementById("agenda");
agenda.innerHTML = "";

let eventosFiltrados = eventosGlobais;

if(filtro !== "todos"){
eventosFiltrados = eventosGlobais.filter(evento =>
evento.esporte.toLowerCase() === filtro.toLowerCase()
);
}

if(eventosFiltrados.length === 0){
agenda.innerHTML = "<p>Nenhum evento encontrado.</p>";
return;
}

eventosFiltrados.sort((a,b)=>(a.prioridade||2)-(b.prioridade||2));

eventosFiltrados.forEach(evento => {

let logo = pegarLogo(evento);

let card = document.createElement("div");
card.className = "evento";

card.innerHTML = `
<div class="titulo">
<img src="${logo}" class="logo" onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg'">
${evento.titulo}
</div>
<div class="hora">${evento.data}</div>
<div class="transmissao">📺 ${evento.transmissao}</div>
`;

agenda.appendChild(card);

});

}

function filtrar(esporte){
mostrarEventos(esporte);
}
