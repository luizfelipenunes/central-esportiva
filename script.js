fetch("eventos.json")
.then(response => response.json())
.then(data => {

let agenda = document.getElementById("agenda");

let esportes = {};

data.forEach(evento => {

if(!esportes[evento.esporte]){
esportes[evento.esporte] = [];
}

esportes[evento.esporte].push(evento);

});

for(let esporte in esportes){

agenda.innerHTML += `<h2>${esporte}</h2>`;

esportes[esporte].forEach(evento => {

agenda.innerHTML += `
<div class="evento">
<div class="titulo">${evento.titulo}</div>
<div class="hora">${evento.data}</div>
<div class="transmissao">📺 ${evento.transmissao}</div>
</div>
`;

});

}

});
