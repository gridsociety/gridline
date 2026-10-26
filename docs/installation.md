# Installazione riproducibile

## Requisiti

| Requisito | Come verificarlo | Se manca |
| --- | --- | --- |
| Agente con file locali e MCP STDIO | Elenco tool della sessione | Configurare un client MCP compatibile; leggere i file SKILL.md anche senza installazione automatica |
| Python 3.12+ e uv | `python3 --version`, `uv --version` | Installare Python/uv; ambiente di riferimento Python 3.13 |
| Dipendenze Gridline | `uv run --frozen gridline doctor` | `uv sync --frozen` |
| QElectroTech desktop e collezione | `gridline doctor`, MCP `health_check` | Installer ufficiale: https://qelectrotech.org/download.html |
| Documentor aziendale | `documentor doctor` | Installazione fissata sotto; accesso GitHub aziendale necessario |
| Chromium per Documentor | `documentor doctor` | `documentor install-browser` con il suo ambiente Python |

Il doctor non installa software né cambia configurazioni. Produce rimedi leggibili
anche in JSON. Se fallisce l'accesso a Documentor, riportare il repository e il
permesso mancante; non richiedere password in chat e non usare un renderer alternativo.

## Gridline

Da un clone o ZIP estratto, con terminale nella radice:

```sh
uv sync --frozen
uv run --frozen gridline doctor --json
```

Il lock è versionato. I comandi usano l'ambiente `.venv`; non installano pacchetti
nel Python globale. Su Windows gli stessi comandi `uv` funzionano in PowerShell.
La prova su un sistema operativo diverso da quello riportato in VALIDATION.md
resta da eseguire, anche quando il rilevamento trova gli strumenti.

## Documentor: installazione separata e fissata

Il collega deve poter leggere `gridsociety/documentor`. Scegli una cartella nuova
accanto a Gridline; non sostituire un checkout esistente con modifiche.

```sh
git clone https://github.com/gridsociety/documentor.git documentor-gridline
git -C documentor-gridline checkout --detach 22e215a70209ca48aa3a94c9e9a63341b143aa49
cd documentor-gridline
uv sync --frozen
uv run --frozen documentor install-browser
uv run --frozen documentor doctor
```

Gridline può usare direttamente l'eseguibile di questo ambiente, senza
installazioni globali. Tornando alla cartella Gridline, su macOS/Linux:

```sh
export GRIDLINE_DOCUMENTOR="/percorso/documentor-gridline/.venv/bin/documentor"
uv run --frozen gridline doctor
```

Su PowerShell:

```powershell
$env:GRIDLINE_DOCUMENTOR = 'C:\percorso\documentor-gridline\.venv\Scripts\documentor.exe'
uv run --frozen gridline doctor
```

Se Documentor è già funzionante nel PATH, Gridline lo riusa. Per riprodurre la
validazione di questa release usare la revisione sopra. Differenze fra versioni
richiedono una nuova prova completa. Il servizio di pubblicazione Documentor,
PostgreSQL e S3 non sono necessari per generare il PDF locale.

Il template delle tavole, la cornice e il logo necessari sono inclusi con
provenienza: non serve scaricare tutto il repository privato document-templates.

## Individuazione QElectroTech

Rilevamento: applicazioni macOS, PATH e percorsi comuni Windows/Linux.
Per installazioni portabili o non standard impostare:

- `QET_BINARY`: file eseguibile QElectroTech.
- `QET_ELEMENTS_ROOT`: cartella della collezione `elements`.
- `QET_TITLEBLOCKS_ROOT`: cartella `titleblocks`, facoltativa per Gridline.

Impostare queste variabili prima di generare la configurazione MCP. Il server
le legge all'avvio: dopo un cambio riavviare soltanto il server interessato.
La piccola collezione inclusa rende la demo riproducibile; per progetti reali
l'agente cerca anche nella collezione completa installata e verifica i simboli.

## Collegare l'agente

Per un client che usa JSON MCP:

```sh
uv run --frozen gridline mcp-config /percorso/commessa
```

Per un client che usa TOML:

```sh
uv run --frozen gridline mcp-config /percorso/commessa --format toml
```

Il comando stampa una configurazione con l'interprete della venv e radice
autorizzata della commessa. Copiare/inserire solo la nuova voce, rispettando
il formato previsto dal proprio client. Non sostituire tutta la configurazione.
Ricaricare la sessione se necessario, poi chiamare davvero `health_check`.
Le radici aggiuntive in `QET_ALLOWED_ROOTS` sono separate da `:` su Unix e `;`
su Windows. Il server senza configurazione limita i file alla directory corrente.

Leggere `skills/gridline/SKILL.md` e `skills/grid-single-line/SKILL.md` direttamente,
oppure copiarne le directory nella posizione di skill prevista dal client.
La documentazione rimane nel checkout: specificarne il percorso all'agente.

## Prova completa

```sh
uv run --frozen gridline smoke workspaces/first-run
```

Il comando avvia un server MCP STDIO nuovo, genera e valida un QET non vuoto,
esporta la vista, invoca Documentor e controlla producer, pagine e dimensioni.
Salva traccia MCP, PDF, PNG, distinta, hash e `qa/environment-readiness.json`.
Il risultato automatico è `pending_visual_review`: aprire il PNG/PDF e il QET
desktop, registrando cosa è stato controllato. La prova STDIO non dimostra che
il server sia già connesso alla sessione dell'agente: verificarlo anche lì.

Errori di porte locali o avvio Chromium dipendono dai permessi dell'ambiente:
autorizzare l'esecuzione locale quando consentito. Non modificare le protezioni
globali della macchina. Su Linux può essere necessario installare le dipendenze
di sistema richieste da Playwright; riportare il messaggio effettivo.
