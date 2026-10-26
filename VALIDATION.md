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
| BTicino | Pianificato, nessuna prova di questa integrazione nel primo commit |

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
