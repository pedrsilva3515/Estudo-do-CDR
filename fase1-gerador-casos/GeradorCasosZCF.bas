Option Explicit

'==========================================================================
' GeradorCasosZCF — Fase 1 do projeto de engenharia reversa do formato ZCF
'
' Gera uma serie de arquivos .cdr de teste, cada um alterando UMA unica
' caracteristica em relacao a um documento base minimo, e grava um
' manifesto JSON ao lado de cada variante descrevendo a alteracao feita.
'
' Compativel com CorelDRAW 2025 OEM:
'   - Nenhum form (.frm) e usado — apenas este modulo.
'   - Constantes de MsgBox substituidas por valores numericos
'     (48 = vbExclamation, 64 = vbInformation).
'
' COMO USAR:
'   1. Ajuste PASTA_SAIDA abaixo se quiser outra pasta de destino.
'   2. Cole este modulo no editor VBA (Alt+F11 > GlobalMacros > inserir
'      modulo > colar).
'   3. Execute a Sub GerarCasosDeTeste (F5 com o cursor dentro dela).
'   4. Ao final, confira log_geracao.txt na pasta de saida. Casos que
'      falharem sao registrados no log e NAO interrompem os demais.
'==========================================================================

' Pasta onde tudo sera gravado (criada automaticamente se nao existir).
' Mantenha a barra invertida no final.
Private Const PASTA_SAIDA As String = "C:\CDR_Testes\"

Private Const MB_ERRO As Long = 48      ' vbExclamation
Private Const MB_INFO As Long = 64      ' vbInformation
Private Const ERRO_CUSTOM As Long = 60001

Private m_ok As Long
Private m_falhas As Long

'==========================================================================
' PONTO DE ENTRADA
'==========================================================================
Public Sub GerarCasosDeTeste()
    On Error GoTo TrataErroFatal
    m_ok = 0
    m_falhas = 0

    If Not GarantirPasta() Then Exit Sub

    LogMsg "=================================================="
    LogMsg "Inicio da geracao de casos de teste ZCF"
    LogMsg "CorelDRAW: " & VersaoCorel()

    ' Imagens-fonte usadas pelos casos de bitmap (JPEG/PNG/TIFF/BMP e
    ' o par de DPI). Sem elas os casos 01-08 nao rodam.
    If Not GerarImagensFonte() Then
        MsgBox "Falha ao gerar as imagens-fonte. Veja log_geracao.txt em " & PASTA_SAIDA, MB_ERRO, "Gerador ZCF"
        Exit Sub
    End If

    ' Documento base minimo: uma pagina com um retangulo vermelho.
    If Not GerarCasoBase() Then
        MsgBox "Falha ao gerar o documento base. Veja log_geracao.txt em " & PASTA_SAIDA, MB_ERRO, "Gerador ZCF"
        Exit Sub
    End If

    '----------------------------------------------------------------------
    ' Variantes — cada uma altera UMA caracteristica em relacao ao arquivo
    ' indicado como base no manifesto.
    '----------------------------------------------------------------------
    CasoAddBitmap "caso_01_add_bitmap_jpeg", "caso_00_base.cdr", "fonte_base.jpg", "add_bitmap", _
        "{ ""formato_origem"": ""JPEG"", ""arquivo_fonte"": ""fonte_base.jpg"" }", _
        "Importa um bitmap JPEG no documento base."

    CasoAddBitmap "caso_02_add_bitmap_png", "caso_00_base.cdr", "fonte_base.png", "add_bitmap", _
        "{ ""formato_origem"": ""PNG"", ""arquivo_fonte"": ""fonte_base.png"" }", _
        "Importa um bitmap PNG no documento base (mesma imagem do caso_01, formato de origem diferente)."

    CasoAddBitmap "caso_03_add_bitmap_tiff", "caso_00_base.cdr", "fonte_base.tif", "add_bitmap", _
        "{ ""formato_origem"": ""TIFF"", ""arquivo_fonte"": ""fonte_base.tif"" }", _
        "Importa um bitmap TIFF no documento base (mesma imagem do caso_01, formato de origem diferente)."

    CasoAddBitmap "caso_04_add_bitmap_bmp", "caso_00_base.cdr", "fonte_base.bmp", "add_bitmap", _
        "{ ""formato_origem"": ""BMP"", ""arquivo_fonte"": ""fonte_base.bmp"" }", _
        "Importa um bitmap BMP no documento base (mesma imagem do caso_01, formato de origem diferente)."

    Caso05_RemoveBitmap
    Caso06_MoveBitmap

    CasoAddBitmap "caso_07_bitmap_dpi_096", "caso_00_base.cdr", "fonte_dpi096.jpg", "bitmap_dpi", _
        "{ ""formato_origem"": ""JPEG"", ""arquivo_fonte"": ""fonte_dpi096.jpg"", ""dpi"": 96, ""pixels"": ""400x400"" }", _
        "Importa JPEG de 400x400 px a 96 DPI. Comparar com caso_08 (mesmos pixels, 300 DPI) para isolar o efeito do DPI."

    CasoAddBitmap "caso_08_bitmap_dpi_300", "caso_00_base.cdr", "fonte_dpi300.jpg", "bitmap_dpi", _
        "{ ""formato_origem"": ""JPEG"", ""arquivo_fonte"": ""fonte_dpi300.jpg"", ""dpi"": 300, ""pixels"": ""400x400"" }", _
        "Importa JPEG de 400x400 px a 300 DPI. Comparar com caso_07 (mesmos pixels, 96 DPI) para isolar o efeito do DPI."

    Caso09_NovaLayer
    Caso10_AlteraCor
    Caso11_Texto
    Caso12_DoisObjetos
    Caso13_Grupo
    Caso14_SegundaPagina
    Caso15_PowerClip

    LogMsg "Fim da geracao: " & m_ok & " casos OK, " & m_falhas & " falhas"
    MsgBox "Geracao concluida." & Chr$(13) & Chr$(10) & _
           "Casos OK: " & m_ok & Chr$(13) & Chr$(10) & _
           "Falhas:   " & m_falhas & Chr$(13) & Chr$(10) & _
           "Pasta:    " & PASTA_SAIDA & Chr$(13) & Chr$(10) & _
           "Detalhes em log_geracao.txt", MB_INFO, "Gerador ZCF"
    Exit Sub

TrataErroFatal:
    LogMsg "ERRO FATAL: #" & Err.Number & " - " & Err.Description
    MsgBox "Erro fatal na geracao: " & Err.Description, MB_ERRO, "Gerador ZCF"
End Sub

'==========================================================================
' PREPARACAO
'==========================================================================
Private Function GarantirPasta() As Boolean
    On Error GoTo Falha
    If Dir(PASTA_SAIDA, 16) = "" Then MkDir PASTA_SAIDA   ' 16 = vbDirectory
    GarantirPasta = True
    Exit Function
Falha:
    MsgBox "Nao foi possivel criar/acessar a pasta " & PASTA_SAIDA & _
           Chr$(13) & Chr$(10) & Err.Description, MB_ERRO, "Gerador ZCF"
End Function

' Cria um documento com formas coloridas e exporta as imagens-fonte que os
' casos de bitmap vao importar. Exportar do proprio Corel evita depender de
' arquivos externos e garante que a MESMA imagem exista nos 4 formatos.
Private Function GerarImagensFonte() As Boolean
    Dim doc As Document
    On Error GoTo Falha
    Set doc = CreateDocument
    doc.Unit = cdrCentimeter

    Dim r As Shape, e As Shape
    Set r = doc.ActiveLayer.CreateRectangle2(2, 2, 8, 8)
    r.Fill.ApplyUniformFill CreateCMYKColor(0, 100, 100, 0)
    Set e = doc.ActiveLayer.CreateEllipse2(7, 7, 2.5)
    e.Fill.ApplyUniformFill CreateCMYKColor(100, 40, 0, 0)

    ' Mesma imagem em 4 formatos de origem (tamanho natural da pagina)
    ExportarBitmap doc, "fonte_base.jpg", cdrJPEG, 300, 0, 0
    ExportarBitmap doc, "fonte_base.png", cdrPNG, 300, 0, 0
    ExportarBitmap doc, "fonte_base.tif", cdrTIFF, 300, 0, 0
    ExportarBitmap doc, "fonte_base.bmp", cdrBMP, 300, 0, 0

    ' Par para o teste de DPI: mesmos pixels (400x400), so o DPI difere
    ExportarBitmap doc, "fonte_dpi096.jpg", cdrJPEG, 96, 400, 400
    ExportarBitmap doc, "fonte_dpi300.jpg", cdrJPEG, 300, 400, 400

    doc.SaveAs PASTA_SAIDA & "fonte_master.cdr"
    doc.Close
    LogMsg "Imagens-fonte geradas com sucesso"
    GerarImagensFonte = True
    Exit Function
Falha:
    LogMsg "ERRO ao gerar imagens-fonte: #" & Err.Number & " - " & Err.Description
    On Error Resume Next
    If Not doc Is Nothing Then doc.Close
End Function

' Largura/altura 0 = deixar o filtro calcular pelo tamanho da pagina.
Private Sub ExportarBitmap(doc As Document, nomeArq As String, filtro As cdrFilter, dpi As Long, pxLarg As Long, pxAlt As Long)
    Dim ef As ExportFilter
    Set ef = doc.ExportBitmap(PASTA_SAIDA & nomeArq, filtro, cdrCurrentPage, cdrRGBColorImage, pxLarg, pxAlt, dpi, dpi)
    ef.Finish
    LogMsg "Exportado: " & nomeArq
End Sub

Private Function GerarCasoBase() As Boolean
    Dim doc As Document
    On Error GoTo Falha
    Set doc = CreateDocument
    doc.Unit = cdrCentimeter

    Dim r As Shape
    Set r = doc.ActiveLayer.CreateRectangle2(3, 3, 6, 4)
    r.Name = "RetanguloBase"
    r.Fill.ApplyUniformFill CreateCMYKColor(0, 100, 100, 0)

    SalvarCaso doc, "caso_00_base"
    EscreverManifesto "caso_00_base", "", "base", "{ }", _
        "Documento minimo: uma pagina com um retangulo vermelho (CMYK 0,100,100,0) chamado RetanguloBase."
    RegistrarOk "caso_00_base"
    GerarCasoBase = True
    Exit Function
Falha:
    TratarFalhaCaso doc, "caso_00_base", Err.Number, Err.Description
End Function

'==========================================================================
' CASOS DE TESTE
'==========================================================================

' Generico para os casos que so importam um bitmap sobre o base.
Private Sub CasoAddBitmap(nomeCaso As String, arqBase As String, arqFonte As String, tipoAlt As String, paramsJson As String, descricao As String)
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr(arqBase)
    doc.ActiveLayer.Import PASTA_SAIDA & arqFonte

    ' Posicao fixa para o bitmap importado (cosmetico; nao aborta o caso)
    On Error Resume Next
    doc.ActiveShape.SetPosition 1, 9
    On Error GoTo Falha

    SalvarCaso doc, nomeCaso
    EscreverManifesto nomeCaso, arqBase, tipoAlt, paramsJson, descricao
    RegistrarOk nomeCaso
    Exit Sub
Falha:
    TratarFalhaCaso doc, nomeCaso, Err.Number, Err.Description
End Sub

' Remove o bitmap do caso_01 — o resultado deve voltar a ser "parecido" com
' o base, e a comparacao caso_01 vs caso_05 mostra o que sobra de residuo.
Private Sub Caso05_RemoveBitmap()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_01_add_bitmap_jpeg.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes(Type:=cdrBitmapShape)
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "Nenhum bitmap encontrado em caso_01"
    sr(1).Delete

    SalvarCaso doc, "caso_05_remove_bitmap"
    EscreverManifesto "caso_05_remove_bitmap", "caso_01_add_bitmap_jpeg.cdr", "remove_bitmap", _
        "{ ""bitmap_removido"": ""o unico bitmap do caso_01"" }", _
        "Abre o caso_01 e apaga o bitmap. Comparar com caso_01 (o que some) e com caso_00 (que residuo fica)."
    RegistrarOk "caso_05_remove_bitmap"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_05_remove_bitmap", Err.Number, Err.Description
End Sub

Private Sub Caso06_MoveBitmap()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_01_add_bitmap_jpeg.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes(Type:=cdrBitmapShape)
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "Nenhum bitmap encontrado em caso_01"
    sr(1).Move 2, -2    ' desloca 2 cm p/ direita e 2 cm p/ baixo

    SalvarCaso doc, "caso_06_move_bitmap"
    EscreverManifesto "caso_06_move_bitmap", "caso_01_add_bitmap_jpeg.cdr", "move_bitmap", _
        "{ ""delta_x_cm"": 2, ""delta_y_cm"": -2 }", _
        "Abre o caso_01 e move o bitmap 2 cm para a direita e 2 cm para baixo. Deve mudar SO a transformacao, nao os dados de pixel."
    RegistrarOk "caso_06_move_bitmap"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_06_move_bitmap", Err.Number, Err.Description
End Sub

Private Sub Caso09_NovaLayer()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")
    doc.ActivePage.CreateLayer "CamadaTeste"

    SalvarCaso doc, "caso_09_nova_layer"
    EscreverManifesto "caso_09_nova_layer", "caso_00_base.cdr", "nova_layer", _
        "{ ""nome_layer"": ""CamadaTeste"" }", _
        "Cria uma layer vazia chamada CamadaTeste no documento base."
    RegistrarOk "caso_09_nova_layer"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_09_nova_layer", Err.Number, Err.Description
End Sub

Private Sub Caso10_AlteraCor()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes("RetanguloBase")
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "RetanguloBase nao encontrado"
    sr(1).Fill.ApplyUniformFill CreateCMYKColor(100, 0, 0, 0)

    SalvarCaso doc, "caso_10_altera_cor"
    EscreverManifesto "caso_10_altera_cor", "caso_00_base.cdr", "altera_cor", _
        "{ ""cor_antes"": ""CMYK 0,100,100,0"", ""cor_depois"": ""CMYK 100,0,0,0"" }", _
        "Muda o preenchimento do retangulo de vermelho para ciano. Nada mais muda."
    RegistrarOk "caso_10_altera_cor"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_10_altera_cor", Err.Number, Err.Description
End Sub

Private Sub Caso11_Texto()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")
    doc.ActiveLayer.CreateArtisticText 1, 9, "Teste ZCF 123"

    SalvarCaso doc, "caso_11_texto"
    EscreverManifesto "caso_11_texto", "caso_00_base.cdr", "add_texto", _
        "{ ""texto"": ""Teste ZCF 123"", ""tipo"": ""artistico"" }", _
        "Adiciona um texto artistico 'Teste ZCF 123' no documento base."
    RegistrarOk "caso_11_texto"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_11_texto", Err.Number, Err.Description
End Sub

' Adiciona uma elipse ao base. Serve de base intermediaria para os casos
' 13 (grupo) e 15 (PowerClip), isolando cada operacao de verdade.
Private Sub Caso12_DoisObjetos()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim e As Shape
    Set e = doc.ActiveLayer.CreateEllipse2(8, 8, 1.5)
    e.Name = "ElipseTeste"
    e.Fill.ApplyUniformFill CreateCMYKColor(100, 0, 100, 0)

    SalvarCaso doc, "caso_12_dois_objetos"
    EscreverManifesto "caso_12_dois_objetos", "caso_00_base.cdr", "add_objeto", _
        "{ ""objeto"": ""elipse"", ""nome"": ""ElipseTeste"", ""cor"": ""CMYK 100,0,100,0"" }", _
        "Adiciona uma elipse verde ao base. Base intermediaria dos casos 13 (grupo) e 15 (PowerClip)."
    RegistrarOk "caso_12_dois_objetos"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_12_dois_objetos", Err.Number, Err.Description
End Sub

' Mesmos dois objetos do caso_12, agrupados. Diff caso_12 vs caso_13
' isola SO o agrupamento.
Private Sub Caso13_Grupo()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_12_dois_objetos.cdr")
    doc.ActivePage.Shapes.All.Group

    SalvarCaso doc, "caso_13_grupo"
    EscreverManifesto "caso_13_grupo", "caso_12_dois_objetos.cdr", "grupo", _
        "{ ""objetos_agrupados"": [""RetanguloBase"", ""ElipseTeste""] }", _
        "Abre o caso_12 e agrupa o retangulo com a elipse. Unica diferenca em relacao ao caso_12 e o grupo."
    RegistrarOk "caso_13_grupo"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_13_grupo", Err.Number, Err.Description
End Sub

Private Sub Caso14_SegundaPagina()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")
    doc.AddPages 1

    SalvarCaso doc, "caso_14_segunda_pagina"
    EscreverManifesto "caso_14_segunda_pagina", "caso_00_base.cdr", "add_pagina", _
        "{ ""paginas_antes"": 1, ""paginas_depois"": 2 }", _
        "Adiciona uma segunda pagina (vazia) ao documento base. Espera-se um page2.dat novo dentro do ZCF."
    RegistrarOk "caso_14_segunda_pagina"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_14_segunda_pagina", Err.Number, Err.Description
End Sub

' Mesmos dois objetos do caso_12, com a elipse dentro do retangulo via
' PowerClip. Diff caso_12 vs caso_15 isola SO o PowerClip.
Private Sub Caso15_PowerClip()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_12_dois_objetos.cdr")

    Dim srE As ShapeRange, srR As ShapeRange
    Set srE = doc.ActivePage.Shapes.FindShapes("ElipseTeste")
    Set srR = doc.ActivePage.Shapes.FindShapes("RetanguloBase")
    If srE.Count = 0 Or srR.Count = 0 Then Err.Raise ERRO_CUSTOM, , "Objetos do caso_12 nao encontrados"
    srE(1).AddToPowerClip srR(1)

    SalvarCaso doc, "caso_15_powerclip"
    EscreverManifesto "caso_15_powerclip", "caso_12_dois_objetos.cdr", "powerclip", _
        "{ ""conteudo"": ""ElipseTeste"", ""recipiente"": ""RetanguloBase"" }", _
        "Abre o caso_12 e coloca a elipse dentro do retangulo via PowerClip. Unica diferenca em relacao ao caso_12."
    RegistrarOk "caso_15_powerclip"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_15_powerclip", Err.Number, Err.Description
End Sub

'==========================================================================
' INFRAESTRUTURA
'==========================================================================
Private Function AbrirCdr(nomeArquivo As String) As Document
    Set AbrirCdr = OpenDocument(PASTA_SAIDA & nomeArquivo)
    AbrirCdr.Unit = cdrCentimeter
End Function

Private Sub SalvarCaso(doc As Document, nomeCaso As String)
    doc.SaveAs PASTA_SAIDA & nomeCaso & ".cdr"
    doc.Close
End Sub

Private Sub TratarFalhaCaso(doc As Document, nomeCaso As String, numErro As Long, descErro As String)
    On Error Resume Next
    If Not doc Is Nothing Then doc.Close
    m_falhas = m_falhas + 1
    LogMsg "ERRO em " & nomeCaso & ": #" & numErro & " - " & descErro
End Sub

Private Sub RegistrarOk(nomeCaso As String)
    m_ok = m_ok + 1
    LogMsg "OK: " & nomeCaso
End Sub

' Manifesto JSON gravado ao lado de cada variante. Descricoes sem acentos
' de proposito, para evitar problemas de encoding (Print # grava em ANSI).
Private Sub EscreverManifesto(nomeCaso As String, arquivoBase As String, tipoAlt As String, paramsJson As String, descricao As String)
    Dim f As Integer
    f = FreeFile
    Open PASTA_SAIDA & nomeCaso & ".json" For Output As #f
    Print #f, "{"
    Print #f, "  ""caso"": """ & nomeCaso & ""","
    Print #f, "  ""arquivo"": """ & nomeCaso & ".cdr"","
    Print #f, "  ""arquivo_base"": """ & arquivoBase & ""","
    Print #f, "  ""tipo_alteracao"": """ & tipoAlt & ""","
    Print #f, "  ""descricao"": """ & descricao & ""","
    Print #f, "  ""parametros"": " & paramsJson & ","
    Print #f, "  ""gerado_em"": """ & Format(Now, "yyyy-mm-dd hh:nn:ss") & ""","
    Print #f, "  ""corel_versao"": """ & VersaoCorel() & """"
    Print #f, "}"
    Close #f
End Sub

Private Sub LogMsg(s As String)
    On Error Resume Next
    Dim f As Integer
    f = FreeFile
    Open PASTA_SAIDA & "log_geracao.txt" For Append As #f
    Print #f, Format(Now, "yyyy-mm-dd hh:nn:ss") & "  " & s
    Close #f
End Sub

Private Function VersaoCorel() As String
    On Error Resume Next
    VersaoCorel = "desconhecida"
    VersaoCorel = Application.VersionMajor & "." & Application.VersionMinor & " build " & Application.VersionBuild
End Function
