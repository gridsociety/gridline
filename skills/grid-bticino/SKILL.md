---
name: grid-bticino
description: Prepara schemi di quadro con dati di dimensionamento da export originali BTicino TiSystem, usando MCP Gridline e Documentor; preserva simboli, linee e tabelle native.
---

# Schema di quadro con dati di dimensionamento

Leggere AGENTS.md e integrations/bticino/README.md del checkout Gridline.
Per una vista generale dell'impianto o integrazione BESS usare il percorso QET;
per entrambe le viste usare `gridline new COMMESSA --workflow combined` e
riconciliare ID, potenze, origini/destinazioni e revisioni nei due sottoprogetti.
Non convertire implicitamente un modello nell'altro.

Separare dati confermati, ipotesi e punti aperti. Non scalare consumi ausiliari
né tenute al cortocircuito dai MW BESS. Compilare il contratto JSON, guidare il
browser TiSystem autenticato e rileggere i dati dopo i caricamenti asincroni.
Per le operazioni UI leggere [tisystem-ui.md](references/tisystem-ui.md).

Il MCP Gridline gestisce i file locali: prepare, inspect, build, verify.
Non controlla TiSystem e non verifica il login. Eseguire davvero il calcolo e
la verifica nell'applicazione, conservare PDF/CSV/report/ti8 originali e legarli
alla richiesta. Nessuna password o sessione browser nel repository.

Conservare il contenuto tecnico nativo: nessun ridisegno dei simboli o correzione
manuale delle tabelle. Per MT verificare prima TiSystem; utilizzare solo simboli
originali con fonte/pagina/rettangolo/terminali e hash. Il riconoscimento del
layout deve fallire se il formato non è qualificato.

Ordine: copertina preliminare/revisione, generale eventuale, legende, quadro e
dettagli componenti, note finali. Metadati nel solo cartiglio Grid Society.
Progettista e disegnatore appartengono alla commessa: non attribuire il documento
all'autore del software e non usare un timbro senza un asset fornito per quel
progetto. Il pacchetto non contiene timbri personali.

Eseguire `gridline bticino-smoke COMMESSA` dopo aver acquisito gli export; aprire
A3/A4 e registrare la verifica visiva. Non chiamare esecutivo un preliminare con
ipotesi. I controlli software, il calcolo nativo, la riapertura nell'applicazione
e l'approvazione del progettista sono stati distinti. Consultare docs/ROADMAP.md
prima di promettere carpenteria, posizionamento DIN o 3D: sono sviluppi futuri.
