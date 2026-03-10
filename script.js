let eventosGlobais = [];

function pegarLogo(evento){

let titulo = evento.titulo.toLowerCase();
let esporte = evento.esporte.toLowerCase();

/* Logos específicos de times */

if(titulo.includes("vasco")){
return "https://crests.football-data.org/498.png";
}

if(titulo.includes("celtics")){
return "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png";
}

if(titulo.includes("seahawks")){
return "https://loodibee.com/wp-content/uploads/nfl-seattle-seahawks-team-logo.png";
}

/* Logos por categoria */

if(esporte.includes("automobilismo")){
return "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg";
}

if(esporte.includes("futebol")){
return "https://upload.wikimedia.org/wikipedia/commons/6/6e/Soccerball.svg";
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

/* fallback padrão */

return "https://upload.wikimedia.org/wikipedia/commons/6/6e/Soccerball.svg";

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
<img src="${logo}" class="logo">
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
<img src="${logo}" class="logo">
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
