<#
Instala ou atualiza o Leitor de pedidos CDR neste computador.

Uso (PowerShell, sem precisar de administrador):
    powershell -ExecutionPolicy Bypass -File instalar-leitor-pedidos.ps1

Ou, sem clonar nada antes:
    iwr https://raw.githubusercontent.com/pedrsilva3515/Estudo-do-CDR/codex/mvp-interpretacao-pedidos/instalar-leitor-pedidos.ps1 -OutFile "$env:TEMP\instalar-leitor-pedidos.ps1"
    powershell -ExecutionPolicy Bypass -File "$env:TEMP\instalar-leitor-pedidos.ps1"

Etapas:
  1. Garante Python 3.10+ e Git (instala pelo winget quando faltam).
  2. Baixa ou atualiza o repositório em %LOCALAPPDATA%\LeitorPedidosCDR\app.
  3. Cria um ambiente virtual próprio e instala as dependências da interface.
  4. Cria atalho na Área de Trabalho.
  5. Instala a macro AnalisarPedidoAtivo no GlobalMacros do CorelDRAW, quando possível.
#>
param(
    [string]$Branch = "codex/mvp-interpretacao-pedidos",
    [string]$Repositorio = "https://github.com/pedrsilva3515/Estudo-do-CDR.git",
    [switch]$SemMacro
)

$ErrorActionPreference = "Stop"
$pasta = Join-Path $env:LOCALAPPDATA "LeitorPedidosCDR"
$app = Join-Path $pasta "app"
$venv = Join-Path $pasta "venv"

function Etapa([string]$texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }

function Atualizar-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

function Encontrar-Python {
    foreach ($cmd in @(@("py", "-3"), @("python"))) {
        try {
            $versao = & $cmd[0] $cmd[1..9] -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and [version]$versao -ge [version]"3.10") { return ,$cmd }
        } catch {}
    }
    return $null
}

function Instalar-Winget([string]$id) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget não está disponível. Instale $id manualmente e rode este script de novo."
    }
    winget install --id $id -e --scope user --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        winget install --id $id -e --accept-package-agreements --accept-source-agreements
    }
    Atualizar-Path
}

New-Item -ItemType Directory -Force -Path $pasta | Out-Null

Etapa "Verificando Python"
$python = Encontrar-Python
if (-not $python) {
    Write-Host "Python 3.10+ não encontrado. Instalando Python 3.12..."
    Instalar-Winget "Python.Python.3.12"
    $python = Encontrar-Python
    if (-not $python) { throw "Python instalado, mas não encontrado no PATH. Feche e abra o PowerShell e rode de novo." }
}
Write-Host "Usando: $($python -join ' ')"

Etapa "Verificando Git"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Instalar-Winget "Git.Git"
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        $gitPadrao = "$env:ProgramFiles\Git\cmd"
        if (Test-Path $gitPadrao) { $env:Path += ";$gitPadrao" }
    }
}

Etapa "Baixando o Leitor de pedidos"
if (Test-Path (Join-Path $app ".git")) {
    git -C $app fetch origin $Branch
    git -C $app checkout $Branch
    git -C $app pull --ff-only origin $Branch
} else {
    if (Test-Path $app) { Remove-Item -Recurse -Force $app }
    git clone --branch $Branch $Repositorio $app
}
if ($LASTEXITCODE -ne 0) { throw "Falha ao baixar o repositório." }

Etapa "Instalando dependências"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
    & $python[0] $python[1..9] -m venv $venv
}
$pyVenv = Join-Path $venv "Scripts\python.exe"
$pywVenv = Join-Path $venv "Scripts\pythonw.exe"
& $pyVenv -m pip install --upgrade pip
& $pyVenv -m pip install -e "$app[gui,api]"
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependências." }

Etapa "Criando atalho na Área de Trabalho"
$shell = New-Object -ComObject WScript.Shell
$atalho = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "Leitor de pedidos CDR.lnk"))
$atalho.TargetPath = $pywVenv
$atalho.Arguments = "-m zcfreader.gui"
$atalho.WorkingDirectory = $pasta
$atalho.Save()

if (-not $SemMacro) {
    Etapa "Instalando macro no CorelDRAW"
    # O editor VBA só importa .bas em ANSI com CRLF.
    $origem = Join-Path $app "macro-corel\LeitorPedidosCDR.bas"
    $bas = Join-Path $pasta "LeitorPedidosCDR.bas"
    $texto = (Get-Content -Raw -Encoding UTF8 $origem) -replace "`r?`n", "`r`n"
    [IO.File]::WriteAllText($bas, $texto, [Text.Encoding]::GetEncoding(1252))

    $instalada = $false
    # Se o CorelDRAW já estiver aberto, o COM se conecta a ele: nesse caso não o fechamos.
    $jaAberto = [bool](Get-Process CorelDRW -ErrorAction SilentlyContinue)
    try {
        $corel = New-Object -ComObject CorelDRAW.Application
        $projeto = $corel.VBE.VBProjects.Item("GlobalMacros")
        foreach ($c in @($projeto.VBComponents)) {
            if ($c.Name -eq "LeitorPedidosCDR") { $projeto.VBComponents.Remove($c) }
        }
        $projeto.VBComponents.Import($bas) | Out-Null
        $instalada = $true
        try { $corel.GMSManager.RefreshMacros() } catch {}
        if (-not $jaAberto) { $corel.Quit() }
    } catch {
        Write-Host "Não foi possível importar automaticamente: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    if ($instalada) {
        Write-Host "Macro GlobalMacros.LeitorPedidosCDR.AnalisarPedidoAtivo instalada." -ForegroundColor Green
        if ($jaAberto) { Write-Host "O CorelDRAW estava aberto: feche-o normalmente para gravar a macro no GlobalMacros." -ForegroundColor Yellow }
    } else {
        Write-Host @"
Importe a macro manualmente (uma única vez):
  1. No CorelDRAW: Ferramentas > Macros > Editor do Visual Basic (Alt+F11).
  2. No painel Projeto, clique em GlobalMacros.
  3. Arquivo > Importar arquivo... e escolha:
     $bas
  4. Arquivo > Salvar GlobalMacros e feche o editor.
"@ -ForegroundColor Yellow
    }
}

Etapa "Concluído"
Write-Host "Abra pelo atalho 'Leitor de pedidos CDR' na Área de Trabalho."
Write-Host "No CorelDRAW, rode a macro AnalisarPedidoAtivo (Alt+Shift+F11) para analisar o documento aberto."
Write-Host "Para atualizar no futuro, execute este script novamente."
