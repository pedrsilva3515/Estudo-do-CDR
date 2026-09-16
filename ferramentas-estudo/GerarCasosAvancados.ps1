param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\gerados-casos-avancados')
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = Join-Path $repo 'casos-de-teste\caso_00_base.cdr'
$output = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $output -Force | Out-Null
$app = $null
$doc = $null

function Close-Document {
    if ($script:doc) { try { $script:doc.Close() } catch { }; $script:doc = $null }
}
function Open-Base([bool]$clean = $false) {
    $script:doc = $script:app.OpenDocument($script:source)
    $script:doc.Unit = 4 # cdrCentimeter
    if ($clean -and $script:doc.ActivePage.Shapes.Count -gt 0) {
        $script:doc.ActivePage.Shapes.All().Delete()
    }
}
function Save-Case([string]$name) {
    $options = $script:app.CreateStructSaveAsOptions()
    $options.Overwrite = $true
    $script:doc.SaveAs((Join-Path $output $name), $options)
}
function Add-Rectangle([string]$name, [double]$x, [double]$y, [double]$w, [double]$h) {
    $shape = $script:doc.ActiveLayer.CreateRectangle2($x, $y, $w, $h)
    $shape.Name = $name
    try { $shape.Outline.SetNoOutline() } catch { }
    return $shape
}
function Add-PowerClip([string]$suffix, [double]$x, [double]$y) {
    $container = $script:doc.ActiveLayer.CreateRectangle2($x, $y, 4, 4)
    $container.Name = "Recipiente$suffix"
    $content = $script:doc.ActiveLayer.CreateEllipse2(($x + 2), ($y + 2), 1.5)
    $content.Name = "Conteudo$suffix"
    $content.AddToPowerClip($container)
}
function Add-ArtisticText([string]$value, [string]$font, [double]$size, [double]$x, [double]$y) {
    $shape = $script:doc.ActiveLayer.CreateArtisticText($x, $y, $value)
    $shape.Name = 'TextoEstudo'
    $shape.Text.Story.Font = $font
    $shape.Text.Story.Size = $size
    return $shape
}
function New-LayerDocument {
    Open-Base $true
    $layer = $script:doc.ActivePage.CreateLayer('LayerEstudo')
    $shape = $layer.CreateRectangle2(4, 8, 5, 3)
    $shape.Name = 'ObjetoDaLayer'
    return $layer
}

try {
    $app = New-Object -ComObject CorelDRAW.Application.26
    $app.Visible = $false

    # 28–32: origem, limites, sangria e tamanhos por página.
    Open-Base
    $doc.DrawingOriginX = 0; $doc.DrawingOriginY = 0
    Save-Case 'caso_28_origem_zero.cdr'; Close-Document

    Open-Base $true
    $doc.DrawingOriginX = 0; $doc.DrawingOriginY = 0
    $page = $doc.ActivePage
    Add-Rectangle 'CruzaEsquerda' ($page.LeftX - 0.5) ($page.CenterY - 0.5) 1 1 | Out-Null
    Add-Rectangle 'CruzaDireita' ($page.RightX - 0.5) ($page.CenterY - 0.5) 1 1 | Out-Null
    Add-Rectangle 'CruzaBase' ($page.CenterX - 0.5) ($page.BottomY - 0.5) 1 1 | Out-Null
    Add-Rectangle 'CruzaTopo' ($page.CenterX - 0.5) ($page.TopY - 0.5) 1 1 | Out-Null
    Add-Rectangle 'Dentro' ($page.CenterX - 0.5) ($page.CenterY - 0.5) 1 1 | Out-Null
    Save-Case 'caso_29_cruza_quatro_bordas.cdr'
    $doc.DrawingOriginX = 5; $doc.DrawingOriginY = -7
    Save-Case 'caso_30_origem_alterada.cdr'; Close-Document

    Open-Base $true
    $doc.DrawingOriginX = 0; $doc.DrawingOriginY = 0
    $doc.ActivePage.Bleed = 0.3; $page = $doc.ActivePage
    Add-Rectangle 'AteSangriaEsquerda' ($page.LeftX - 0.3) ($page.CenterY - 1) 2 2 | Out-Null
    Save-Case 'caso_31_sangria_3mm.cdr'; Close-Document

    Open-Base $true
    $doc.DrawingOriginX = 0; $doc.DrawingOriginY = 0
    $doc.AddPages(1); $page = $doc.Pages.Item(2); $page.Activate(); $page.SetSize(10, 20)
    Add-Rectangle 'CruzaDireitaPagina2' ($page.RightX - 0.5) ($page.CenterY - 0.5) 1 1 | Out-Null
    Add-Rectangle 'CentroPagina2' ($page.CenterX - 0.5) ($page.CenterY - 0.5) 1 1 | Out-Null
    Save-Case 'caso_32_paginas_tamanhos_diferentes.cdr'; Close-Document

    # 33–36: PowerClip.
    Open-Base $true
    Add-PowerClip 'A' 2 2; Add-PowerClip 'B' 10 10
    Save-Case 'caso_33_powerclip_duplo_mesma_pagina.cdr'; Close-Document

    Open-Base $true
    Add-PowerClip 'Pagina1' 2 2; $doc.AddPages(1); $doc.Pages.Item(2).Activate()
    Add-PowerClip 'Pagina2' 4 4
    Save-Case 'caso_34_powerclip_duas_paginas.cdr'; Close-Document

    Open-Base $true
    $outer = $doc.ActiveLayer.CreateRectangle2(2, 2, 8, 8); $outer.Name = 'RecipienteExterno'
    $inner = $doc.ActiveLayer.CreateRectangle2(4, 4, 4, 4); $inner.Name = 'RecipienteInterno'
    $content = $doc.ActiveLayer.CreateEllipse2(6, 6, 1.5); $content.Name = 'ConteudoAninhado'
    $content.AddToPowerClip($inner); $inner.AddToPowerClip($outer)
    Save-Case 'caso_35_powerclip_aninhado.cdr'; Close-Document

    Open-Base $true
    $page = $doc.ActivePage
    $container = $doc.ActiveLayer.CreateRectangle2(($page.RightX - 1), ($page.CenterY - 2), 4, 4)
    $container.Name = 'RecipienteForaDaPagina'
    $content = $doc.ActiveLayer.CreateEllipse2(($page.RightX + 1), $page.CenterY, 1.5)
    $content.Name = 'ConteudoForaDaPagina'; $content.AddToPowerClip($container)
    Save-Case 'caso_36_powerclip_fora_da_pagina.cdr'; Close-Document

    # 37–44: textos.
    foreach ($case in @(
        @('caso_37_texto_arial_12.cdr', 'Texto Alfa 123', 'Arial', 12),
        @('caso_38_texto_conteudo_alterado.cdr', 'Texto Beta 456', 'Arial', 12),
        @('caso_39_texto_arial_24.cdr', 'Texto Alfa 123', 'Arial', 24),
        @('caso_40_texto_times_12.cdr', 'Texto Alfa 123', 'Times New Roman', 12)
    )) {
        Open-Base $true
        Add-ArtisticText $case[1] $case[2] $case[3] 2 20 | Out-Null
        Save-Case $case[0]; Close-Document
    }
    Open-Base $true
    $paragraph = $doc.ActiveLayer.CreateParagraphText(2, 20, 10, 14, "Primeira linha`rSegunda linha")
    $paragraph.Name = 'ParagrafoEstudo'; $paragraph.Text.Story.Font = 'Arial'; $paragraph.Text.Story.Size = 12
    Save-Case 'caso_41_texto_paragrafo.cdr'; Close-Document

    Open-Base $true
    Add-ArtisticText 'Primeiro objeto' 'Arial' 12 2 20 | Out-Null
    Add-ArtisticText 'Segundo objeto' 'Times New Roman' 18 2 16 | Out-Null
    Save-Case 'caso_42_texto_dois_objetos.cdr'; Close-Document

    Open-Base $true
    Add-ArtisticText 'Texto pagina um' 'Arial' 12 2 20 | Out-Null
    $doc.AddPages(1); $doc.Pages.Item(2).Activate()
    Add-ArtisticText 'Texto pagina dois' 'Times New Roman' 18 2 20 | Out-Null
    Save-Case 'caso_43_texto_duas_paginas.cdr'; Close-Document

    Open-Base $true
    $container = $doc.ActiveLayer.CreateRectangle2(2, 12, 8, 6); $container.Name = 'RecipienteTexto'
    $content = Add-ArtisticText 'Texto no PowerClip' 'Arial' 16 3 16; $content.AddToPowerClip($container)
    Save-Case 'caso_44_texto_powerclip.cdr'; Close-Document

    # 45–48: propriedades de layer.
    $layer = New-LayerDocument; Save-Case 'caso_45_layer_padrao.cdr'; Close-Document
    $layer = New-LayerDocument; $layer.Visible = $false; Save-Case 'caso_46_layer_oculta.cdr'; Close-Document
    $layer = New-LayerDocument; $layer.Printable = $false; Save-Case 'caso_47_layer_nao_imprimivel.cdr'; Close-Document
    $layer = New-LayerDocument; $layer.Editable = $false; Save-Case 'caso_48_layer_bloqueada.cdr'; Close-Document

    # 49–61: contornos.
    Open-Base; Save-Case 'caso_49_contorno_padrao_02mm.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.SetNoOutline()
    Save-Case 'caso_50_sem_contorno.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.Width = 0
    Save-Case 'caso_51_contorno_largura_zero.cdr'; Close-Document
    foreach ($case in @(@('caso_52_contorno_05mm.cdr', 0.05), @('caso_53_contorno_10mm.cdr', 0.1))) {
        Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.Width = $case[1]
        Save-Case $case[0]; Close-Document
    }
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.ScaleWithShape = $true
    Save-Case 'caso_54_contorno_escala_objeto.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.Style = $app.OutlineStyles.Item(2)
    Save-Case 'caso_55_contorno_tracejado.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.LineCaps = 1; $shape.Outline.LineJoin = 1
    Save-Case 'caso_56_contorno_caps_join_1.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.Justification = 1
    Save-Case 'caso_57_contorno_alinhamento_interno.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.Justification = 2
    Save-Case 'caso_58_contorno_alinhamento_externo.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Outline.LineCaps = 2; $shape.Outline.LineJoin = 2
    Save-Case 'caso_59_contorno_caps_join_2.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Delete()
    $line = $doc.ActiveLayer.CreateLineSegment(4, 8, 10, 8); $line.Name = 'LinhaComSetas'; $line.Outline.Width = 0.02
    $line.Outline.StartArrow = $app.ArrowHeads.Item(1); $line.Outline.EndArrow = $app.ArrowHeads.Item(2)
    Save-Case 'caso_60_contorno_setas.cdr'; Close-Document
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.CreateSelection()
    $app.FrameWork.Automation.InvokeItem('1a7d5259-ae16-44e1-9a0c-13a7d4ef26a5')
    Save-Case 'caso_61_contorno_linha_fina.cdr'; Close-Document

    # 67–71: preenchimento e transparencia. Cada caso altera uma propriedade
    # de cada vez em relacao ao retangulo vermelho CMYK do documento base.
    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Fill.ApplyNoFill()
    Save-Case 'caso_67_sem_preenchimento.cdr'; Close-Document

    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1)
    $shape.Fill.ApplyUniformFill($app.CreateCMYKColor(100, 0, 0, 0))
    Save-Case 'caso_68_preenchimento_cmyk_ciano.cdr'; Close-Document

    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1)
    $shape.Fill.ApplyUniformFill($app.CreateRGBColor(0, 0, 255))
    Save-Case 'caso_69_preenchimento_rgb_azul.cdr'; Close-Document

    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.OverprintFill = $true
    Save-Case 'caso_70_preenchimento_sobreimpressao.cdr'; Close-Document

    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1); $shape.Transparency.ApplyUniformTransparency(50)
    Save-Case 'caso_71_transparencia_uniforme_50.cdr'; Close-Document

    Open-Base; $shape = $doc.ActivePage.Shapes.FindShapes('RetanguloBase').Item(1)
    $inicio = $app.CreateCMYKColor(0, 100, 100, 0); $fim = $app.CreateCMYKColor(100, 0, 0, 0)
    # cdrLinearFountainFill = 1 na type library do CorelDRAW 26.
    $shape.Fill.ApplyFountainFill($inicio, $fim, 1)
    Save-Case 'caso_72_degrade_linear.cdr'; Close-Document

    # 62–66: subcaminhos e segmentos de curvas.
    Open-Base $true
    $curve = $app.CreateCurve($doc); $sp = $curve.CreateSubPath(4, 8)
    $null = $sp.AppendLineSegment(7, 10); $null = $sp.AppendLineSegment(10, 8)
    $shape = $doc.ActiveLayer.CreateCurve($curve); $shape.Name = 'CurvaAberta'
    Save-Case 'caso_62_curva_aberta.cdr'; Close-Document

    Open-Base $true
    $curve = $app.CreateCurve($doc); $sp = $curve.CreateSubPath(4, 8)
    $null = $sp.AppendLineSegment(7, 10); $null = $sp.AppendLineSegment(10, 8); $sp.Closed = $true
    $shape = $doc.ActiveLayer.CreateCurve($curve); $shape.Name = 'CurvaFechada'
    Save-Case 'caso_63_curva_fechada.cdr'; Close-Document

    Open-Base $true
    $curve = $app.CreateCurve($doc); $sp = $curve.CreateSubPath(3, 9)
    $null = $sp.AppendLineSegment(5, 10); $null = $sp.AppendLineSegment(7, 9)
    $sp = $curve.CreateSubPath(8, 7); $null = $sp.AppendLineSegment(9, 9); $null = $sp.AppendLineSegment(11, 7); $sp.Closed = $true
    $shape = $doc.ActiveLayer.CreateCurve($curve); $shape.Name = 'DoisSubcaminhos'
    Save-Case 'caso_64_curva_dois_subcaminhos.cdr'; Close-Document

    Open-Base $true
    $curve = $app.CreateCurve($doc); $sp = $curve.CreateSubPath(3, 9); $null = $sp.AppendLineSegment(6, 10)
    $sp = $curve.CreateSubPath(8, 7); $null = $sp.AppendLineSegment(11, 8)
    $shape = $doc.ActiveLayer.CreateCurve($curve); $shape.Name = 'DoisSubcaminhosAbertos'
    Save-Case 'caso_65_curva_dois_subcaminhos_abertos.cdr'; Close-Document

    Open-Base $true
    $curve = $app.CreateCurve($doc); $sp = $curve.CreateSubPath(3, 8)
    $null = $sp.AppendCurveSegment2(11, 8, 5, 11, 9, 5)
    $shape = $doc.ActiveLayer.CreateCurve($curve); $shape.Name = 'CurvaBezierAberta'
    Save-Case 'caso_66_curva_bezier_aberta.cdr'; Close-Document

    Write-Output "Casos 28–66 gerados em: $output"
}
finally {
    Close-Document
    if ($app) { try { $app.Quit() } catch { } }
}
