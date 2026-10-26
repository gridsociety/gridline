# Contribuire

Usare branch per integrazione o correzione e clone/worktree separato quando
più agenti lavorano contemporaneamente. Non annullare modifiche altrui.

Commit: `tipo(scope): comportamento concreto`, in inglese per continuità con
i repository aziendali. Tipi: `feat`, `fix`, `docs`, `test`, `chore`.
Scope: `qelectrotech`, `bticino`, `core`, `setup`, `docs`.

Esempi:

```text
feat(qelectrotech): publish reproducible agent-guided single-line workflow
feat(bticino): add native single-line generation through MCP
fix(core): preserve drawing dimensions in Documentor output
```

Una funzione completa comprende codice, guida per l'agente, requisiti,
esempio sintetico e verifica. Non dichiarare un backend operativo con soli
stub o import da file non inclusi. Le dipendenze Python sono bloccate da uv.lock;
software esterni, versioni, accessi e prove reali sono documentati separatamente.

Prima del commit: test pertinenti, `git diff --check`, revisione di tutti i file
nuovi e controllo che non siano entrati dati cliente o percorsi personali.
La CI usa runner GitHub ospitati: non collegare codice pubblico non revisionato
ai runner aziendali con accesso alla rete interna o credenziali.

PR: problema e comportamento risultante, verifica riproducibile, limitazioni.
Per BTicino seguire docs/BTICINO-HANDOFF.md. Il merge squash mantiene un commit
logico per ogni integrazione nella storia principale.
