let eventosGlobais = [];
let resultadosGlobais = [];
let filtroAtual = "todos";

function normalizar(texto){
  return (texto || "").toLowerCase().trim();
}

function normalizarEsporte(esporte){
  return normalizar(esporte || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function slugify(texto){
  return normalizar(texto)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function renderizarTransmissao(transmissao){
  if(!transmissao) return "<div class='transmissao'>📺 A confirmar</div>";

  let canais = transmissao.split("/").map(function(c){ return c.trim(); });
  let itens = [];

  canais.forEach(function(canal){
    let chave = canal.toLowerCase();
    let encontrou = false;
    for(let key in LOGOS_CANAIS){
      if(chave.includes(key)){
        itens.push(
          "<div class='logo-canal-popup'>" +
          "<img src='" + LOGOS_CANAIS[key] + "' onerror='this.style.display=\"none\"'>" +
          "<span>" + canal + "</span>" +
          "</div>"
        );
        encontrou = true;
        break;
      }
    }
    if(!encontrou){
      itens.push("<div class='logo-canal-popup'><span>" + canal + "</span></div>");
    }
  });

  return "<div class='transmissao-wrapper'>" +
    "<div class='transmissao transmissao-toggle'>📺 Transmiss\u00e3o</div>" +
    "<div class='transmissao-popup'>" + itens.join("") + "</div>" +
    "</div>";
}

const LOGOS_COMPETICAO = {
  "brasileirao": "assets/logos/competicoes/brasileirao.png",
  "copa do brasil": "assets/logos/competicoes/copa-do-brasil.png",
  "copa do mundo": "assets/logos/competicoes/copa-do-mundo.png",
  "libertadores": "assets/logos/competicoes/libertadores.png",
  "formula 1": "assets/logos/competicoes/formula1.png",
  "tenis": "assets/logos/competicoes/tenis.png",
  "monte carlo": "assets/logos/competicoes/tenis.png",
  "roland garros": "assets/logos/competicoes/tenis.png",
  "wimbledon": "assets/logos/competicoes/tenis.png",
  "us open": "assets/logos/competicoes/tenis.png",
  "madrid open": "assets/logos/competicoes/tenis.png",
  "italian open": "assets/logos/competicoes/tenis.png",
};



const LOGOS_CANAIS = {
  "globo": "assets/logos/canais/globo.png",
  "sportv": "assets/logos/canais/sportv.png",
  "sptv": "assets/logos/canais/sportv.png",
  "premiere": "assets/logos/canais/premiere.png",
  "amazon": "assets/logos/canais/primevideo.png",
  "prime video": "assets/logos/canais/primevideo.png",
  "primevideo": "assets/logos/canais/primevideo.png",
  "espn": "assets/logos/canais/espn.png",
  "disney": "assets/logos/canais/disney.png",
  "disney+": "assets/logos/canais/disney.png",
  "caztv": "assets/logos/canais/cazetv.png",
  "cazetv": "assets/logos/canais/cazetv.png",
  "caz": "assets/logos/canais/cazetv.png",
  "ge tv": "assets/logos/canais/getv.png",
  "getv": "assets/logos/canais/getv.png",
  "sbt": "assets/logos/canais/sbt.png",
  "paramount": "assets/logos/canais/paramount.png",
  "band": "assets/logos/canais/band.png",
  "bandsports": "assets/logos/canais/bandsports.png",
  "record": "assets/logos/canais/record.png",
  "rede record": "assets/logos/canais/record.png",
};

const LOGOS_TIMES = {
  "ca mineiro": "assets/logos/times/atletico-mg.png",
  "ca paranaense": "assets/logos/times/atletico-pr.png",
  "ec bahia": "assets/logos/times/bahia.png",
  "botafogo fr": "assets/logos/times/botafogo.png",
  "rb bragantino": "assets/logos/times/bragantino.png",
  "red bull bragantino": "assets/logos/times/bragantino.png",
  "chapecoense af": "assets/logos/times/chapecoense.png",
  "sc corinthians paulista": "assets/logos/times/corinthians.png",
  "coritiba fbc": "assets/logos/times/coritiba.png",
  "cruzeiro ec": "assets/logos/times/cruzeiro.png",
  "cr flamengo": "assets/logos/times/flamengo.png",
  "fluminense fc": "assets/logos/times/fluminense.png",
  "gremio fbpa": "assets/logos/times/gremio.png",
  "sc internacional": "assets/logos/times/internacional.png",
  "mirassol fc": "assets/logos/times/mirassol.png",
  "se palmeiras": "assets/logos/times/palmeiras.png",
  "clube do remo": "assets/logos/times/remo.png",
  "santos fc": "assets/logos/times/santos.png",
  "sao paulo fc": "assets/logos/times/sao-paulo.png",
  "cr vasco da gama": "assets/logos/times/vasco.png",
  "ec vitoria": "assets/logos/times/vitoria.png",
};

function pegarLogoTime(nomeTime){
  let n = normalizar(nomeTime || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  for(let key in LOGOS_TIMES){
    if(n === key) return LOGOS_TIMES[key];
  }
  return "";
}

function logoTimeHtml(nomeTime){
  let url = pegarLogoTime(nomeTime);
  if(!url) return "";
  return `<img src="${url}" class="logo-time" onerror="this.style.display='none'">`;
}

const NOMES_TIMES = {
  "ca mineiro": "Atletico-MG",
  "ca paranaense": "Athletico-PR",
  "ec bahia": "Bahia",
  "botafogo fr": "Botafogo",
  "rb bragantino": "Bragantino",
  "red bull bragantino": "Bragantino",
  "chapecoense af": "Chapecoense",
  "sc corinthians paulista": "Corinthians",
  "coritiba fbc": "Coritiba",
  "cruzeiro ec": "Cruzeiro",
  "cr flamengo": "Flamengo",
  "fluminense fc": "Fluminense",
  "gremio fbpa": "Gremio",
  "sc internacional": "Internacional",
  "juventude": "Juventude",
  "mirassol fc": "Mirassol",
  "se palmeiras": "Palmeiras",
  "clube do remo": "Remo",
  "santos fc": "Santos",
  "sao paulo fc": "Sao Paulo",
  "sport recife": "Sport",
  "cr vasco da gama": "Vasco",
  "ec vitoria": "Vitoria",
  "brazil": "🇧🇷 Brasil",
  "argentina": "🇦🇷 Argentina",
  "france": "🇫🇷 Franca",
  "england": "🏴󠁧󠁢 Inglaterra",
  "germany": "🇩🇪 Alemanha",
  "spain": "🇪🇸 Espanha",
  "portugal": "🇵🇹 Portugal",
  "netherlands": "🇳🇱 Holanda",
  "italy": "🇮🇹 Italia",
  "uruguay": "🇺🇾 Uruguai",
  "colombia": "🇨🇴 Colombia",
  "chile": "🇨🇱 Chile",
  "mexico": "🇲🇽 Mexico",
  "united states": "🇺🇸 EUA",
  "japan": "🇯🇵 Japao",
  "south korea": "🇰🇷 Coreia do Sul",
  "morocco": "🇲🇦 Marrocos",
  "senegal": "🇸🇳 Senegal",
  "australia": "🇦🇺 Australia",
  "ecuador": "🇪🇨 Equador",
  "peru": "🇵🇪 Peru",
  "venezuela": "🇻🇪 Venezuela",
  "bolivia": "🇧🇴 Bolivia",
  "paraguay": "🇵🇾 Paraguai",
  "croatia": "🇭🇷 Croacia",
  "serbia": "🇷🇸 Serbia",
  "switzerland": "🇨🇭 Suica",
  "denmark": "🇩🇰 Dinamarca",
  "poland": "🇵🇱 Polonia",
  "cameroon": "🇨🇲 Camaroes",
  "nigeria": "🇳🇬 Nigeria",
  "ghana": "🇬🇭 Gana",
  "iran": "🇮🇷 Ira",
  "saudi arabia": "🇸🇦 Arabia Saudita",
  "costa rica": "🇨🇷 Costa Rica",
  "canada": "🇨🇦 Canada",
  "ca boca juniors": "Boca Juniors",
  "ca penarol": "Penarol",
  "club nacional de football": "Nacional",
  "ldu de quito": "LDU Quito",
  "estudiantes de la plata": "Estudiantes",
  "ca lanus": "Lanus",
  "ca rosario central": "Rosario Central",
  "ca platense": "Platense",
  "independiente santa fe": "Santa Fe",
  "cd independiente medellin": "Ind. Medellin",
  "cd tolima": "Tolima",
  "barcelona sc": "Barcelona SC",
  "car independiente del valle": "Ind. del Valle",
  "cs cristal": "Sporting Cristal",
  "club universitario de deportes": "Universitario",
  "cusco fc": "Cusco FC",
  "club alianza lima": "Alianza Lima",
  "club always ready": "Always Ready",
  "club bolivar": "Bolivar",
  "deportivo la guaira fc": "La Guaira",
  "cs independiente rivadavia": "Ind. Rivadavia",
  "cd universidad catolica": "U. Catolica",
  "cd coquimbo unido": "Coquimbo",
  "club cerro porteno": "Cerro Porteno",
  "club libertad asuncion": "Libertad",
  "club guarani": "Guarani",
  "juventud de las piedras": "Juventud",
  "carabobo fc": "Carabobo",
  "cd huachipato": "Huachipato",
  "ohiggins fc": "OHiggins",
  "aa argentinos juniors": "Argentinos Jr.",
  "deportivo tachira fc": "Dep. Tachira",
  "club the strongest": "The Strongest",
  "cdp junior fc": "Junior FC",
  "universidad central de venezuela fc": "U. Central Venezuela",
};

function normalizarNomeTime(nome){
  let n = normalizar(nome || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  return NOMES_TIMES[n] || nome;
}

const DIAS_SEMANA = [
  "Domingo", "Segunda-feira", "Terca-feira", "Quarta-feira",
  "Quinta-feira", "Sexta-feira", "Sabado"
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

function pegarHeaderCard(evento){
  let comp = evento.competicao || "";
  let rodada = evento.rodada;
  let c = normalizar(comp)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

  if(c === "brasileirao" && rodada){
    return "BRASILEIRAO 2026 - " + rodada + "\u00aa RODADA";
  }
  if(c === "libertadores" && rodada){
    return "LIBERTADORES 2026 - RODADA " + rodada;
  }
  if(c === "copa do mundo" && rodada){
    return "COPA DO MUNDO 2026 - " + rodada;
  }
  if(normalizar(evento.esporte) === "automobilismo" && rodada){
    return "FORMULA 1 2026 - GP " + rodada;
  }
  if(normalizarEsporte(evento.esporte) === "tenis"){
    let compNome = evento.competicao || "";
    let rodadaStr = evento.rodada ? " - " + evento.rodada : "";
    let cn = compNome.toLowerCase();
  
    let categoria = "TENIS";
    if(cn.includes("australian open")) categoria = "GRAND SLAM";
    else if(cn.includes("roland garros") || cn.includes("french open")) categoria = "GRAND SLAM";
    else if(cn.includes("wimbledon")) categoria = "GRAND SLAM";
    else if(cn.includes("us open")) categoria = "GRAND SLAM";
    else if(cn.includes("monte carlo") || cn.includes("madrid") || cn.includes("rome") ||
            cn.includes("canadian") || cn.includes("cincinnati") || cn.includes("shanghai") ||
            cn.includes("paris") || cn.includes("indian wells") || cn.includes("miami")) categoria = "ATP MASTERS 1000";

    return categoria + " - " + compNome.toUpperCase() + rodadaStr;
  }
  if(comp){
    return comp.toUpperCase();
  }
  return "";
}

function normalizarTitulo(titulo){
  return (titulo || "").replace(/ vs /gi, " x ");
}

function renderizarTituloJogo(evento, mostrarResultado){
  mostrarResultado = mostrarResultado || false;
  let mandante = evento.mandante || "";
  let visitante = evento.visitante || "";
  if(normalizarEsporte(evento.esporte) === "tenis"){
  let titulo = evento.titulo || "";
  let partes = titulo.split(" vs ");
  if(partes.length === 2){
    let p1 = partes[0].trim();
    let p2 = partes[1].trim();
    if(mostrarResultado && evento.resultado){
      let scores = evento.resultado.split("x").map(function(s){ return s.trim(); });
      if(scores.length === 2){
        return "<span class='time-nome'><span>" + p1 + "</span><span class='placar-numero'>" + scores[0] + "</span></span>" +
               "<span class='placar-sep'>x</span>" +
               "<span class='time-nome'><span class='placar-numero'>" + scores[1] + "</span><span>" + p2 + "</span></span>";
      }
    }
    return "<span class='time-nome'><span>" + p1 + "</span></span>" +
           "<span class='placar-sep'>x</span>" +
           "<span class='time-nome'><span>" + p2 + "</span></span>";
  }
  return normalizarTitulo(titulo);
  }
  if(!mandante || !visitante){
    return normalizarTitulo(evento.titulo || "");
  }
  let nomeMandante = normalizarNomeTime(mandante);
  let nomeVisitante = normalizarNomeTime(visitante);
  let scoreMandante = "";
  let scoreVisitante = "";
  if(mostrarResultado && evento.resultado){
    let partes = evento.resultado.split("x").map(function(s){ return s.trim(); });
    if(partes.length === 2){
      scoreMandante = partes[0];
      scoreVisitante = partes[1];
    }
  }
  if(normalizar(evento.esporte) === "futebol"){
    if(scoreMandante !== "" && scoreVisitante !== ""){
      return "<span class='time-nome'>" +
        logoTimeHtml(mandante) +
        "<span>" + nomeMandante + "</span>" +
        "<span class='placar-numero'>" + scoreMandante + "</span>" +
        "</span>" +
        "<span class='placar-sep'>x</span>" +
        "<span class='time-nome'>" +
        "<span class='placar-numero'>" + scoreVisitante + "</span>" +
        "<span>" + nomeVisitante + "</span>" +
        logoTimeHtml(visitante) +
        "</span>";
    }
    return "<span class='time-nome'>" +
      logoTimeHtml(mandante) +
      "<span>" + nomeMandante + "</span>" +
      "</span>" +
      "<span class='placar-sep'>x</span>" +
      "<span class='time-nome'>" +
      "<span>" + nomeVisitante + "</span>" +
      logoTimeHtml(visitante) +
      "</span>";
  }
  if(scoreMandante !== "" && scoreVisitante !== ""){
    return "<span class='time-nome'><span>" + nomeMandante + "</span></span>" +
           "<span class='placar-sep'>x</span>" +
           "<span class='time-nome'><span>" + nomeVisitante + "</span></span>";
  }
  return "<span class='time-nome'><span>" + nomeMandante + "</span></span>" +
         "<span class='placar-sep'>x</span>" +
         "<span class='time-nome'><span>" + nomeVisitante + "</span></span>";
  }

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
  if(t.includes("joao fonseca") || t.includes("fonseca")) return 1;
  if(t.includes("brazil") || t.includes("brasil")) return 1;
  return e.prioridade || 999;
}

function linhaDataHora(e){
  let dia = diaSemana(e.data_ordem);
  let data = e.data || "";
  let hora = e.hora || "";
  let linhaData = dia && data ? dia + ", " + data : data;
  if(linhaData && hora) return linhaData + " - " + hora;
  if(linhaData) return linhaData;
  if(hora) return hora;
  return "";
}

function ordenar(lista){
  return lista.slice().sort(function(a, b){
    let pa = destaque(a);
    let pb = destaque(b);
    if(pa !== pb) return pa - pb;
    return (a.data_ordem || "").localeCompare(b.data_ordem || "");
  });
}

function filtrarEventosBase(lista, filtro){
  let base = lista.filter(function(e){ return !isDiagnostico(e); });
  if(filtro === "todos") return base;
  return base.filter(function(e){ 
    let esporte = normalizar(e.esporte)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
    return esporte === filtro; 
  });
}

function pegarLogoCompeticao(competicao){
  let c = normalizar(competicao || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  for(let key in LOGOS_COMPETICAO){
    if(c.includes(key)) return LOGOS_COMPETICAO[key];
  }
  return "";
}

function criarCardEvento(e, mostrarResultado){
  mostrarResultado = mostrarResultado || false;
  let el = document.createElement("div");
  el.className = "evento";
  
  if(e._statusCard){
  el.classList.add("evento-status-torneio");
  let watermarkUrl = pegarLogoCompeticao(e.competicao);
  let watermarkHtml = watermarkUrl
    ? "<img src='" + watermarkUrl + "' class='logo-watermark' onerror='this.style.display=\"none\"'>"
    : "";
  let header = pegarHeaderCard(e);
  let headerHtml = header
    ? "<div class='card-header'>" + header + "</div>"
    : "";
  el.innerHTML =
    watermarkHtml +
    headerHtml +
    "<div class='titulo' style='color:#e11d48'>" + e.titulo + "</div>" +
    "<div class='transmissao' style='margin-top:8px'>📺 " + (e.transmissao || "ESPN / Disney+") + "</div>";
  return el;
}
  
  if(destaque(e) === 1){
    el.classList.add("evento-destaque");
  }

  let watermarkUrl = pegarLogoCompeticao(e.competicao);
  let watermarkHtml = watermarkUrl
    ? "<img src='" + watermarkUrl + "' class='logo-watermark' onerror='this.style.display=\"none\"'>"
    : "";

  let header = pegarHeaderCard(e);
  let headerHtml = header
    ? "<div class='card-header'>" + header + "</div>"
    : "";

  let tituloJogo = renderizarTituloJogo(e, mostrarResultado);

  let estadioHtml = "";
  if(e.estadio){
    let local = e.estadio;
    if(e.cidade && e.uf){
      local += " - " + e.cidade + "/" + e.uf;
    }
    estadioHtml = "<div class='transmissao'>📍 " + local + "</div>";
  }

  el.innerHTML =
    watermarkHtml +
    headerHtml +
    "<div class='titulo'>" + tituloJogo + "</div>" +
    "<div class='hora'>" + linhaDataHora(e) + "</div>" +
    estadioHtml +
   renderizarTransmissao(e.transmissao, slugify((e.titulo || "") + (e.data_ordem || "")))

  return el;
}

function formatarNomeCompeticao(nome){
  let n = nome.toLowerCase();
  if(n.includes("monte carlo") || n.includes("madrid") || n.includes("rome") ||
     n.includes("canadian") || n.includes("cincinnati") || n.includes("shanghai") ||
     n.includes("paris masters") || n.includes("indian wells") || n.includes("miami")){
    return "ATP Masters 1000 - " + nome;
  }
  if(n.includes("australian open") || n.includes("roland garros") ||
     n.includes("wimbledon") || n.includes("us open") || n.includes("french open")){
    return "Grand Slam - " + nome;
  }
  return nome;
}

function criarBlocoCompeticao(nome, eventos, mostrarResultado, prefixo){
  mostrarResultado = mostrarResultado || false;
  prefixo = prefixo || "";
  if(eventos.length === 0) return null;
  let grupoId = prefixo + "grupo-" + slugify(nome);
  let bloco = document.createElement("div");
  bloco.className = "bloco-competicao";
  let titulo = document.createElement("h3");
  titulo.className = "titulo-competicao";
  titulo.style.cursor = "pointer";
  titulo.innerText = "▼ " + formatarNomeCompeticao(nome);
  titulo.onclick = function(){
    toggleGrupo(grupoId, titulo);
  };
  let divGrupo = document.createElement("div");
  divGrupo.id = grupoId;
  divGrupo.className = "grupo";
  ordenar(eventos).forEach(function(e){
    divGrupo.appendChild(criarCardEvento(e, mostrarResultado));
  });
  bloco.appendChild(titulo);
  bloco.appendChild(divGrupo);
  return bloco;
}

function proximaRodadaDaCompeticao(eventos){
  // F1
  if(eventos.length > 0 && normalizarEsporte(eventos[0].esporte) === "automobilismo"){
    let futuros = eventos.filter(function(e){
      return e.status === "futuro" && typeof e.dias_ate === "number" && e.dias_ate >= 0;
    });
    if(futuros.length === 0) return [];
    let proximoRound = futuros.reduce(function(min, e){
      return e.dias_ate < min.dias_ate ? e : min;
    }, futuros[0]).rodada;
    return futuros.filter(function(e){ return e.rodada === proximoRound; });
  }

  // Tennis
  if(eventos.length > 0 && normalizarEsporte(eventos[0].esporte) === "tenis"){
    let futuros = eventos.filter(function(e){
      return e.status === "futuro" && typeof e.dias_ate === "number" && e.dias_ate >= 0;
    });
    let resultados = eventos.filter(function(e){
      return e.status === "resultado";
    });

    let rodadaAtual = "";
    if(resultados.length > 0){
      let maisRecente = resultados.reduce(function(max, e){
        return (e.data_ordem || "") > (max.data_ordem || "") ? e : max;
      }, resultados[0]);
      rodadaAtual = maisRecente.rodada || "";
    }

    let comp = eventos[0].competicao || "";
    let transmissao = eventos[0].transmissao || "ESPN / Disney+";
    let dataRef = futuros.length > 0 ? futuros[0] : eventos[0];

    let statusCard = {
      esporte: eventos[0].esporte,
      competicao: comp,
      titulo: rodadaAtual ? "Em andamento - " + rodadaAtual : "Em andamento",
      status: "futuro",
      resultado: null,
      transmissao: transmissao,
      destaque: false,
      rodada: rodadaAtual,
      data_ordem: dataRef.data_ordem || "",
      data: dataRef.data || "",
      hora: "",
      dias_ate: 0,
      mandante: null,
      visitante: null,
      estadio: null,
      cidade: null,
      uf: null,
      tipo: "evento",
      prioridade: 2,
      origem: comp,
      fonte: "status_card",
      _statusCard: true
    };

    let resultado = [statusCard];
    if(futuros.length > 0){
      resultado = resultado.concat(futuros.slice(0, 5));
    }
    return resultado;
  }

  // Football
  let futuros = eventos.filter(function(e){
    return e.status === "futuro" && typeof e.dias_ate === "number" && e.dias_ate >= 0;
  });
  if(futuros.length === 0) return [];
  let comRodada = futuros.filter(function(e){
    return e.rodada !== null && e.rodada !== undefined;
  });
  if(comRodada.length > 0){
    let minRodada = Math.min.apply(null, comRodada.map(function(e){ return e.rodada; }));
    return comRodada.filter(function(e){ return e.rodada === minRodada; });
  }
  let minDias = Math.min.apply(null, futuros.map(function(e){ return e.dias_ate; }));
  let prox = futuros.find(function(e){ return e.dias_ate === minDias; });
  let proximaData = prox && prox.data_ordem ? prox.data_ordem.slice(0, 10) : null;
  if(!proximaData) return futuros.slice(0, 5);
  return futuros.filter(function(e){
    if(!e.data_ordem) return false;
    return e.data_ordem.slice(0, 10) >= proximaData;
  }).slice(0, 10);
}

function ultimaRodadaDaCompeticao(eventos){
  if(eventos.length > 0 && normalizarEsporte(eventos[0].esporte) === "tenis"){
    let resultados = eventos.filter(function(e){
      return e.status === "resultado";
    });
    if(resultados.length === 0) return [];
    
    // Find most recent date
    let maisRecente = resultados.reduce(function(max, e){
      return (e.data_ordem || "") > (max.data_ordem || "") ? e : max;
    }, resultados[0]);
    
    let dataRecente = (maisRecente.data_ordem || "").slice(0, 10);
    
    // Return only results from the most recent day
    return resultados.filter(function(e){
      return (e.data_ordem || "").slice(0, 10) === dataRecente;
    });
  }
  if(eventos.length > 0 && normalizar(eventos[0].esporte) === "automobilismo"){
    let resultados = eventos.filter(function(e){ return e.status === "resultado"; });
    if(resultados.length === 0) return [];
    let ultimoRound = resultados.reduce(function(max, e){
      let ra = parseInt(e.rodada) || 0;
      let rb = parseInt(max.rodada) || 0;
      return ra > rb ? e : max;
    }, resultados[0]).rodada;
    return resultados.filter(function(e){ return e.rodada === ultimoRound; });
  }

  let resultados = eventos.filter(function(e){ return e.status === "resultado"; });
  if(resultados.length === 0) return [];

  let comRodada = resultados.filter(function(e){
    return e.rodada !== null && e.rodada !== undefined;
  });
  if(comRodada.length > 0){
    let maxRodada = Math.max.apply(null, comRodada.map(function(e){ return e.rodada; }));
    return comRodada.filter(function(e){ return e.rodada === maxRodada; });
  }

  return resultados.filter(function(e){
    return typeof e.dias_ate === "number" && e.dias_ate >= -3 && e.dias_ate <= 0;
  });
}

function renderHoje(){
  let container = document.getElementById("hoje");
  if(!container) return;
  container.innerHTML = "";

  let lista = filtrarEventosBase(eventosGlobais, filtroAtual).filter(function(e){ return isHoje(e); });
  lista = ordenar(lista);

  if(lista.length === 0){
    container.innerHTML = "<p>Nenhum evento hoje.</p>";
    return;
  }

  lista.forEach(function(e){ container.appendChild(criarCardEvento(e)); });
}

function renderProximosJogos(){
  let container = document.getElementById("proximos");
  if(!container) return;
  container.innerHTML = "";

  let base = filtrarEventosBase(eventosGlobais, filtroAtual).filter(function(e){ return !isHoje(e); });

let grupos = {};
base.forEach(function(e){
  let chave = e.competicao || e.origem || "Outros";
  if(!grupos[chave]) grupos[chave] = [];
  grupos[chave].push(e);
});

// For tennis — also add results so we know the current round
filtrarEventosBase(resultadosGlobais, filtroAtual)
  .filter(function(e){ return normalizarEsporte(e.esporte) === "tenis"; })
  .forEach(function(e){
    let chave = e.competicao || e.origem || "Outros";
    if(!grupos[chave]) grupos[chave] = [];
    grupos[chave].push(e);
  });

  let temConteudo = false;

  Object.keys(grupos).sort(function(a, b){
    let futurosA = grupos[a].filter(function(e){ return e.status === "futuro"; });
    let futurosB = grupos[b].filter(function(e){ return e.status === "futuro"; });
    let dataA = futurosA.length > 0 ? Math.min.apply(null, futurosA.map(function(e){ return e.dias_ate; })) : 999;
    let dataB = futurosB.length > 0 ? Math.min.apply(null, futurosB.map(function(e){ return e.dias_ate; })) : 999;
    return dataA - dataB;
  }).forEach(function(comp){
    let proximos = proximaRodadaDaCompeticao(grupos[comp]);
    if(proximos.length === 0) return;
    let bloco = criarBlocoCompeticao(comp, proximos, false, "prox-");
    if(bloco){
      container.appendChild(bloco);
      temConteudo = true;
    }
  });

  if(!temConteudo){
    container.innerHTML = "<p>Nenhum evento proximo.</p>";
  }
}

function renderResultados(){
  let container = document.getElementById("resultados");
  if(!container) return;
  container.innerHTML = "";

  let base = filtrarEventosBase(resultadosGlobais, filtroAtual);

  let grupos = {};
  base.forEach(function(e){
    let chave = e.competicao || e.origem || "Outros";
    if(!grupos[chave]) grupos[chave] = [];
    grupos[chave].push(e);
  });

  filtrarEventosBase(eventosGlobais, filtroAtual)
    .filter(function(e){ return e.status === "resultado"; })
    .forEach(function(e){
      let chave = e.competicao || e.origem || "Outros";
      if(!grupos[chave]) grupos[chave] = [];
      grupos[chave].push(e);
    });

  let temConteudo = false;

  Object.keys(grupos).sort(function(a, b){
    let ultimaA = grupos[a].filter(function(e){ return e.status === "resultado"; });
    let ultimaB = grupos[b].filter(function(e){ return e.status === "resultado"; });
    let dataA = ultimaA.length > 0 ? Math.max.apply(null, ultimaA.map(function(e){ return e.dias_ate || -999; })) : -999;
    let dataB = ultimaB.length > 0 ? Math.max.apply(null, ultimaB.map(function(e){ return e.dias_ate || -999; })) : -999;
    return dataB - dataA;
  }).forEach(function(comp){
    let ultimos = ultimaRodadaDaCompeticao(grupos[comp]);
    if(ultimos.length === 0) return;
    let bloco = criarBlocoCompeticao(comp, ultimos, true, "res-");
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
  let lista = eventosGlobais.concat(resultadosGlobais).filter(function(e){ return isDiagnostico(e); });
  let box = document.getElementById("diagnosticos");
  let secao = document.getElementById("diagnosticos-section");

  if(!box || !secao) return;
  box.innerHTML = "";

  if(lista.length === 0){
    secao.style.display = "none";
    return;
  }

  lista.forEach(function(e){
    let d = document.createElement("div");
    d.className = "evento";
    d.innerHTML = "<div class='titulo'>" + e.titulo + "</div><div class='transmissao'>Fonte: " + (e.origem || "diagnostico") + "</div>";
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
  document.querySelectorAll(".nav-item").forEach(function(btn){
    btn.classList.remove("ativo");
  });
  document.querySelectorAll(".nav-item[data-filtro='" + esporte + "']").forEach(function(btn){
    btn.classList.add("ativo");
  });
  renderizarTudo();
}

function toggleGrupo(grupoId, tituloEl){
  let el = document.getElementById(grupoId);
  if(!el) return;
  if(el.classList.contains("collapsed")){
    el.classList.remove("collapsed");
    tituloEl.innerText = tituloEl.innerText.replace("▶", "▼");
  } else {
    el.classList.add("collapsed");
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
  fetch("data/eventos.json?ts=" + Date.now()).then(function(r){ return r.json(); }),
  fetch("data/resultados.json?ts=" + Date.now()).then(function(r){ return r.json(); })
])
.then(function(results){
  eventosGlobais = Array.isArray(results[0]) ? results[0] : [];
  resultadosGlobais = Array.isArray(results[1]) ? results[1] : [];
  renderizarTudo();
})
.catch(function(error){
  console.error("Erro ao carregar dados:", error);
});
