# Validazione

Verifica del 26 ottobre 2026. Nessuna verifica software costituisce approvazione elettrica.

| Prova | Esito |
| --- | --- |
| Installazione da `uv.lock` in ambiente nuovo | Superata su macOS Intel, Python 3.13.12, uv 0.10.6 |
| Test automatici | 21 superati: isolamento percorsi, workspace, simboli, collegamenti, etichette, errore render e demo MCP reale |
| Build sdist e wheel | Superata; wheel installata in ambiente isolato e demo MCP eseguita fuori dal checkout |
| Diagnosi QET e Documentor | Superata nell'ambiente di prova |
| MCP STDIO → QET → SVG → Documentor | Superata: sei elementi, cinque conduttori, un PDF con numero di pagine e dimensioni controllati |
| PDF e anteprima | Ispezionati: due rami distinti, etichette, qualificatori, nodi, cornice e cartiglio leggibili |
| Resa nativa desktop QET | Non ispezionata visivamente in questa verifica |
| Riesame elettrico | Non applicabile come progetto: demo sintetica senza dimensionamento |
| CI macOS, Windows e Linux | 21 test e build superati su tutti e tre i runner; la CI non esegue QET desktop né Documentor privato |
| BTicino | Contributo implementato: vedere la validazione dedicata sotto |

La prova PDF usa un checkout pulito di Documentor al commit
`22e215a70209ca48aa3a94c9e9a63341b143aa49`, con il suo lock e Chromium 1187.
Non usa le modifiche non committate della workstation originale.

Comando di riproduzione dopo l'installazione:

```sh
uv run --frozen pytest -q
uv run --frozen gridline smoke workspaces/verification-new
```

Il [campione pubblicato](examples/double-feeder/README.md) contiene PDF, QET,
anteprima e hash. Le tracce automatiche includono percorsi macchina e restano
nel workspace locale, fuori dalla pubblicazione. Il report automatico della
demo distingue la prova STDIO da un collegamento alla sessione dell'agente.

Rimangono warning delle dipendenze Pydantic e PyMuPDF nella suite; i test
funzionali passano. Non sono stati eseguiti test di tutti i simboli della
collezione QET né di ogni famiglia di primitive del renderer. L'anteprima
MCP resta approssimativa e va verificata per ciascuna commessa.

CI del codice verificato: [run 40354647060](https://github.com/gridsociety/gridline/actions/runs/40354647060), commit `38a46fe`.


## Contributo BTicino e selezione dei workflow — 26/10/2026

| Prova | Esito |
| --- | --- |
| Suite locale dopo riallineamento a main `72187a3` | 38 test superati: QET, adapter BTicino, numerica indipendente, confinamento/symlink, contesti isolati, MCP reale e modalità combinata |
| Regressione QET | Demo MCP a due partenze eseguita dopo l'integrazione; nessuna modifica al server QET |
| Caso reale TiSystem | Tre batterie 2,5 MW/5 MWh, quattro AUX e MT: export nativi di un dimostratore locale, non redistribuiti |
| MCP STDIO BTicino → Documentor | prepare, inspect, build A3/A4, verify eseguiti realmente; nessun mock del renderer o API TiSystem dichiarato |
| Fascicoli | Due PDF di sei pagine; integrità operatori/parole/area tecnica verificata; tutte le pagine identiche pixel per pixel a 72 dpi all'esempio già revisionato |
| Packaging | sdist/wheel costruite; wheel installata in venv separata, workspace combinato e configurazioni dei due MCP provati fuori dal checkout |
| Diagnosi BTicino | Eseguita dall'ambiente installato; non richiede QET e non certifica l'autenticazione TiSystem |
| Modalità combinata | Instradamento, due MCP, isolamento e rifiuto dei modelli incompleti testati; coordinamento tecnico e impaginazione in un unico PDF non automatizzati |
| Identità e dati distribuiti | Progettista configurabile; nessun timbro, firma, cliente reale, export privato, catalogo OEM o sessione browser nel contributo |
| Riapertura `.ti8` | Non testata nel nuovo adapter; non dedotta dall'hash o dall'indice ZIP |
| Approvazione elettrica | OPEN: carichi AUX ipotizzati, limiti station/DC/MT dichiarati; i test software non promuovono la fase |

La prova BTicino è eseguita su macOS Intel, Python 3.13.12, con Documentor
aziendale disponibile sulla workstation. La revisione pulita Documentor citata
nella validazione QET non viene automaticamente attribuita a questa prova.
Windows/Linux: vedere la CI della PR per i test e il packaging; il rendering
Documentor e l'accesso TiSystem sui sistemi dei colleghi restano prove distinte.

Riproduzione dopo acquisizione degli originali nel proprio workspace:

```sh
uv sync --frozen
uv run --frozen pytest -q
uv run --frozen gridline bticino-smoke /percorso/commessa
uv build
```

Per offline usare `--offline` solo con dipendenze già in cache. Nessuna nuova
libreria Python è stata necessaria: l'aggiornamento degli entrypoint e del
packaging non cambia le risoluzioni di `uv.lock`.

La skill `grid-bticino` è validata strutturalmente. La roadmap costruttiva e
3D elenca lavoro futuro, non capacità certificate in questa consegna.
