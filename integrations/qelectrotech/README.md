# QElectroTech

Backend disponibile. Server in `src/qelectrotech_mcp`, skill in
`skills/grid-single-line`, compositore comune in `src/gridline`.

Il server espone ricerca/ispezione simboli, creazione progetto/fogli,
inserimento/modifica/spostamento apparecchi, collegamenti, cancellazione,
validazione, distinta CSV, anteprima SVG e apertura desktop. Le scritture
creano backup salvo esplicita disabilitazione su una nuova demo sintetica.

Le definizioni sono incorporate nel QET. Il preview MCP è approssimativo:
non è il renderer nativo e non verifica tutti i comportamenti grafici di QET.
Il PDF finale è Documentor; la sua vista va controllata contro il progetto.

Per ambiente e prova: docs/installation.md. Per il metodo:
skills/grid-single-line/SKILL.md. Per il catalogo pubblico: manifest e licenza
in `src/gridline/resources/symbols`.
