let eventosGlobais = [];

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

destaque.innerHTML = `
<div class="evento">
<div class="titulo">${evento.titulo}</div>
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

let card = document.createElement("div");
card.className = "evento";

card.innerHTML = `
<div class="titulo">${evento.titulo}</div>
<div class="hora">${evento.data}</div>
<div class="transmissao">📺 ${evento.transmissao}</div>
`;

agenda.appendChild(card);

});

}

function filtrar(esporte){
mostrarEventos(esporte);
}
