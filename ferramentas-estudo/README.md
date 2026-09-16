# Ferramentas do estudo avançado

`GerarCasosAvancados.ps1` reproduz os casos controlados 28–66 usados para
estudar páginas, PowerClip, texto, layers, contornos e curvas.

Requisitos:

- Windows;
- CorelDRAW 2025 v26 registrado como `CorelDRAW.Application.26`;
- PowerShell;
- `casos-de-teste/caso_00_base.cdr` presente.

Uso a partir da raiz do repositório:

```powershell
.\ferramentas-estudo\GerarCasosAvancados.ps1
```

Por segurança, o padrão grava em `gerados-casos-avancados/` e não substitui as
fixtures versionadas. Para escolher outra pasta:

```powershell
.\ferramentas-estudo\GerarCasosAvancados.ps1 -OutputDirectory C:\temp\cdr-casos
```

Os manifestos em `casos-de-teste/caso_XX_*.json` descrevem a mutação e o
resultado esperado de cada caso.
