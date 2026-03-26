let eventosGlobais = [];
let filtroAtual = "todos";

function normalizar(texto){
  return (texto || "").toLowerCase().trim();
}

function slugify(texto){
  return normalizar(texto)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function pegarLogo(evento){
  let t = normalizar(evento.titulo);
  let e = normalizar(evento.esporte);

  if(t.includes("vasco")){
    return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
  }

  if(t.includes("celtics") || e.includes("nba")){
    return "https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png";
  }

  if(t.includes("seahawks") || e.includes("nfl")){
    return "https://upload.wikimedia.org/wikipedia/commons/3/3a/American_football.svg";
  }

  if(e.includes("automobilismo")){
    return "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg";
  }

  if(e.includes("futebol")){
    return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
  }

  if(e.includes("tenis")){
    return "https://upload.wikimedia.org/wikipedia/commons/3/3e/Tennis_Racket_and_Ball.svg";
  }

  return "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg";
}

function isDiagnostico(e){
  return e.tipo === "diagnostico";
}

function isHoje(e){
  return e.dias_ate === 0;
}

function is7Dias(e){
  return typeof e.dias_ate === "number" && e.dias_ate >= 1 && e.dias_ate <= 7;
}

function is30Dias(e){
  return typeof e.dias_ate === "number" && e.dias_ate >= 8 && e.dias_ate <= 30;
}

function destaque(e){
  let t = normalizar(e.titulo);

  if(t.includes("vasco")) return 1;
  if(t.includes("celtics")) return 1;
  if(t.includes("seahawks")) return 1;

  return e.prioridade || 999;
}

function linhaDataHora(e){
  let data = e.data || "";
  let hora = e.hora || "";

  if(data && hora) return `${data} • ${hora}`;
  if(data) return data;
  if(hora) return hora;
  return "";
}

function ordenar(lista){
  return [...lista].sort((a, b) => {
    let pa = destaque(a);
    let pb = destaque(b);

    if(pa !== pb){
      return pa - pb;
    }

    return (a.data_ordem || "").localeCompare(b.data_ordem || "");
  });
}

function filtrarEventosBase(filtro){
  let base = eventosGlobais.filter(e => !isDiagnostico(e));

  if(filtro === "todos"){
    return base;
  }

  return base.filter(e => normalizar(e.esporte) === filtro);
}

function criarCardEvento(e){
  let logo = pegarLogo(e);

  let el = document.createElement("div");
  el.className = "evento";

  if(destaque(e) === 1){
    el.classList.add("evento-destaque");
  }

  el.innerHTML = `
    <div class="titulo">
      <img src="${logo}" class="logo" onerror="this.style.display='none'">
      ${e.titulo}
    </div>
    <div class="hora">${linhaDataHora(e)}</div>
    <div class="transmissao">📺 ${e.transmissao || "A confirmar"}</div>
    <div class="transmissao">${e.origem || ""}</div>
  `;

  return el;
}

function renderHoje(){
  let container = document.getElementById("hoje");
  if(!container) return;

  container.innerHTML = "";

  let lista = filtrarEventosBase(filtroAtual).filter(e => isHoje(e));
  lista = ordenar(lista);

  if(lista.length === 0){
    container.innerHTML = "<p>Nenhum evento hoje.</p>";
    return;
  }

  lista.forEach(e => container.appendChild(criarCardEvento(e)));
}

function render7Dias(){
  let container = document.getElementById("agenda");
  if(!container) return;

  container.innerHTML = "";

  let lista = filtrarEventosBase(filtroAtual).filter(e => is7Dias(e));
  lista = ordenar(lista);

  if(lista.length === 0){
    container.innerHTML = "<p>Nenhum evento nos próximos 7 dias.</p>";
    return;
  }

  lista.forEach(e => container.appendChild(criarCardEvento(e)));
}

function render30Dias(){
  let container = document.getElementById("agenda-30");
  if(!container) return;

  container.innerHTML = "";

  let lista = filtrarEventosBase(filtroAtual).filter(e => is30Dias(e));
  lista = ordenar(lista);

  if(lista.length === 0){
    container.innerHTML = "<p>Nenhum evento entre 8 e 30 dias.</p>";
    return;
  }

  let grupos = {};

  lista.forEach(e => {
    let chave = e.origem || "Outros";
    if(!grupos[chave]){
      grupos[chave] = [];
    }
    grupos[chave].push(e);
  });

  Object.keys(grupos).sort((a, b) => {
    let primeiroA = ordenar(grupos[a])[0];
    let primeiroB = ordenar(grupos[b])[0];
    let dataA = primeiroA?.data_ordem || "9999-99-99T99:99:99";
    let dataB = primeiroB?.data_ordem || "9999-99-99T99:99:99";
    return dataA.localeCompare(dataB);
  }).forEach(comp => {
    let grupoId = "grupo-" + slugify(comp);

    let bloco = document.createElement("div");
    bloco.className = "bloco-competicao";

    let titulo = document.createElement("h3");
    titulo.className = "titulo-competicao";
    titulo.style.cursor = "pointer";
    titulo.innerText = `▼ ${comp}`;
    titulo.onclick = function(){
      toggleGrupo(grupoId, titulo);
    };

    let divGrupo = document.createElement("div");
    divGrupo.id = grupoId;
    divGrupo.className = "grupo";

    ordenar(grupos[comp]).forEach(e => {
      divGrupo.appendChild(criarCardEvento(e));
    });

    bloco.appendChild(titulo);
    bloco.appendChild(divGrupo);
    container.appendChild(bloco);
  });
}

function toggleGrupo(grupoId, tituloEl){
  let el = document.getElementById(grupoId);
  if(!el) return;

  if(el.style.display === "none"){
    el.style.display = "block";
    tituloEl.innerText = tituloEl.innerText.replace("▶", "▼");
  } else {
    el.style.display = "none";
    tituloEl.innerText = tituloEl.innerText.replace("▼", "▶");
  }
}

function renderDiagnostico(){
  let lista = eventosGlobais.filter(e => isDiagnostico(e));
  let box = document.getElementById("diagnosticos");
  let secao = document.getElementById("diagnosticos-section");

  if(!box || !secao) return;

  box.innerHTML = "";

  if(lista.length === 0){
    secao.style.display = "none";
    return;
  }

  lista.forEach(e => {
    let d = document.createElement("div");
    d.className = "evento";
    d.innerHTML = `
      <div class="titulo">${e.titulo}</div>
      <div class="transmissao">Fonte: ${e.origem || "diagnostico"}</div>
    `;
    box.appendChild(d);
  });
}

function renderizarTudo(){
  renderHoje();
  render7Dias();
  render30Dias();
  renderDiagnostico();
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

function toggleDiagnostico(){
  let el = document.getElementById("diagnosticos-section");
  if(!el) return;

  if(el.style.display === "none"){
    el.style.display = "block";
  } else {
    el.style.display = "none";
  }
}

fetch("eventos.json?ts=" + Date.now())
.then(r => r.json())
.then(data => {
  eventosGlobais = Array.isArray(data) ? data : [];
  renderizarTudo();
})
.catch(error => {
  console.error("Erro ao carregar eventos:", error);
});
