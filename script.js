let eventosGlobais = [];

fetch("eventos.json")
.then(response => response.json())
.then(data => {

eventosGlobais = data;
mostrarEventos("todos");

});

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

