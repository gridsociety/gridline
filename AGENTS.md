# Gridline — istruzioni per gli agenti

Leggi README.md, docs/installation.md, docs/architecture.md e VALIDATION.md.
Per generare schemi leggi skills/gridline/SKILL.md e la skill dell'integrazione.

## Operatività

1. Esegui `python3 scripts/doctor.py --json` con Python 3.12+; se assente indica
   il requisito. Riusa QET, Documentor e gli ambienti già funzionanti. Installa
   il progetto con `uv sync --frozen`; non aggiornare il lock senza motivo.
2. Genera la configurazione con `uv run --frozen gridline mcp-config COMMESSA`.
   Integra soltanto il server nuovo nella configurazione del client. Preserva
   gli altri server. La configurazione scritta non dimostra una sessione attiva.
3. Esegui una prova in una directory nuova con `gridline smoke`. Controlla le
   anteprime; registra l'apertura nel QET desktop separatamente. Non dichiarare
   pronto un ambiente soltanto perché `doctor` termina correttamente.
4. Prima di modificare una commessa leggi tutte le note e le fonti. Mantieni
   distinti fatti, ipotesi, punti aperti e approvazioni. Non inventare taglie,
   terminali, tarature o fonti. Chiedi le decisioni che cambiano la topologia.
5. QET, modello eventuale e viste devono essere coerenti. Non ricostruire un QET
   modificato manualmente da dati obsoleti. Preserva originali e backup.
6. PDF finali solo Documentor; nessun fallback PDF. Conserva log, variabili,
   hash e verifiche. Non pubblicare nel registro Documentor senza richiesta.
7. I progetti cliente sono esterni al repository; `workspaces/` è ignorata.
   Non committare dati di commessa, credenziali, cookie, sessioni, firme o timbri.

## Sviluppo

Le integrazioni possono avere modelli elettrici diversi. Condividono il
contratto di consegna descritto in docs/architecture.md. Evita conversioni
implicite tra QET e output BTicino. Non attribuire a BTicino una funzione non
verificata nell'applicazione reale.

Per BTicino segui docs/BTICINO-HANDOFF.md. Lavora sul branch `feat/bticino`,
non modificare il progetto locale di un altro agente e non annullare modifiche
altrui. Il codice QET rimane operativo dopo l'integrazione.

Test: `uv run --frozen pytest`. Esegui inoltre il caso reale sintetico del backend
modificato. Aggiorna README, CHANGELOG, VALIDATION e documentazione dell'integrazione.
Il repository usa commit Conventional Commits con scope del componente.
