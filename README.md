# Gridline · Grid Society

**Descrivi il circuito al tuo agente. Gridline gli fornisce metodo, strumenti e
standard per produrre un unifilare modificabile e il PDF aziendale.**

> «Leggi AGENTS.md e usa la skill grid-single-line. Parti dallo schema allegato,
> conserva l'esistente e inserisci un doppio montante cliente/BESS. Genera il
> QET editabile e il PDF Documentor; registra ipotesi e verifiche aperte.»

L'agente sceglie il percorso in base all'elaborato richiesto. QElectroTech conserva il disegno generale modificabile; TiSystem produce gli schemi di quadro con i dati tecnici nativi. Documentor compone i PDF aziendali. I controlli software non sostituiscono il riesame elettrico.

## Scegliere il tipo di elaborato

| Richiesta professionale | Percorso | Uso |
| --- | --- | --- |
| **Schema generale di integrazione** | QElectroTech · `general` | Architettura d'impianto, esistente, nuovo BESS, montanti e interfacce |
| **Schema di quadro con dati di dimensionamento** | BTicino · `equipment` | Componenti in colonna, cavi, portate, poteri d'interruzione e tarature da export TiSystem |
| **Fascicolo coordinato generale e quadri** | Entrambi · `combined` | Due viste della stessa commessa, con modelli e verifiche distinti |

Esempi di richiesta: «Genera lo schema generale per integrare il BESS nell'impianto esistente» oppure «Genera l'unifilare del quadro con specifiche dei prodotti, cavi, tarature, portate e poteri d'interruzione». Se servono entrambi, chiedere il fascicolo coordinato. L'agente esplicita la scelta prima di produrre gli elaborati; non converte automaticamente un QET in un calcolo TiSystem.

```sh
uv run --frozen gridline workflows
uv run --frozen gridline new /percorso/commessa --workflow equipment
uv run --frozen gridline new /percorso/fascicolo --workflow combined
```

Progettista e disegnatore sono dati della commessa. Nessun timbro personale è incluso o attribuito automaticamente ai colleghi.

## Per iniziare con un agente

Scarica questo repository o clonalo:

```sh
git clone https://github.com/gridsociety/gridline.git
cd gridline
```

Apri questa cartella nell'agente che usi e incolla:

> Leggi AGENTS.md e docs/installation.md. Verifica i requisiti con
> scripts/doctor.py. Riusa le installazioni funzionanti, indica esattamente
> cosa manca e configura il server MCP senza sovrascrivere gli altri server.
> Installa le dipendenze fissate, esegui la prova completa in una nuova cartella,
> controlla PDF e QET. Poi lavoriamo sulla mia commessa fuori dal repository.

La diagnosi preliminare funziona anche prima di installare le librerie:

```sh
python3 scripts/doctor.py --json
```

Per l'ambiente Python, con [uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
uv sync --frozen
uv run --frozen gridline doctor
uv run --frozen gridline smoke workspaces/first-run
```

**Documentor è una dipendenza aziendale privata.** Il repository Gridline è
pubblico, ma per installare Documentor serve l'accesso del collega al repository
`gridsociety/documentor`. Non occorre un account personale dell'autore.
Per il render locale non serve accedere al registro di pubblicazione.
La [guida di installazione](docs/installation.md) fissa la revisione e spiega
come installare Chromium e individuare i requisiti mancanti. QElectroTech è
un'applicazione separata e va installata sul computer.

## Cosa contiene

| Percorso | Responsabilità |
| --- | --- |
| `skills/gridline/` | Orientamento dell'agente e scelta dell'integrazione |
| `skills/grid-single-line/` | Metodo elettrico e grafico QElectroTech |
| `src/qelectrotech_mcp/` | Server MCP STDIO: simboli, fogli, apparecchi, collegamenti, BOM e validazione |
| `src/gridline/` | CLI, diagnosi, workspace, demo MCP e composizione Documentor |
| `src/gridline/resources/` | Catalogo con provenienza, logo e template per le tavole |
| `integrations/qelectrotech/` | Procedura e limiti dell'integrazione disponibile |
| `integrations/bticino/` | Workflow TiSystem, acquisizione nativa, MCP e Documentor |
| `src/gridline_bticino/`, `skills/grid-bticino/` | Adapter, MCP locale, profili e metodo BTicino |
| `examples/double-feeder/` | Richiesta e istruzioni per la demo sintetica |
| `tests/` | Regressioni del codice e del contratto di progetto |

```mermaid
flowchart LR
    R[Richiesta e allegati] --> A[Agente e skill]
    A --> Q[MCP QElectroTech]
    Q --> S[QET e viste]
    A --> B[BTicino TiSystem via browser]
    B --> N[MCP export nativi]
    N --> V[Viste e dati delle tavole]
    S --> V
    V --> D[Documentor]
    D --> P[PDF aziendale e verifiche]
```

## Comandi

```sh
uv run --frozen gridline integrations
uv run --frozen gridline new /percorso/commessa --backend qelectrotech
uv run --frozen gridline mcp-config /percorso/commessa --format toml
uv run --frozen gridline check /percorso/commessa
uv run --frozen gridline render /percorso/commessa
uv run --frozen gridline demo workspaces/demo --no-render
```

`new` crea un progetto vuoto, non un circuito progettato. `demo` costruisce
attraverso MCP un esempio fittizio a due partenze; senza `--no-render` produce
anche il PDF. `smoke` aggiunge il requisito dell'applicazione QET e della sua
libreria presenti. Le destinazioni devono essere nuove: non sovrascrive prove
o progetti esistenti. `render` richiede viste SVG/PDF e `drawing-set.json` coerenti
con il QET; non importa automaticamente modifiche manuali dal disegno.

Ogni commessa conserva `source/`, `inputs/`, `notes/`, `variables/`, `qa/`,
`out/` e `published/`. Generazione e pubblicazione sono passaggi distinti.

## Stato e contributi

Sono disponibili il percorso QElectroTech e l'adapter BTicino da export nativi.
Il MCP BTicino prepara, controlla e impagina i file; il calcolo e l'export avvengono
in TiSystem web autenticato. Il repository non contiene sessioni browser,
cataloghi OEM, export privati né timbri. L'esempio pubblico BTicino contiene
input sintetici; la demo reale è descritta in [VALIDATION.md](VALIDATION.md).

Il workspace combinato instrada i due backend e produce due consegne; la
riconciliazione tecnica resta esplicita. Dettagli costruttivi, viste fronte/lato,
guide DIN, morsettiere e 3D sono nella [roadmap](docs/ROADMAP.md), con criteri di
completamento. Non sono funzionalità già disponibili.

- [Installazione e requisiti](docs/installation.md)
- [Uso da un agente](docs/agent-workflow.md)
- [Architettura e contratto delle integrazioni](docs/architecture.md)
- [Uso e limiti BTicino](integrations/bticino/README.md)
- [Sviluppi futuri e criteri di completamento](docs/ROADMAP.md)
- [Contribuire e convenzioni dei commit](CONTRIBUTING.md)
- [Provenienza e licenze dei contenuti](NOTICE.md)

XML valido, PDF leggibile, resa nativa QET e validazione elettrica sono controlli
separati. Le verifiche automatiche non attestano dimensionamento, selettività,
tarature o conformità normativa.
