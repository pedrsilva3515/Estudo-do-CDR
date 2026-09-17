$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$saida = Join-Path $raiz "dist"
$temporarios = Join-Path $raiz "build"

Push-Location $raiz
try {
    python -m pip install -e ".[gui,api]" pyinstaller
    python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name "Leitor-de-Pedidos-CDR" `
        --paths "fase3-parser" `
        --collect-all tkinterdnd2 `
        --collect-all keyring `
        --distpath $saida `
        --workpath $temporarios `
        --specpath $temporarios `
        "scripts/cdr_pedido_gui_entry.py"
} finally {
    Pop-Location
}

Write-Output "Executável criado em $saida\Leitor-de-Pedidos-CDR.exe"
