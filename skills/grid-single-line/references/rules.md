# Regole derivate dal risultato approvato

## Grafo prima della grafica

Dorsale di distribuzione orizzontale e rami verticali discendenti. Evitare collegamenti che aggirano l'intero foglio e rendono ambiguo il punto di innesto. Separare la partenza in cabina dall'apparecchiatura MT della station; indicare nome e confine fisico.

Configurazione A: dorsale a monte, due protezioni generali indipendenti, misure correnti e SPG per ciascun ramo. Configurazione B: protezione generale comune a monte, dorsale a valle e due rami separati. Il tipo di dispositivo dei rami B e il destinatario del rincalzo dipendono dal progetto: una soluzione con QS e rincalzo DG comune non è una regola automatica.

Una station può essere rappresentata come gruppo funzionale, dichiarando ciò che non è sviluppato. Eliminare un simbolo duplicato dalla rappresentazione non significa eliminare hardware dall'offerta. Non importare il modello Schneider SM6 solo perché presente in un esempio.

## Simboli

Magnetotermico automatico: contatto con qualificatore automatico pieno, sganciatori termico/magnetico nel rettangolo a due celle. La variante differenziale aggiunge Id. L'interruttore con sganciatore elettronico o protezione esterna richiede simbolo e testo pertinenti, non un magnetotermico scelto per somiglianza.

Scala uniforme, proporzioni preservate, stessa dimensione per stessa famiglia nella medesima vista. Mai deformare X/Y per riempire il foglio. La dimensione stampata va verificata con testi e leggibilità; non esiste qui una pretesa misura normativa universale. Il riferimento grafico storico CEI fornito non certifica l'edizione vigente.

## Impaginazione

Preferenza approvata: il foglio segue l'ingombro della vista, lasciando poco spazio laterale inutile. Il compositore usa formati personalizzati e scala uniforme. Se il cliente impone un formato ISO, rispettarlo; comporre più dettagli o riorganizzare il disegno invece di deformarlo. Non etichettare A0/A2/A3 un formato personalizzato.

Cornice solo esterna: fasce nero/bianco alternate, numeri sopra/sotto, lettere sui lati. Nessuna griglia sopra i simboli. Usare coordinate per rinvii solo se corrispondono alla tavola effettiva.

Generali completi delle alternative per primi, poi dettagli. Un cartiglio in basso a destra nei generali; nei dettagli aggiungere lo storico revisioni riquadrato a sinistra. Cartiglio con logo ufficiale Grid Society, oggetto, committente, sito, POD quando disponibile, codice, revisione/data, stato, numero pagina e vista. Non inventare firme o registrazioni Documentor.

Convenzione del caso storico: nero esistente, arancione intervento BESS, blu tratteggiato misura/comando. In altri progetti dichiarare la convenzione scelta. Uniformare testi e distanze; conservare spazi sufficienti intorno a simboli, targhe e percorsi. Non aggiungere un foglio legenda salvo richiesta.

## Standard aziendali e limiti

Fonte organizzativa esaminata: repository `grid-standards`, versione del nuovo standard nel manifest; struttura in inglese, contenuti italiani. Asset di marchio derivati da `document-templates/static/gridsociety/logo_scritta/GS Brand Color.svg`, snapshot incluso e tracciato, non ridisegnato.

Lo standard Documentor prescrive variabili separate dai template, memoria in notes/, naming di emissione e pubblicazione tramite Documentor. L'utente ha confermato esplicitamente che i PDF devono essere generati con Documentor. QET è il sorgente elettrico; gli script preparano SVG e dati. Il template Jinja a sezioni dirette incluso conserva i formati di ciascuna tavola e genera il PDF attraverso Documentor. Nessun assemblaggio finale manuale o fallback PDF.

Ogni nuovo progetto deve avere evidenza del comando Documentor e del producer PDF. Un render locale ha ID DRAFT; l'emissione production richiede il registro reale e l'autorizzazione del progetto.
