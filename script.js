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

let eventosFiltrados;

if(filtro === "todos"){
eventosFiltrados = eventosGlobais;
}else{
eventosFiltrados = eventosGlobais.filter(e => e.esporte === filtro);
}

eventosFiltrados.forEach(evento => {

agenda.innerHTML += `
<div class="evento">
<div class="titulo">${evento.titulo}</div>
<div class="hora">${evento.data}</div>
<div class="transmissao">📺 ${evento.transmissao}</div>
</div>
`;

});

}

function filtrar(esporte){
mostrarEventos(esporte);
}

