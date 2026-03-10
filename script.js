fetch("eventos.json")
.then(response => response.json())
.then(data => {

let agenda = document.getElementById("agenda");

data.forEach(evento => {

agenda.innerHTML += `
<div class="evento">
<div class="titulo">${evento.titulo}</div>
<div class="hora">${evento.data}</div>
<div class="transmissao">📺 ${evento.transmissao}</div>
</div>
`;

});

});
