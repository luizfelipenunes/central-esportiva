let eventosGlobais = [];
let resultadosGlobais = [];
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

// =========================
// COMPETITION LOGOS (watermark)
// =========================

const LOGOS_COMPETICAO = {
  "brasileirão": "assets/logos/competicoes/brasileirao.png",
  "copa do brasil": "assets/logos/competicoes/copa-do-brasil.png",
  "copa do mundo": "assets/logos/competicoes/copa-do-mundo.png",
  "libertadores": "assets/logos/competicoes/libertadores.png",
  "formula 1": "assets/logos/competicoes/formula1.png",
  "tênis": "assets/logos/competicoes/tenis.png",
  "monte carlo": "assets/logos/competicoes/tenis.png",
  "roland garros": "assets/logos/competicoes/tenis.png",
  "wimbledon": "assets/logos/competicoes/tenis.png",
  "us open": "assets/logos/competicoes/tenis.png",
  "madrid open": "assets/logos/competicoes/tenis.png",
  "italian open": "assets/logos/competicoes/tenis.png",
};

function pegarLogoCompetição(competicao){
  let c = normalizar(competicao || "");
  for(let key in LOGOS_COMPETICAO){
    if(c.includes(key)) return LOGOS_COMPETICAO[key];
  }
  return "";
}

// =========================
// TEAM LOGOS
// =========================

const LOGOS_TIMES = {
  "ca mineiro": "assets/logos/times/atletico-mg.png",
  "atletico mineiro": "assets/logos/times/atletico-mg.png",
  "ca paranaense": "assets/logos/times/atletico-pr.png",
  "athletico paranaense": "assets/logos/times/atletico-pr.png",
  "ec bahia": "assets/logos/times/bahia.png",
  "botafogo fr": "assets/logos/times/botafogo.png",
  "rb bragantino": "assets/logos/times/bragantino.png",
  "red bull bragantino": "assets/logos/times/bragantino.png",
  "ceará": "assets/logos/times/ceara.png",
  "ceara": "assets/logos/times/ceara.png",
  "chapecoense af": "assets/logos/times/chapecoense.png",
  "sc corinthians": "assets/logos/times/corinthians.png",
  "corinthians": "assets/logos/times/corinthians.png",
  "coritiba fbc": "assets/logos/times/coritiba.png",
  "cruzeiro ec": "assets/logos/times/cruzeiro.png",
  "cr flamengo": "assets/logos/times/flamengo.png",
  "flamengo": "assets/logos/times/flamengo.png",
  "fluminense fc": "assets/logos/times/fluminense.png",
  "grêmio fbpa": "assets/logos/times/gremio.png",
  "gremio": "assets/logos/times/gremio.png",
  "sc internacional": "assets/logos/times/internacional.png",
  "mirassol fc": "assets/logos/times/mirassol.png",
  "se palmeiras": "assets/logos/times/palmeiras.png",
  "palmeiras": "assets/logos/times/palmeiras.png",
  "clube do remo": "assets/logos/times/remo.png",
  "santos fc": "assets/logos/times/santos.png",
  "são paulo fc": "assets/logos/times/sao-paulo.png",
  "sao paulo fc": "assets/logos/times/sao-paulo.png",
  "sport": "assets/logos/times/sport.png",
  "cr vasco da gama": "assets/logos/times/vasco.png",
  "vasco": "assets/logos/times/vasco.png",
  "ec vitória": "assets/logos/times/vitoria.png",
  "ec vitoria": "assets/logos/times/vitoria.png",
  "juventude": "assets/logos/times/juventude.png",
};

function pegarLogoTime(nomeTime){
  let n = normalizar(nomeTime || "");
  for(let key in LOGOS_TIMES){
    if(n.includes(normalizar(key))) return LOGOS_TIMES[key];
  }
  return "";
}

function logoTimeHtml(nomeTime){
  let url = pegarLogoTime(nomeTime);
  if(!url) return "";
  return `<img src="${url}" class="logo-time" onerror="this.style.display='none'">`;
}

// =========================
// WEEKDAY IN PORTUGUESE
// =========================

const DIAS_SEMANA = [
  "Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira",
  "Quinta-feira", "Sexta-feira", "Sábado"
];

function diaSemana(dataOrdem){
  if(!dataOrdem) return "";
  try {
    let dt = new Date(dataOrdem);
    return DIAS_SEMANA[dt.getDay()];
  } catch(e){
    return "";
  }
}

// =========================
// CARD HEADER TITLE
// =========================

function pegarHeaderCard(evento){
  let comp = evento.competicao || "";
  let rodada = evento.rodada;
  let c = normalizar(comp);

  if(c === "brasileirão" && rodada){
    return `BRASILEIRÃO 2026 — ${rodada}ª RODADA`;
  }
  if(c === "libertadores" && rodada){
    return `LIBERTADORES 2026 — RODADA ${rodada}`;
  }
  if(c === "copa do mundo" && rodada){
    return `COPA DO MUNDO 2026 — ${rodada}`;
  }
  if(normalizar(evento.esporte) === "automobilismo" && rodada){
    return `FORMULA 1 2026 — GP ${rodada}`;
  }
  if(comp){
    return comp.toUpperCase();
  }
  return "";
}

// =========================
// NORMALIZE TITLE
// =========================

function normalizarTitulo(titulo){
  return (titulo || "").replace(/ vs /gi, " x ");
}

function renderizarTimeComLogo(nomeTime){
  let logo = logoTimeHtml(nomeTime);
  return `${logo}<span>${nomeTime}</span>`;
}

function renderizarTituloJogo(evento){
  let mandante = evento.mandante || "";
  let visitante = evento.visitante || "";

  if(!mandante || !visitante){
    return normalizarTitulo(evento.titulo || "");
  }

  let nomeMandante = normalizarNomeTime(mandante);
  let nomeVisitante = normalizarNomeTime(visitante);

  if(normalizar(evento.esporte) === "futebol"){
    return `
      <span class="time-nome">
        ${logoTimeHtml(mandante)}
        <span>${nomeMandante}</span>
      </span>
      <span class="placar-sep">x</span>
      <span class="time-nome">
        ${logoTimeHtml(visitante)}
        <span>${nomeVisitante}</span>
      </span>
    `;
  }

  return `${nomeMandante} x ${nomeVisitante}`;
}

// =========================
// UTIL
// =========================

function isDiagnostico(e){
  return e.tipo === "diagnostico";
}

function isHoje(e){
  return e.dias_ate === 0;
}

function destaque(e){
  let t = normalizar(e.titulo);
  if(t.includes("vasco")) return 1;
  if(t.includes("celtics")) return 1;
  if(t.includes("seahawks")) return 1;
  if(t.includes("joão fonseca") || t.includes("joao fonseca")) return 1;
  if(t.includes("brazil") || t.includes("brasil")) return 1;
  return e.prioridade || 999;
}

function linhaDataHora(e){
  let dia = diaSemana(e.data_ordem);
  let data = e.data || "";
  let hora = e.hora || "";
  let linhaData = dia && data ? `${dia}, ${data}` : data;
  if(linhaData && hora) return `${linhaData} • ${hora}`;
  if(linhaData) return linhaData;
  if(hora) return hora;
  return "";
}

function ordenar(lista){
  return [...lista].sort((a, b) => {
    let pa = destaque(a);
    let pb = destaque(b);
    if(pa !== pb) return pa - pb;
    return (a.data_ordem || "").localeCompare(b.data_ordem || "");
  });
}

function filtrarEventosBase(lista, filtro){
  let base = lista.filter(e => !isDiagnostico(e));
  if(filtro === "todos") return base;
  return base.filter(e => normalizar(e.esporte) === filtro);
}

function criarCardEvento(e, mostrarResultado = false){
  let el = document.createElement("div");
  el.className = "evento";

  if(destaque(e) === 1){
    el.classList.add("evento-destaque");
  }

  // Watermark
  let watermarkUrl = pegarLogoCompetição(e.competicao);
  let watermarkHtml = watermarkUrl
    ? `<img src="${watermarkUrl}" class="logo-watermark" onerror="this.style.display='none'">`
    : "";

  // Card header
  let header = pegarHeaderCard(e);
  let headerHtml = header
    ? `<div class="card-header">${header}</div>`
    : "";

  // Match title with team logos
  let tituloJogo = renderizarTituloJogo(e);

  // Estadio
  let estadioHtml = "";
  if(e.estadio){
    let local = e.estadio;
    if(e.cidade && e.uf){
      local += ` • ${e.cidade}/${e.uf}`;
    }
    estadioHtml = `<div class="transmissao">📍 ${local}</div>`;
  }

  // Result
  let resultadoHtml = "";
  if(mostrarResultado && e.resultado){
    resultadoHtml = `<div class="hora">🏁 ${e.resultado}</div>`;
  }

  el.innerHTML = `
    ${watermarkHtml}
    ${headerHtml}
    <div class="titulo">${tituloJogo}</div>
    <div class="hora">${linhaDataHora(e)}</div>
    ${resultadoHtml}
    ${estadioHtml}
    <div class="transmissao">📺 ${e.transmissao || "A confirmar"}</div>
  `;

  return el;
}

function criarBlocoCompetição(nome, eventos, mostrarResultado = false){
  if(eventos.length === 0) return null;

  let grupoId = "grupo-" + slugify(nome);

  let bloco = document.createElement("div");
  bloco.className = "bloco-competicao";

  let titulo = document.createElement("h3");
  titulo.className = "titulo-competicao";
  titulo.style.cursor = "pointer";
  titulo.innerText = `▼ ${nome}`;
  titulo.onclick = function(){
    toggleGrupo(grupoId, titulo);
  };

  let divGrupo = document.createElement("div");
  divGrupo.id = grupoId;
  divGrupo.className = "grupo";

  ordenar(eventos).forEach(e => {
    divGrupo.appendChild(criarCardEvento(e, mostrarResultado));
  });

  bloco.appendChild(titulo);
  bloco.appendChild(divGrupo);
  return bloco;
}

// =========================
// NEXT ROUND LOGIC
// =========================

function proximaRodadaDaCompetição(eventos){
  if(eventos.length > 0 && normalizar(eventos[0].esporte) === "automobilismo"){
    let futuros = eventos.filter(e => e.status === "futuro" && typeof e.dias_ate === "number" && e.dias_ate >= 0);
    if(futuros.length === 0) return [];
    let proximoRound = futuros.reduce((min, e) => e.dias_ate < min.dias_ate ? e : min, futuros[0]).rodada;
    return futuros.filter(e => e.rodada === proximoRound);
  }

  let futuros = eventos.filter(e => e.status === "futuro" && typeof e.dias_ate === "number" && e.dias_ate >= 0);
  if(futuros.length === 0) return [];

  let comRodada = futuros.filter(e => e.rodada !== null && e.rodada !== undefined);
  if(comRodada.length > 0){
    let minRodada = Math.min(...comRodada.map(e => e.rodada));
    return comRodada.filter(e => e.rodada === minRodada);
  }

  let minDias = Math.min(...futuros.map(e => e.dias_ate));
  let proximaData = futuros.find(e => e.dias_ate === minDias)?.data_ordem?.slice(0, 10);
  if(!proximaData) return futuros.slice(0, 5);

  return futuros.filter(e => {
    if(!e.data_ordem) return false;
    return e.data_ordem.slice(0, 10) >= proximaData;
  }).slice(0, 10);
}

function ultimaRodadaDaCompetição(eventos){
  if(eventos.length > 0 && normalizar(eventos[0].esporte) === "automobilismo"){
    let resultados = eventos.filter(e => e.status === "resultado");
    if(resultados.length === 0) return [];
    let ultimoRound = resultados.reduce((max, e) => {
      let ra = parseInt(e.rodada) || 0;
      let rb = parseInt(max.rodada) || 0;
      return ra > rb ? e : max;
    }, resultados[0]).rodada;
    return resultados.filter(e => e.rodada === ultimoRound);
  }

  let resultados = eventos.filter(e => e.status === "resultado");
  if(resultados.length === 0) return [];

  let comRodada = resultados.filter(e => e.rodada !== null && e.rodada !== undefined);
  if(comRodada.length > 0){
    let maxRodada = Math.max(...comRodada.map(e => e.rodada));
    return comRodada.filter(e => e.rodada === maxRodada);
  }

  return resultados.filter(e => typeof e.dias_ate === "number" && e.dias_ate >= -3 && e.dias_ate <= 0);
}

// =========================
// RENDER FUNCTIONS
// =========================

function renderHoje(){
  let container = document.getElementById("hoje");
  if(!container) return;
  container.innerHTML = "";

  let lista = filtrarEventosBase(eventosGlobais, filtroAtual).filter(e => isHoje(e));
  lista = ordenar(lista);

  if(lista.length === 0){
    container.innerHTML = "<p>Nenhum evento hoje.</p>";
    return;
  }

  lista.forEach(e => container.appendChild(criarCardEvento(e)));
}

function renderProximosJogos(){
  let container = document.getElementById("proximos");
  if(!container) return;
  container.innerHTML = "";

  let base = filtrarEventosBase(eventosGlobais, filtroAtual).filter(e => !isHoje(e));

  let grupos = {};
  base.forEach(e => {
    let chave = e.competicao || e.origem || "Outros";
    if(!grupos[chave]) grupos[chave] = [];
    grupos[chave].push(e);
  });

  let temConteudo = false;

  Object.keys(grupos).sort((a, b) => {
    let futurosA = grupos[a].filter(e => e.status === "futuro");
    let futurosB = grupos[b].filter(e => e.status === "futuro");
    let dataA = futurosA.length > 0 ? Math.min(...futurosA.map(e => e.dias_ate)) : 999;
    let dataB = futurosB.length > 0 ? Math.min(...futurosB.map(e => e.dias_ate)) : 999;
    return dataA - dataB;
  }).forEach(comp => {
    let proximos = proximaRodadaDaCompetição(grupos[comp]);
    if(proximos.length === 0) return;

    let bloco = criarBlocoCompetição(comp, proximos, false);
    if(bloco){
      container.appendChild(bloco);
      temConteudo = true;
    }
  });

  if(!temConteudo){
    container.innerHTML = "<p>Nenhum evento próximo.</p>";
  }
}

function renderResultados(){
  let container = document.getElementById("resultados");
  if(!container) return;
  container.innerHTML = "";

  let base = filtrarEventosBase(resultadosGlobais, filtroAtual);

  let grupos = {};
  base.forEach(e => {
    let chave = e.competicao || e.origem || "Outros";
    if(!grupos[chave]) grupos[chave] = [];
    grupos[chave].push(e);
  });

  filtrarEventosBase(eventosGlobais, filtroAtual)
    .filter(e => e.status === "resultado")
    .forEach(e => {
      let chave = e.competicao || e.origem || "Outros";
      if(!grupos[chave]) grupos[chave] = [];
      grupos[chave].push(e);
    });

  let temConteudo = false;

  Object.keys(grupos).sort((a, b) => {
    let ultimaA = grupos[a].filter(e => e.status === "resultado");
    let ultimaB = grupos[b].filter(e => e.status === "resultado");
    let dataA = ultimaA.length > 0 ? Math.max(...ultimaA.map(e => e.dias_ate || -999)) : -999;
    let dataB = ultimaB.length > 0 ? Math.max(...ultimaB.map(e => e.dias_ate || -999)) : -999;
    return dataB - dataA;
  }).forEach(comp => {
    let ultimos = ultimaRodadaDaCompetição(grupos[comp]);
    if(ultimos.length === 0) return;

    let bloco = criarBlocoCompetição(comp, ultimos, true);
    if(bloco){
      container.appendChild(bloco);
      temConteudo = true;
    }
  });

  if(!temConteudo){
    container.innerHTML = "<p>Nenhum resultado recente.</p>";
  }
}

function renderDiagnostico(){
  let lista = [...eventosGlobais, ...resultadosGlobais].filter(e => isDiagnostico(e));
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
  renderProximosJogos();
  renderResultados();
  renderDiagnostico();
}

function filtrar(esporte){
  filtroAtual = esporte;
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.classList.remove("ativo");
  });
  document.querySelectorAll(`.nav-item[data-filtro="${esporte}"]`).forEach(btn => {
    btn.classList.add("ativo");
  });
  renderizarTudo();
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

function toggleDiagnostico(){
  let el = document.getElementById("diagnosticos-section");
  if(!el) return;
  if(el.style.display === "none"){
    el.style.display = "block";
  } else {
    el.style.display = "none";
  }
}

Promise.all([
  fetch("data/eventos.json?ts=" + Date.now()).then(r => r.json()),
  fetch("data/resultados.json?ts=" + Date.now()).then(r => r.json())
])
.then(([eventos, resultados]) => {
  eventosGlobais = Array.isArray(eventos) ? eventos : [];
  resultadosGlobais = Array.isArray(resultados) ? resultados : [];
  renderizarTudo();
})
.catch(error => {
  console.error("Erro ao carregar dados:", error);
});

const NOMES_TIMES = {
  // Atletico Mineiro
  "ca mineiro": "Atlético-MG",
  "atletico mineiro": "Atlético-MG",
  
  // Athletico Paranaense
  "ca paranaense": "Athletico-PR",
  "athletico paranaense": "Athletico-PR",
  
  // Bahia
  "ec bahia": "Bahia",
  
  // Botafogo
  "botafogo fr": "Botafogo",
  
  // Bragantino
  "rb bragantino": "Bragantino",
  "red bull bragantino": "Bragantino",
  
  // Ceará
  "ceará sc": "Ceará",
  "ceara sc": "Ceará",
  
  // Chapecoense
  "chapecoense af": "Chapecoense",
  
  // Corinthians
  "sc corinthians paulista": "Corinthians",
  
  // Coritiba
  "coritiba fbc": "Coritiba",
  
  // Cruzeiro
  "cruzeiro ec": "Cruzeiro",
  
  // Flamengo
  "cr flamengo": "Flamengo",
  
  // Fluminense
  "fluminense fc": "Fluminense",
  
  // Grêmio
  "grêmio fbpa": "Grêmio",
  "gremio fbpa": "Grêmio",
  
  // Internacional
  "sc internacional": "Internacional",
  
  // Juventude
  "juventude": "Juventude",
  
  // Mirassol
  "mirassol fc": "Mirassol",
  
  // Palmeiras
  "se palmeiras": "Palmeiras",
  
  // Remo
  "clube do remo": "Remo",
  
  // Santos
  "santos fc": "Santos",
  
  // São Paulo
  "são paulo fc": "São Paulo",
  "sao paulo fc": "São Paulo",
  
  // Sport
  "sport recife": "Sport",
  
  // Vasco
  "cr vasco da gama": "Vasco",
  
  // Vitória
  "ec vitória": "Vitória",
  "ec vitoria": "Vitória",

  // World Cup teams
  "brazil": "Brasil",
  "argentina": "Argentina",
  "france": "França",
  "england": "Inglaterra",
  "germany": "Alemanha",
  "spain": "Espanha",
  "portugal": "Portugal",
  "netherlands": "Holanda",
  "italy": "Itália",
  "uruguay": "Uruguai",
  "colombia": "Colômbia",
  "chile": "Chile",
  "mexico": "México",
  "united states": "EUA",
  "japan": "Japão",
  "south korea": "Coreia do Sul",
  "senegal": "Senegal",
  "morocco": "Marrocos",
  "nigeria": "Nigéria",
  "cameroon": "Camarões",
  "australia": "Austrália",
  "ecuador": "Equador",
  "peru": "Peru",
  "venezuela": "Venezuela",
  "bolivia": "Bolívia",
  "paraguay": "Paraguai",

  // Libertadores common teams
  "boca juniors": "Boca Juniors",
  "ca boca juniors": "Boca Juniors",
  "river plate": "River Plate",
  "ca river plate": "River Plate",
  "ca penarol": "Peñarol",
  "ca peñarol": "Peñarol",
  "club nacional": "Nacional",
  "club nacional de football": "Nacional",
  "ldu de quito": "LDU Quito",
  "estudiantes de la plata": "Estudiantes",
  "ca independiente": "Independiente",
  "ca huracan": "Huracán",
  "ca lanus": "Lanús",
  "ca lanús": "Lanús",
  "ca rosario central": "Rosario Central",
  "ca platense": "Platense",
  "independiente santa fe": "Santa Fe",
  "cd independiente medellin": "Ind. Medellín",
  "cd tolima": "Tolima",
  "barcelona sc": "Barcelona SC",
  "ldu": "LDU Quito",
  "car independiente del valle": "Ind. del Valle",
  "cs cristal": "Sporting Cristal",
  "club universitario de deportes": "Universitario",
  "cusco fc": "Cusco FC",
  "club alianza lima": "Alianza Lima",
  "club always ready": "Always Ready",
  "club bolivar": "Bolívar",
  "club bolívar": "Bolívar",
  "deportivo la guaira fc": "La Guaira",
  "cs independiente rivadavia": "Ind. Rivadavia",
  "universidad central de venezuela fc": "U. Central",
  "cd universidad catolica": "U. Católica",
  "cd coquimbo unido": "Coquimbo",
  "club cerro porteno": "Cerro Porteño",
  "club cerro porteño": "Cerro Porteño",
  "club libertad asuncion": "Libertad",
  "club guarani": "Guaraní",
  "club guaraní": "Guaraní",
  "juventud de las piedras": "Juventud",
  "2 de mayo": "2 de Mayo",
  "carabobo fc": "Carabobo",
  "cd huachipato": "Huachipato",
  "o'higgins fc": "O'Higgins",
  "liverpool fc": "Liverpool FC",
  "aa argentinos juniors": "Argentinos Jr.",
  "club nacional potosi": "Nacional Potosí",
  "club nacional potosí": "Nacional Potosí",
  "deportivo tachira fc": "Dep. Táchira",
  "deportivo táchira fc": "Dep. Táchira",
  "club the strongest": "The Strongest",
  "cdp junior fc": "Junior FC",
  "universidad catolica": "U. Católica Chile",
};

function normalizarNomeTime(nome){
  let n = normalizar(nome || "");
  return NOMES_TIMES[n] || nome;
}
