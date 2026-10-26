# Gridline — istruzioni per gli agenti

Leggi README.md, docs/installation.md, docs/architecture.md e VALIDATION.md.
Per generare schemi leggi skills/gridline/SKILL.md e la skill dell'integrazione.
QElectroTech e BTicino sono entrambi disponibili su `main`, come percorsi
alternativi o combinabili: generale di integrazione, quadro con dati di
dimensionamento, oppure fascicolo coordinato. Scegli in base alla richiesta.

## Operatività

1. Verifica Python 3.12+ e riusa gli ambienti funzionanti. Installa il progetto
   con `uv sync --frozen`; non aggiornare il lock senza motivo. Per QET usa
   `gridline doctor` (oppure `python3 scripts/doctor.py --json` prima della
   installazione); per BTicino usa `gridline doctor --backend bticino`.
2. Genera la configurazione con `uv run --frozen gridline mcp-config COMMESSA`.
   Integra soltanto il server nuovo nella configurazione del client. Preserva
   gli altri server. La configurazione scritta non dimostra una sessione attiva.
3. Per QET esegui `gridline smoke` in una directory nuova; per BTicino usa
   `gridline bticino-smoke COMMESSA` dopo l'acquisizione degli export nativi.
   Controlla le anteprime e registra la verifica nell'applicazione nativa
   separatamente. Il solo `doctor` non dimostra un ambiente pronto.
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

Per BTicino segui integrations/bticino/README.md; docs/BTICINO-HANDOFF.md conserva
la procedura del contributo iniziale, già integrato. Per nuove modifiche usa
branch e clone/worktree dedicati, senza modificare il checkout di un altro
agente o annullare modifiche altrui. Preserva entrambi i backend.

Test: `uv run --frozen pytest`. Esegui inoltre il caso reale sintetico del backend
modificato. Aggiorna README, CHANGELOG, VALIDATION e documentazione dell'integrazione.
Il repository usa commit Conventional Commits con scope del componente.
