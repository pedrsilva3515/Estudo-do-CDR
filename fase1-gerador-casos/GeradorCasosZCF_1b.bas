Option Explicit

'==========================================================================
' GeradorCasosZCF_1b — Fase 1b do projeto de engenharia reversa do ZCF
'
' Casos extras para fechar as hipoteses abertas na Fase 2:
'   H1 (registro RI aninhado / multiplos bitmaps por arquivo)
'   H2 (24 bitmaps vs 4 registros UI + JPEGs embutidos no helo.cdr)
'
'   caso_16  dois bitmaps DIFERENTES        -> quantos registros UI?
'   caso_17  o MESMO bitmap duplicado 2x    -> deduplicacao?
'   caso_18  JPEG grande (2400x2400)        -> original preservado como JPEG?
'   caso_19  bitmap CMYK (TIFF)             -> bpp/stride no cabecalho
'   caso_20  bitmap com transparencia (PNG) -> 32 bpp / canal alfa
'   caso_21  foto real (OPCIONAL)           -> coloque uma foto de camera
'            chamada foto_real.jpg na pasta de saida antes de rodar;
'            se nao existir, o caso e pulado sem erro.
'
' PRE-REQUISITO: os arquivos da Fase 1 (caso_00_base.cdr e
' caso_01_add_bitmap_jpeg.cdr) precisam existir na PASTA_SAIDA.
'
' Compativel com CorelDRAW 2025 OEM: nenhum form, constantes numericas no
' lugar de vbXxx (48/64 no MsgBox, 16 no Dir, Chr(13) para quebra de linha).
'
' COMO USAR: cole este modulo no editor VBA (Alt+F11 > GlobalMacros >
' inserir modulo > colar) e execute a Sub GerarCasosDeTeste1b (F5).
' Log em log_geracao_1b.txt na pasta de saida.
'==========================================================================

' Mesma pasta usada na Fase 1. Mantenha a barra invertida no final.
Private Const PASTA_SAIDA As String = "C:\CDR_Testes\"

Private Const MB_ERRO As Long = 48      ' vbExclamation
Private Const MB_INFO As Long = 64      ' vbInformation
Private Const ERRO_CUSTOM As Long = 60001

Private m_ok As Long
Private m_falhas As Long
Private m_pulados As Long

'==========================================================================
' PONTO DE ENTRADA
'==========================================================================
Public Sub GerarCasosDeTeste1b()
    On Error GoTo TrataErroFatal
    m_ok = 0
    m_falhas = 0
    m_pulados = 0

    ' Pre-requisitos da Fase 1
    If Dir(PASTA_SAIDA, 16) = "" Then
        MsgBox "Pasta " & PASTA_SAIDA & " nao encontrada. Rode a Fase 1 antes.", MB_ERRO, "Gerador ZCF 1b"
        Exit Sub
    End If
    If Dir(PASTA_SAIDA & "caso_00_base.cdr") = "" Or Dir(PASTA_SAIDA & "caso_01_add_bitmap_jpeg.cdr") = "" Then
        MsgBox "caso_00_base.cdr e/ou caso_01_add_bitmap_jpeg.cdr nao encontrados em " & _
               PASTA_SAIDA & Chr(13) & "Rode a Fase 1 (GerarCasosDeTeste) antes.", MB_ERRO, "Gerador ZCF 1b"
        Exit Sub
    End If

    LogMsg "=================================================="
    LogMsg "Inicio da geracao Fase 1b"
    LogMsg "CorelDRAW: " & VersaoCorel()

    If Not GerarImagensFonte1b() Then
        MsgBox "Falha ao gerar as imagens-fonte da Fase 1b. Veja log_geracao_1b.txt em " & PASTA_SAIDA, MB_ERRO, "Gerador ZCF 1b"
        Exit Sub
    End If

    Caso16_DoisBitmapsDiferentes
    Caso17_BitmapDuplicado
    Caso18_JpegGrande
    Caso19_BitmapCmyk
    Caso20_BitmapAlpha
    Caso21_FotoReal

    LogMsg "Fim da geracao 1b: " & m_ok & " casos OK, " & m_falhas & " falhas, " & m_pulados & " pulados"
    MsgBox "Geracao 1b concluida." & Chr(13) & _
           "Casos OK: " & m_ok & Chr(13) & _
           "Falhas:   " & m_falhas & Chr(13) & _
           "Pulados:  " & m_pulados & Chr(13) & _
           "Pasta:    " & PASTA_SAIDA & Chr(13) & _
           "Detalhes em log_geracao_1b.txt", MB_INFO, "Gerador ZCF 1b"
    Exit Sub

TrataErroFatal:
    LogMsg "ERRO FATAL: #" & Err.Number & " - " & Err.Description
    MsgBox "Erro fatal na geracao 1b: " & Err.Description, MB_ERRO, "Gerador ZCF 1b"
End Sub

'==========================================================================
' IMAGENS-FONTE DA FASE 1b
'==========================================================================
' Composicao DIFERENTE da fonte_base da Fase 1 (cores e formas trocadas),
' para os casos que precisam de uma segunda imagem distinta.
Private Function GerarImagensFonte1b() As Boolean
    Dim doc As Document
    On Error GoTo Falha
    Set doc = CreateDocument
    doc.Unit = cdrCentimeter

    Dim r As Shape, e1 As Shape, e2 As Shape
    Set r = doc.ActiveLayer.CreateRectangle2(2, 2, 8, 8)
    r.Fill.ApplyUniformFill CreateCMYKColor(0, 0, 100, 0)      ' amarelo
    Set e1 = doc.ActiveLayer.CreateEllipse2(5, 7, 2.5)
    e1.Fill.ApplyUniformFill CreateCMYKColor(0, 100, 0, 0)     ' magenta
    Set e2 = doc.ActiveLayer.CreateEllipse2(8, 4, 1.2)
    e2.Fill.ApplyUniformFill CreateCMYKColor(100, 0, 0, 0)     ' ciano

    ' Degrade no retangulo deixa a imagem menos "chapada" (mais proxima de
    ' foto para fins de compressao). Se a build nao aceitar, segue uniforme.
    On Error Resume Next
    r.Fill.ApplyFountainFill CreateCMYKColor(0, 0, 100, 0), CreateCMYKColor(100, 100, 0, 0)
    If Err.Number <> 0 Then LogMsg "Aviso: ApplyFountainFill falhou (#" & Err.Number & "), retangulo ficou uniforme"
    On Error GoTo Falha

    ' Segunda imagem distinta, mesmo tamanho natural da fonte_base
    ExportarBitmap doc, "fonte_alt.jpg", cdrJPEG, cdrRGBColorImage, 300, 0, 0

    ' JPEG grande: 2400x2400 px (~5,8 MPixel) para testar se imagem grande
    ' muda o modo de armazenamento (H2)
    ExportarBitmap doc, "fonte_grande.jpg", cdrJPEG, cdrRGBColorImage, 300, 2400, 2400

    ' TIFF CMYK: testa cabecalho com espaco de cor CMYK (32 bits/pixel)
    ExportarBitmap doc, "fonte_cmyk.tif", cdrTIFF, cdrCMYKColorImage, 300, 0, 0

    ' PNG com transparencia: fundo da pagina fica transparente -> canal alfa
    ExportarBitmapAlpha doc, "fonte_alpha.png", cdrPNG, cdrRGBColorImage, 300, 0, 0

    doc.SaveAs PASTA_SAIDA & "fonte_master_1b.cdr"
    doc.Close
    LogMsg "Imagens-fonte 1b geradas com sucesso"
    GerarImagensFonte1b = True
    Exit Function
Falha:
    LogMsg "ERRO ao gerar imagens-fonte 1b: #" & Err.Number & " - " & Err.Description
    On Error Resume Next
    If Not doc Is Nothing Then doc.Close
End Function

' Mesma chamada de 8 argumentos que funcionou na Fase 1.
Private Sub ExportarBitmap(doc As Document, nomeArq As String, filtro As cdrFilter, tipoImg As cdrImageType, dpi As Long, pxLarg As Long, pxAlt As Long)
    Dim ef As ExportFilter
    Set ef = doc.ExportBitmap(PASTA_SAIDA & nomeArq, filtro, cdrCurrentPage, tipoImg, pxLarg, pxAlt, dpi, dpi)
    ef.Finish
    LogMsg "Exportado: " & nomeArq
End Sub

' Variante com os 3 argumentos extras (antialiasing, dithered, TRANSPARENT)
' para gerar PNG com canal alfa. Se a assinatura nao bater na sua build,
' o log vai acusar erro aqui — me avise que eu ajusto.
Private Sub ExportarBitmapAlpha(doc As Document, nomeArq As String, filtro As cdrFilter, tipoImg As cdrImageType, dpi As Long, pxLarg As Long, pxAlt As Long)
    Dim ef As ExportFilter
    Set ef = doc.ExportBitmap(PASTA_SAIDA & nomeArq, filtro, cdrCurrentPage, tipoImg, pxLarg, pxAlt, dpi, dpi, cdrNormalAntiAliasing, False, True)
    ef.Finish
    LogMsg "Exportado (com alfa): " & nomeArq
End Sub

'==========================================================================
' CASOS DE TESTE 1b
'==========================================================================

' Dois bitmaps DIFERENTES no mesmo documento. Diff contra caso_01 isola a
' adicao do 2o bitmap: aparece um 2o registro UI? Como o 1o se desloca?
Private Sub Caso16_DoisBitmapsDiferentes()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_01_add_bitmap_jpeg.cdr")
    doc.ActiveLayer.Import PASTA_SAIDA & "fonte_alt.jpg"
    On Error Resume Next
    doc.ActiveShape.SetPosition 8, 9
    On Error GoTo Falha

    SalvarCaso doc, "caso_16_dois_bitmaps_diferentes"
    EscreverManifesto "caso_16_dois_bitmaps_diferentes", "caso_01_add_bitmap_jpeg.cdr", "add_segundo_bitmap", _
        "{ ""formato_origem"": ""JPEG"", ""arquivo_fonte"": ""fonte_alt.jpg"", ""observacao"": ""imagem DIFERENTE da ja presente"" }", _
        "Abre o caso_01 e importa uma segunda imagem, diferente da primeira. Testa multiplos registros UI no Bitmaps.dat (H1/H2)."
    RegistrarOk "caso_16_dois_bitmaps_diferentes"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_16_dois_bitmaps_diferentes", Err.Number, Err.Description
End Sub

' O MESMO bitmap duplicado dentro do documento. Se o Bitmaps.dat NAO
' crescer, ha deduplicacao (explicaria os 24 bitmaps vs 4 UI do helo).
Private Sub Caso17_BitmapDuplicado()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_01_add_bitmap_jpeg.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes(Type:=cdrBitmapShape)
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "Nenhum bitmap encontrado em caso_01"
    sr(1).Duplicate 2, -2

    SalvarCaso doc, "caso_17_bitmap_duplicado"
    EscreverManifesto "caso_17_bitmap_duplicado", "caso_01_add_bitmap_jpeg.cdr", "duplica_bitmap", _
        "{ ""operacao"": ""Duplicate"", ""delta_x_cm"": 2, ""delta_y_cm"": -2 }", _
        "Abre o caso_01 e duplica o bitmap existente. Se Bitmaps.dat nao crescer, ha deduplicacao de imagens (H2)."
    RegistrarOk "caso_17_bitmap_duplicado"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_17_bitmap_duplicado", Err.Number, Err.Description
End Sub

' JPEG grande importado no base. Testa se imagem grande e' armazenada de
' outro modo (JPEG embutido, como visto no helo.cdr) em vez de raw.
Private Sub Caso18_JpegGrande()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")
    doc.ActiveLayer.Import PASTA_SAIDA & "fonte_grande.jpg"
    On Error Resume Next
    doc.ActiveShape.SetPosition 1, 9
    On Error GoTo Falha

    SalvarCaso doc, "caso_18_jpeg_grande"
    EscreverManifesto "caso_18_jpeg_grande", "caso_00_base.cdr", "add_bitmap_grande", _
        "{ ""formato_origem"": ""JPEG"", ""arquivo_fonte"": ""fonte_grande.jpg"", ""pixels"": ""2400x2400"" }", _
        "Importa JPEG de 2400x2400 px no base. Testa se imagens grandes sao guardadas como JPEG embutido em vez de raw (H2)."
    RegistrarOk "caso_18_jpeg_grande"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_18_jpeg_grande", Err.Number, Err.Description
End Sub

Private Sub Caso19_BitmapCmyk()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")
    doc.ActiveLayer.Import PASTA_SAIDA & "fonte_cmyk.tif"
    On Error Resume Next
    doc.ActiveShape.SetPosition 1, 9
    On Error GoTo Falha

    SalvarCaso doc, "caso_19_bitmap_cmyk"
    EscreverManifesto "caso_19_bitmap_cmyk", "caso_00_base.cdr", "add_bitmap_cmyk", _
        "{ ""formato_origem"": ""TIFF"", ""arquivo_fonte"": ""fonte_cmyk.tif"", ""espaco_cor"": ""CMYK"" }", _
        "Importa TIFF CMYK no base. Comparar cabecalho do Bitmaps.dat (bpp/stride/campos de cor) com o caso RGB (caso_03)."
    RegistrarOk "caso_19_bitmap_cmyk"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_19_bitmap_cmyk", Err.Number, Err.Description
End Sub

Private Sub Caso20_BitmapAlpha()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")
    doc.ActiveLayer.Import PASTA_SAIDA & "fonte_alpha.png"
    On Error Resume Next
    doc.ActiveShape.SetPosition 1, 9
    On Error GoTo Falha

    SalvarCaso doc, "caso_20_bitmap_alpha"
    EscreverManifesto "caso_20_bitmap_alpha", "caso_00_base.cdr", "add_bitmap_alpha", _
        "{ ""formato_origem"": ""PNG"", ""arquivo_fonte"": ""fonte_alpha.png"", ""canal_alfa"": true }", _
        "Importa PNG com transparencia no base. Comparar bpp/stride do cabecalho com o caso sem alfa (caso_02)."
    RegistrarOk "caso_20_bitmap_alpha"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_20_bitmap_alpha", Err.Number, Err.Description
End Sub

' OPCIONAL: se voce colocar uma foto real de camera/celular chamada
' foto_real.jpg na pasta de saida, este caso a importa no base — e o teste
' mais fiel ao cenario do helo.cdr (fotos grandes). Sem o arquivo, e pulado.
Private Sub Caso21_FotoReal()
    Dim doc As Document
    On Error GoTo Falha
    If Dir(PASTA_SAIDA & "foto_real.jpg") = "" Then
        m_pulados = m_pulados + 1
        LogMsg "PULADO: caso_21_foto_real (foto_real.jpg nao encontrada na pasta — opcional)"
        Exit Sub
    End If

    Set doc = AbrirCdr("caso_00_base.cdr")
    doc.ActiveLayer.Import PASTA_SAIDA & "foto_real.jpg"
    On Error Resume Next
    doc.ActiveShape.SetPosition 1, 9
    On Error GoTo Falha

    SalvarCaso doc, "caso_21_foto_real"
    EscreverManifesto "caso_21_foto_real", "caso_00_base.cdr", "add_foto_real", _
        "{ ""formato_origem"": ""JPEG"", ""arquivo_fonte"": ""foto_real.jpg"", ""observacao"": ""foto real fornecida manualmente"" }", _
        "Importa uma foto real (JPEG de camera) no base. Cenario mais proximo do helo.cdr para testar JPEG embutido (H2)."
    RegistrarOk "caso_21_foto_real"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_21_foto_real", Err.Number, Err.Description
End Sub

'==========================================================================
' INFRAESTRUTURA (mesmos padroes validados na Fase 1)
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
    Open PASTA_SAIDA & "log_geracao_1b.txt" For Append As #f
    Print #f, Format(Now, "yyyy-mm-dd hh:nn:ss") & "  " & s
    Close #f
End Sub

Private Function VersaoCorel() As String
    On Error Resume Next
    VersaoCorel = "desconhecida"
    VersaoCorel = Application.VersionMajor & "." & Application.VersionMinor & " build " & Application.VersionBuild
End Function
