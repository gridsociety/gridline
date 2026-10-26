# Secondo contributo: automazione BTicino

Destinazione: **https://github.com/gridsociety/gridline**.
Il primo commit introduce il percorso QElectroTech. Il secondo contributo
aggiunge l'automazione BTicino nello stesso programma, preservando il primo.

## Checkout e branch

Usare un clone separato dal checkout dell'altro agente:

```sh
git clone https://github.com/gridsociety/gridline.git gridline-bticino
cd gridline-bticino
git switch -c feat/bticino
```

Se il branch remoto esiste già, riprenderlo invece di ricrearlo. Leggere
AGENTS.md, CONTRIBUTING.md, docs/architecture.md e VALIDATION.md prima di copiare.

## Cartelle di competenza

| Contenuto | Destinazione |
| --- | --- |
| Automazione MCP e logica BTicino | `src/gridline_bticino/` |
| Procedura, capacità provate, limiti e dipendenze | `integrations/bticino/` |
| Istruzioni operative all'agente | `skills/grid-bticino/SKILL.md` e riferimenti |
| Esempio pubblico sintetico | `examples/bticino/` |
| Test specifici e fixture anonime | `tests/bticino/` |
| Template/asset specifici necessari | risorse del pacchetto BTicino con provenienza |

Non copiare l'intera cartella di lavoro storica: importare la versione corrente
e le dipendenze effettive. Conservare gli export nativi necessari a riprodurre
la demo, dopo aver rimosso dati cliente e verificato la redistribuzione.
Cookie, ticket, profili, HAR autenticati e credenziali restano fuori dal repo.
Non ridisegnare simboli vendor con QET per simulare un'integrazione nativa.

## Collegamento al programma

- Aggiungere l'entrypoint MCP e le dipendenze specifiche in `pyproject.toml`,
  preferibilmente come extra se non servono a QET; aggiornare `uv.lock`.
- Estendere la diagnosi con prerequisiti e rimedi BTicino: app/browser,
  autenticazione personale e connessione reale al server MCP.
- Registrare il backend come disponibile soltanto con una demo verificata.
  Non basta cambiare `planned` in `available`: `new`, invocazione e consegna
  devono instradare davvero l'implementazione BTicino.
- Riutilizzare il contratto di consegna comune. Per viste e dettagli per
  componente usare l'adapter Documentor appropriato: non forzare il compositore
  QET se il formato BTicino richiede un diverso layout.
- Documentare se il flusso parte dal prompt, automatizza l'applicazione,
  importa export manuali, o richiede passaggi umani. Non confondere questi stati.
- Conservare la leggibilità di AGENTS.md e dei README: aggiornare lo stato corrente,
  senza accodare più intestazioni “versione corrente” contraddittorie.

I file condivisi modificabili quando necessario sono `pyproject.toml`, `uv.lock`,
`src/gridline/cli.py`, diagnosi/registro backend, README, CHANGELOG e VALIDATION.
Non modificare `src/qelectrotech_mcp/` salvo un problema dimostrato da un test.

## Verifica e commit

```sh
uv sync --frozen
uv run --frozen pytest
uv run --frozen gridline demo workspaces/qet-regression --no-render
# Eseguire anche la demo BTicino reale, il render Documentor e il controllo visivo.
git diff --check
git status --short
# Aggiungere esplicitamente solo i file del contributo dopo revisione.
git commit -m "feat(bticino): add native single-line generation through MCP"
git push -u origin feat/bticino
```

Aprire una pull request verso `main` con titolo uguale al commit. Descrivere
il comportamento ottenuto, un comando riproducibile, test eseguiti e limiti
ancora aperti. Con merge squash il contributo diventa il secondo commit logico
su main. Non fare force-push e non usare il checkout attivo di un altro agente.

## Prompt pronto da inoltrare

> Integra l'automazione BTicino che abbiamo realizzato nel repository
> https://github.com/gridsociety/gridline. Usa un clone separato e il branch
> feat/bticino. Leggi AGENTS.md e docs/BTICINO-HANDOFF.md. Importa soltanto la
> versione corrente e ciò che serve a un collega per riprodurla; esempi pubblici
> sintetici, nessuna commessa o sessione privata. Collega diagnosi, MCP, skill,
> output Documentor e test al programma, preservando il backend QElectroTech.
> Aggiorna le guide e il lock, esegui la demo reale, committa con scope bticino,
> pusha il branch e apri una PR verso main. Riporta cosa è verificato e cosa
> richiede ancora un passaggio manuale.
