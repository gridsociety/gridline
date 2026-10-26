---
name: gridline
description: Genera e aggiorna unifilari Grid Society da richieste e allegati, scegliendo l'integrazione disponibile e verificando ambiente, sorgenti e PDF Documentor.
---

# Gridline

Apri il checkout Gridline e leggi AGENTS.md, docs/installation.md e
docs/architecture.md. Esegui `gridline integrations`: non usare un backend
pianificato come se fosse implementato. Per QET leggi anche
skills/grid-single-line/SKILL.md; per BTicino skills/grid-bticino/SKILL.md.

Scegliere in base al risultato: «schema generale di integrazione» → QET;
«schema di quadro con dati di dimensionamento» → BTicino; «fascicolo coordinato»
→ combined. Specifiche prodotto, portate, cavi, tarature e poteri di interruzione
indicano il percorso BTicino; integrazione di un BESS nell’esistente indica il
generale QET. Se manca una scelta, esplicitare l’interpretazione e proporre
la modalità combinata quando entrambi gli elaborati sono utili. Non trasferire
valori o stati di approvazione fra i due modelli senza riconciliazione.
Usare il nome del progettista della commessa, mai quello dell’autore del tool.
Consultare docs/ROADMAP.md per distinguere capacità presenti e future.

L'utente fornisce scopo, idea e fonti. Gestisci strumenti e file intermedi;
non richiedere all'utente di prepararli se puoi generarli. Rileva cosa manca
con il doctor e riusa installazioni funzionanti. Segui la prova completa
senza confondere preflight, sessione MCP, PDF e resa nativa.

Conserva i dati della commessa fuori dal repository pubblico e registra
fonti, decisioni, verifiche e domande aperte nella cartella del progetto.
