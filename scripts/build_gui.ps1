param(
    [string]$Nome = "Leitor-de-Pedidos-CDR",
    [string]$DistDir = "dist",
    [string]$BuildDir = "build"
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$saida = Join-Path $raiz $DistDir
$temporarios = Join-Path $raiz $BuildDir

Push-Location $raiz
try {
    python -m pip install -e ".[gui,api]" pyinstaller
    python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name $Nome `
        --paths "fase3-parser" `
        --collect-all tkinterdnd2 `
        --collect-all keyring `
        --collect-all rapidocr_onnxruntime `
        --collect-submodules win32com `
        --hidden-import pythoncom `
        --hidden-import pywintypes `
        --add-data "$(Join-Path $raiz 'fase3-parser/zcfreader/regras_da_casa.md');zcfreader" `
        --distpath $saida `
        --workpath $temporarios `
        --specpath $temporarios `
        "scripts/cdr_pedido_gui_entry.py"
} finally {
    Pop-Location
}

Write-Output "Executável criado em $saida\$Nome.exe"
