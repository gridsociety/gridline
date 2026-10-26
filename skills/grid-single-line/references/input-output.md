# Ingresso, ragionamento e consegna

## Prompt minimo per il collega

> Usa $grid-single-line. Voglio un unifilare per [progetto], partendo da [idea/allegati]. La rete è [MT/BT e tensione se nota], l'esistente è [descrizione], aggiungiamo [apparecchi]. Il punto d'innesto previsto è [dorsale/quadro/dispositivo]. Prepara il sorgente QET e un PDF nello stile aziendale; segnala i dati mancanti e salva le decisioni nel progetto.

Sono sufficienti idea e scopo per iniziare. Per completare il circuito servono riscontri sulle scelte che cambiano collegamenti e protezioni. Chiedere presto: punto di connessione, apparati esistenti da mantenere, confini di fornitura, protezione generale/interfaccia e alternative richieste. Una potenza nominale non determina da sola protezioni, cavi e corrente di corto circuito.

## Dati da raccogliere

- Identità: nome progetto, committente, ubicazione, codice, revisione, data, POD se pertinente.
- Rete: tensione, schema di terra, potenza disponibile, eventuali dati di corto circuito e prescrizioni del distributore.
- Esistente: as-built, sigle, TA/TV/TO, protezioni, quadri, trasformatori, cavi e carichi/generatori.
- Intervento: apparecchi, potenze/tensioni, connessioni AC/DC, ausiliari, misure, comandi, confini cabina/station e fornitore.
- Obiettivo: concettuale, preliminare o esecutivo; alternative; formato obbligatorio di stampa se c'è.
- Fonti: PDF, DWG, QET, manuali, schemi costruttore, schizzo e note. Registrare file, pagina/revisione, data e affidabilità.

Ogni dato ha valore/unità, stato (CONFERMATO / IPOTESI / DA DEFINIRE) e fonte. Non trasferire da altre commesse marchi, taglie, POD, interfacce, cavi, schema di terra o architettura A/B a un nuovo cliente.

## Modello dell'impianto

Oggetti: sbarra, interruttore automatico, sezionatore, sezionatore di terra, fusibile, magnetotermico, differenziale, TA, TV, TO, relè, contatore, trasformatore, convertitore, batteria, generatore FV, carico, porta funzionale, confine di assieme.

Per ciascuno: id stabile, sigla, tipo/funzione, ubicazione, esistente/nuovo, caratteristiche e fonte, simbolo/terminali, stato di rappresentazione. Per ciascun collegamento: estremi e terminali, dominio MT/BT/DC/misura/comando, poli, cavo se noto, fonte; percorso grafico separato dalla connessione logica.

Il grafo è distinto dal posizionamento. Un confine tratteggiato non è un collegamento. Incrocio senza nodo non significa connessione. Colore non sostituisce la topologia. Gli sganciatori magnetotermici non sostituiscono un relè di protezione esterno.

## Output atteso

- PDF vettoriale: generali all'inizio, dettagli dopo; nessuna legenda aggiunta automaticamente.
- QET editabile con simboli incorporati; libreria usata e provenienza.
- Modello/tabella componenti e collegamenti, fonti e ipotesi.
- Anteprime di tutte le tavole e rapporto QA con verifiche effettuate/non effettuate.
- Memoria in `notes/` e `GENERATION.md` con comandi, versioni e dipendenze.
- Stato: bozza / approvato graficamente / verificato elettricamente, con persona e data reali quando disponibili.
