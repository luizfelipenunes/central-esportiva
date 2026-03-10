let eventosGlobais = [];

function pegarLogo(titulo){

titulo = titulo.toLowerCase();

if(titulo.includes("vasco")){
return "https://upload.wikimedia.org/wikipedia/en/5/5b/CR_Vasco_da_Gama_logo.svg";
}

if(titulo.includes("celtics")){
return "https://upload.wikimedia.org/wikipedia/en/8/8f/Boston_Celtics.svg";
}

if(titulo.includes("seahawks")){
return "https://upload.wikimedia.org/wikipedia/en/8/8e/Seattle_Seahawks_logo.svg";
}

if(titulo.includes("f1")){
return "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg";
}

if(titulo.includes("motogp")){
return "https://upload.wikimedia.org/wikipedia/commons/7/77/Moto_Gp_logo.svg";
}

if(titulo.includes("indy")){
return "https://upload.wikimedia.org/wikipedia/commons/3/3e/IndyCar_Series_logo.svg";
}

if(titulo.includes("tenis")){
return "https://upload.wikimedia.org/wikipedia/commons/3/3e/Tennis_Racket_and_Ball.svg";
}

return "";

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

let logo = pegarLogo(evento.titulo);

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

let logo = pegarLogo(evento.titulo);

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
