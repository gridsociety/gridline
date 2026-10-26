# Schema di quadro con dati di dimensionamento — BTicino

Backend operativo **da export nativi**. L'agente usa TiSystem web per modellare,
calcolare e verificare; il server MCP Gridline prepara gli input, riconcilia gli
export e compone il fascicolo Documentor. Non è un API TiSystem, non effettua
login né dimensiona da solo dal linguaggio naturale.

Per architetture di impianto, esistente e integrazione BESS usare invece lo
**schema generale di integrazione** QElectroTech. Le due viste possono convivere
nella modalità `combined`, mantenendo modelli e verifiche separati.

## Requisiti e avvio

Python 3.12+, dipendenze `uv.lock`, Documentor/Chromium secondo
[installazione](../../docs/installation.md), browser con accesso personale a
[TiSystem](https://tisystem.bticino.it/). QET non serve al solo backend BTicino.
Nessun cookie, ticket, credenziale o profilo browser è gestito dal pacchetto.

```sh
uv sync --frozen
uv run --frozen gridline doctor --backend bticino --json
uv run --frozen gridline new /percorso/commessa --workflow equipment
uv run --frozen gridline mcp-config /percorso/commessa
```

`new` crea un workspace che richiede input, non uno schema progettato. Compilare
`source/bticino/cases/current/request.json` e `cover.json`, usando l'esempio
sintetico come struttura e sostituendo i dati di prova. Il progettista è un campo
del documento; nessun nome o timbro personale è preimpostato. Un timbro può
essere fornito esplicitamente nella commessa locale, ma non è richiesto.

L'adapter usa `source/bticino/docs/documentor.toml`; la mappa è anche in
`variables/backend.json`. `qa/`, `out/`, `notes/` e `published/` seguono il
contratto Gridline. Le commesse stanno fuori dal repository o in `workspaces/`
ignorata. Il pacchetto porta soltanto i template aziendali necessari.

## Acquisizione e contratto dei file

1. Dichiarare input, provenienza, ipotesi e valori mancanti in `request.json`.
   Distinguere MW/MWh BESS e kW AUX; la tenuta dipende dalla sorgente/impedenze.
2. Nell'applicazione creare una copia, impostare sorgente e topologia, rileggere
   i menu dopo il caricamento, eseguire **Calcolo** e **Verifica**. Salvare.
3. Esportare stampa tecnica PDF con legende, report dettagliato PDF, CSV e `.ti8`.
   Rileggere circuiti e note; archiviare gli originali immutabili nel caso.
4. Compilare `exports.json` secondo `schemas/exports.schema.json`: hash SHA-256
   dei quattro file, hash canonico `design` (funzione `model.digest`), mappa
   ID/quadro/numero linea/articolo, pagine zero-based e rilievi riconosciuti.
   L'hash lega i file, non dimostra da solo il corretto calcolo.
5. Copertina e note sono HTML/JSON. `engineering.json` può restare con `pages: []`
   per un fascicolo BT; per MT aggiungere solo simboli originali tracciati,
   cataloghi locali e hash in `sources/registry.json`. Verificare prima le
   disponibilità TiSystem; nessun simbolo elettrico generato dall'AI.

```sh
uv run --frozen gridline bticino-prepare /percorso/commessa
uv run --frozen gridline check /percorso/commessa
uv run --frozen gridline render /percorso/commessa --format A3 --format A4
uv run --frozen gridline bticino-smoke /percorso/commessa
```

`bticino-smoke` avvia realmente MCP STDIO, prepara, ispeziona, genera entrambi i
formati e verifica gli hash. Richiede gli export già acquisiti: non simula
TiSystem. I risultati restano `DRAFT`, verifica visiva `PENDING` e approvazione
elettrica `OPEN` finché non sono effettuati i riesami pertinenti.

Il server espone `health_check`, `create_workspace`, `prepare_case`,
`inspect_exports`, `build_document`, `verify_document`. Il confinamento usa
`BTICINO_ALLOWED_ROOTS` (separatore di sistema); senza impostazione usa la cartella
corrente. La configurazione non dimostra che il client sia già collegato.

## Importare il workflow locale corrente

Per un caso del precedente motore con `cases/...`, registro fonti e profili:

```sh
uv run --frozen gridline bticino-import /percorso/workflow-locale /percorso/nuova-commessa --request cases/demo/request.json
```

L'import verifica hash, circuito e geometria prima della copia. Copia soltanto
il caso e le dipendenze dichiarate, in una destinazione nuova. Non esegue codice
o template del progetto importato; usa il motore e i template del pacchetto.
Non carica nulla su GitHub né nel registro Documentor. Gli originali rimangono
inalterati. L'import può contenere dati privati: la destinazione è una commessa,
mai la cartella degli esempi pubblici.

## Consegna e limiti

Ordine: **copertina con fase/revisione → generale eventuale → legende → quadro
con tabella componenti → note**. Il cartiglio GS è unico. Il rettangolo tecnico
nativo viene riconosciuto e inserito con clipping vettoriale e scala uniforme.
I controlli confrontano operatori PDF, parole e tutta l'area tecnica a 144 dpi.
Un nuovo layout TiSystem non riconosciuto viene rifiutato: qualificare un nuovo
profilo, non abbassare i controlli o ricreare i simboli.

L'adapter attuale è qualificato sul layout TiSystem 8 / manuale R7 con due
legende e un unifilare AUX a quattro partenze. UI e catalogo web possono cambiare.
La differenza osservata fra Iz del disegno e Iz corretto nel report resta
visibile e deve essere dichiarata, senza alterare le celle native.

Gli screening numerici opzionali richiedono `research/design-basis.json` nel
formato del caso qualificato; non sono un motore universale di dimensionamento.
Selettività riportata dall'applicazione, curva completa, I²t, tempi, terra, RCD,
spunti, posa e verifica MT rimangono livelli di verifica distinti. Il `.ti8` è
un archivio proprietario cifrato: un hash o la lettura dell'indice ZIP non prova
la riapertura nell'applicazione.

[Roadmap costruttiva e 3D](../../docs/ROADMAP.md) ·
[Esempio sintetico](../../examples/bticino/README.md) ·
[Indicazioni UI](../../skills/grid-bticino/references/tisystem-ui.md)
