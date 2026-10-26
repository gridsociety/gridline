# Architettura e contratto delle integrazioni

Gridline coordina agenti, strumenti CAD e impaginazione. L'interpretazione della
richiesta è dell'agente; non c'è un parser deterministico del linguaggio naturale.

## Confini

1. **Agente e skill:** ricostruiscono circuito, fonti, stati e scelte; guidano i tool.
2. **Integrazione:** possiede il suo formato nativo e le operazioni MCP. QET usa
   XML editabile con definizioni incorporate. BTicino conserva il proprio
   progetto e gli export effettivamente ottenuti dall'applicazione.
3. **Consegna comune:** dati della commessa, sorgenti, viste, verifiche e provenienza.
4. **Documentor:** genera il PDF con il cartiglio aziendale; nessun backend
   introduce un renderer PDF alternativo per le consegne.

Non imponiamo uno schema elettrico universale prima di aver verificato entrambi
i backend. Un backend può avere un manifest JSON/YAML ricco e produrre la sua
distinta; un altro può usare direttamente il file QET. Il contratto comune è
quello della consegna e delle verifiche, non l'uguaglianza dei formati interni.

## Cartella della commessa

```text
gridline.json                 # schema_version, backend, gridline_version
inputs/                       # fonti originali e provenienza
source/                       # progetto nativo e modello del backend
notes/                        # context, decisions, status, attachments
variables/drawing-set.json    # viste del compositore QET, quando utilizzato
documentor.toml               # workspace Documentor
templates/ + static/          # template e viste, provenienze tracciate
qa/                          # test, controlli visivi, punti aperti, hash
out/                         # elaborati generati, log, distinta
published/                   # solo stati deliberatamente promossi
```

Il formato del `drawing-set.json` è il contratto del compositore storico QET:
metadati di documento e `pages[]` con `source`, `title`, `kind`, `variant`,
`width_mm`, `clip` opzionale e `source_page` zero-based per PDF.
Generali prima dei dettagli; viste senza un vecchio cartiglio incorporato.
Il compositore attuale richiede larghezza almeno 420 mm per il suo cartiglio.
BTicino può avere un adapter Documentor distinto per A4/A3 e colonne tecniche,
senza deformare le viste o forzare il contratto QET.

## Verifiche separabili

- validità strutturale del sorgente;
- conservazione del circuito e controllo delle modifiche;
- verifica numerica del backend, se disponibile, con assunzioni e ambito;
- generazione Documentor e corrispondenza delle pagine;
- controllo visivo degli elaborati;
- apertura e verifica nell'applicazione nativa;
- riesame elettrico del progettista.

Non promuovere un controllo nell'altro. Lo stato `planned` di una integrazione
deve rifiutare l'uso, non restituire un successo vuoto. Il manifest degli artefatti
riporta backend, stato DRAFT e hash dei file effettivamente prodotti.

## Estensioni

Il codice generico rimane in `src/gridline/`. Il server QET è in
`src/qelectrotech_mcp/`. Una seconda integrazione può aggiungere
`src/gridline_bticino/` e il suo entrypoint MCP, una skill dedicata e test isolati.
Dipendenze opzionali e strumenti browser restano specifici del backend.
Le interfacce comuni cambiano con un test di regressione per entrambi i percorsi.

## Percorsi attuali

`gridline workflows` espone general, equipment e combined. Il workspace combinato
contiene due sottoprogetti (`general/`, `quadri/`), due configurazioni MCP e un
`coordination.json` aperto. `check` visita entrambi; `render` richiede entrambi
completi e conserva due consegne. Non fonde i file nativi né deduce equivalenze.

BTicino usa `source/bticino/` per contratto del caso, profili e originali locali;
il workspace Documentor è `source/bticino/docs/`, indicato in
`variables/backend.json`. I PDF finali sono in `out/`, verifiche in `qa/`.
Il motore mantiene il contesto per chiamata e confina le risorse alla commessa.
Il server STDIO non emette log del renderer su stdout e non gestisce login.

Le risorse aziendali sono incluse con provenienza; PDF/cataloghi OEM sono
forniti localmente e non redistribuiti nel repository. Le pagine tecniche
restano PDF nativi con clipping e scala uniforme, mai SVG ricostruiti.
