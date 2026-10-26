---
name: grid-single-line
description: Crea e modifica unifilari QElectroTech Grid Society da idea, schizzo, as-built o capitolato, con simbologia tracciata, PDF Documentor e controlli distinti dalla validazione elettrica.
---

# Unifilari QElectroTech con Gridline

Questa skill guida l'agente: interpreta la richiesta, costruisce il circuito
tramite MCP e prepara tutti gli intermedi per il PDF. Il compositore da solo
non interpreta la topologia. Leggi AGENTS.md e docs/installation.md del checkout.

## Ambiente

Esegui il doctor, integra il server generato da `gridline mcp-config` e verifica
`health_check` nella sessione effettiva. Su una macchina nuova esegui
`gridline smoke CARTELLA_NUOVA` e ispeziona le anteprime. Registra la revisione
desktop QET separatamente. Non dichiarare pronto un ambiente dal solo preflight.

## Metodo

1. Leggi notes/context.md, decisions.md, status.md, attachments.md e le fonti.
   Applica references/input-output.md, references/rules.md e references/qa.md.
2. Risolvi prima apparecchi, terminali e collegamenti, distinguendo esistente,
   nuovo, ipotesi e dato mancante. Punto di innesto e confini sono espliciti.
3. Cerca e ispeziona i simboli. Il catalogo pubblico è in
   src/gridline/resources/symbols con manifest e licenza. MT/RCBO sono originali
   QET: gli adattamenti storici da schemario del committente non sono distribuiti.
   Altri simboli includono adattamenti di scala dichiarati. Per un simbolo
   mancante consulta la collezione QET installata e registra la provenienza.
4. Crea/modifica il QET via MCP con UUID e terminali reali, definizioni incorporate,
   connessioni ortogonali e backup. Il preview MCP è approssimativo.
5. Mantieni QET e viste coerenti; non sovrascrivere modifiche manuali da un
   modello precedente. Genera viste senza vecchi bordi/cartigli incorporati.
6. Compila variables/drawing-set.json: generali prima dei dettagli, niente
   legenda aggiunta senza richiesta. Esegui `gridline check`, quindi
   `gridline render`. Solo Documentor produce il PDF finale.
7. Verifica ogni pagina, circuito preservato, simboli, incroci, etichette e
   cartigli. Registra separatamente XML, PDF, QET nativo e riesame elettrico.
8. Consegna sorgenti, PDF, modello eventuale, fonti, QA e comandi di rigenerazione.

`new` crea uno scheletro vuoto, `demo` un esercizio fittizio. Nessuno dei due
costituisce un impianto progettato. `check` verifica struttura e riferimenti;
dimensionamento, selettività e conformità non sono certificati dal software.
