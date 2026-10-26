# Stato e sviluppi dell'ufficio tecnico

Aggiornato il 26/10/2026. Le caselle distinguono capacità implementate e lavoro
futuro. La consegna software del workflow unifilari non implica che siano già
pronte carpenteria, 3D o progettazione esecutiva automatica.

## Disponibile

- [x] Schema generale di integrazione QElectroTech, MCP, progetto modificabile.
- [x] Schema di quadro con dati di dimensionamento da export TiSystem originali.
- [x] MCP locale BTicino: input, riconciliazione, composizione Documentor e hash.
- [x] Cartiglio aziendale, copertina con progettista configurabile, A3/A4 e note.
- [x] Due percorsi nella stessa applicazione; workspace combinato con modelli
  separati e stato di coordinamento esplicito.
- [x] Test e demo locali. Condizioni e controlli non effettuati in VALIDATION.md.

## P1 — progetto coordinato e dati verificabili

| Sviluppo | Risultato atteso | Criterio di completamento |
|---|---|---|
| Registro comune circuiti/apparecchi | ID stabili fra generale, quadri, BOM e cavi | Una modifica rende obsolete solo le viste dipendenti; conflitti e revisioni rilevati su due casi reali |
| Acquisizione guidata TiSystem | Ridurre ripetizioni UI con rilettura, log e ripresa | Creazione, calcolo, verifica, export e riapertura testati; gestione degli errori senza alterare gli originali |
| Cataloghi multi-fornitore | Metadati OEM e simboli originali tracciati | Fonte/licenza, revisione, dimensioni, poli, dissipazione e accessoristica verificate; nessun equivalente inventato |
| Verifiche elettriche complete | Portata corretta, caduta, I²t, corto minimo/massimo, selettività e backup | Riscontri con motore qualificato e curve/tabelle OEM; esiti riproducibili, ipotesi e limiti espliciti |
| Interfacce MT e DC | Protezioni, TA/TV, terra, schermi, PCS e ripartizione batterie | Dati rete/OEM disponibili, studio coordinato, riesame del progettista e prove pertinenti |

## P2 — dettagli costruttivi del quadro

| Sviluppo | Risultato atteso | Criterio di completamento |
|---|---|---|
| Carpenteria e piastra | Ingombri, grado IP/IK richiesto, accessibilità, entrate cavi | Dimensioni OEM, spazi utili e vincoli costruttivi controllati; export quotato |
| Fronte e lato | Prospetti frontale/laterale, interno/porta e sezioni | Stessi ID dell'unifilare, quote leggibili e riferimento alla revisione |
| Guide DIN e posizionamento | Interruttori, alimentatori, relè, PLC, morsettiere | Larghezze e profondità reali; riserve, accessori, distanze, manovra e manutenzione verificate |
| Canaline e cablaggio | Percorsi, separazione potenza/segnale, raggi e riempimento | Nessuna collisione; sezioni/posa e spazi di curvatura confermati |
| Morsetti e connessioni | Morsettiere, numeri filo, PE/N, ponticelli, capicorda | Connessioni e sezioni coerenti con schema, lista fili e BOM |
| Bilancio termico | Dissipazione, ventilazione/condizionamento e derating | Perdite OEM e condizioni ambientali; confronto con metodo e prove applicabili |
| Tenuta e costruzione | Insieme quadro, sbarre, fissaggi, separazioni e verifiche | Requisiti della serie CEI EN IEC 61439 applicabili individuati e verificati da responsabile competente; nessuna conformità dedotta dal render |
| Officina e collaudo | Disegni di foratura, etichette, montaggio, controlli FAT | Documenti coerenti con distinta e revisioni, prova su un quadro reale |

## P3 — modello geometrico e consegna

- [ ] Libreria parametrica con STEP originali OEM quando disponibili, oppure
  ingombri dichiarati; origine e grado di fedeltà visibili.
- [ ] Modello 3D del quadro con porta, piastra, guide, apparecchi e canaline;
  controllo interferenze e accessibilità. Render derivato dalla geometria.
- [ ] Esportazioni STEP/GLB e tavole PDF Documentor; DXF costruttivi da geometria
  controllata. Un PDF TiSystem non viene reinterpretato come modello 3D.
- [ ] Distinta materiali con alternative qualificate, accessori e ricambi;
  dati economici separati dalle verifiche tecniche.
- [ ] Handover as-built, revisione, documenti fornitori, prove e manutenzione;
  consegna aziendale identificata da hash e stato di approvazione.
- [ ] Collaudi su workstation di colleghi macOS/Windows/Linux e verifica della
  riapertura dei formati nativi, con procedure d'installazione riproducibili.

## Come completare una voce

Aprire un branch dedicato; specificare input necessari, dati OEM, formato
modificabile e prove di accettazione. Implementare un caso sintetico e uno
locale autorizzato, eseguire test e controllo visivo, aggiornare VALIDATION e
questa roadmap. Promuovere la casella solo con evidenze. Firma, approvazione
e conformità dell'impianto non vengono assegnate automaticamente dal software.

Riferimenti di partenza per le verifiche future: [IEC 61439-1](https://webstore.iec.ch/en/publication/32338), [IEC 61439-2](https://webstore.iec.ch/en/publication/30043) e [guida alla specifica IEC TR 61439-0](https://webstore.iec.ch/en/publication/66003). Confermare edizioni e recepimenti applicabili al progetto quando si avvia lo sviluppo.
