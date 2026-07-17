Option Explicit

'==========================================================================
' GeradorCasosZCF_1e — Fase 1e do projeto de engenharia reversa do ZCF
'
' Teste decisivo para a hipotese P8 (docs/descobertas-fase3-page1.md):
' a regiao de "3 blocos de 16 bytes" no offset 16 de page1.dat parece ser
' um CACHE do ultimo objeto transformado (mover/redimensionar/rotacionar),
' nao um registro fixo por objeto — porque RetanguloDois (criado no
' caso_26, nunca transformado) nao apareceu em lugar nenhum do arquivo
' com sua propria versao dessa regiao.
'
' Este caso cria os DOIS retangulos (RetanguloBase, como sempre, e um
' segundo objeto) e MOVE O SEGUNDO, no lugar do primeiro. Se a hipotese
' do cache estiver certa, a regiao do offset 16 deve passar a refletir o
' SEGUNDO objeto (nao mais o RetanguloBase). Se nao mudar nada, ou mudar
' de outro jeito, a hipotese cai.
'
'   caso_27  cria RetanguloDois e move ELE (nao o RetanguloBase)
'
' Parte do caso_00_base.cdr (precisa existir na PASTA_SAIDA).
'
' Compativel com CorelDRAW 2025 OEM: nenhum form, constantes numericas no
' lugar de vbXxx (48/64 no MsgBox), Chr(13) para quebra de linha.
' GetPosition/GetSize recebem os parametros SEM CDbl() (licao da Fase 1c).
'
' COMO USAR: cole este modulo no editor VBA (Alt+F11 > GlobalMacros >
' inserir modulo > colar) e execute a Sub GerarCasosDeTeste1e (F5).
' Log em log_geracao_1e.txt na pasta de saida.
'==========================================================================

Private Const PASTA_SAIDA As String = "C:\CDR_Testes\"

Private Const MB_ERRO As Long = 48      ' vbExclamation
Private Const MB_INFO As Long = 64      ' vbInformation
Private Const ERRO_CUSTOM As Long = 60001

Private m_ok As Long
Private m_falhas As Long

'==========================================================================
' PONTO DE ENTRADA
'==========================================================================
Public Sub GerarCasosDeTeste1e()
    On Error GoTo TrataErroFatal
    m_ok = 0
    m_falhas = 0

    If Dir(PASTA_SAIDA & "caso_00_base.cdr") = "" Then
        MsgBox "caso_00_base.cdr nao encontrado em " & PASTA_SAIDA & Chr(13) & _
               "Rode a Fase 1 (GerarCasosDeTeste) antes.", MB_ERRO, "Gerador ZCF 1e"
        Exit Sub
    End If

    LogMsg "=================================================="
    LogMsg "Inicio da geracao Fase 1e"
    LogMsg "CorelDRAW: " & VersaoCorel()

    Caso27_MoveSegundoRetangulo

    LogMsg "Fim da geracao 1e: " & m_ok & " casos OK, " & m_falhas & " falhas"
    MsgBox "Geracao 1e concluida." & Chr(13) & _
           "Casos OK: " & m_ok & Chr(13) & _
           "Falhas:   " & m_falhas & Chr(13) & _
           "Pasta:    " & PASTA_SAIDA & Chr(13) & _
           "Detalhes em log_geracao_1e.txt", MB_INFO, "Gerador ZCF 1e"
    Exit Sub

TrataErroFatal:
    LogMsg "ERRO FATAL: #" & Err.Number & " - " & Err.Description
    MsgBox "Erro fatal na geracao 1e: " & Err.Description, MB_ERRO, "Gerador ZCF 1e"
End Sub

'==========================================================================
' CASO DE TESTE
'==========================================================================

' Cria um segundo retangulo (igual ao caso_26) e MOVE ELE por um delta
' conhecido, deixando RetanguloBase parado. Teste decisivo da hipotese
' P8: a regiao de "3 blocos" deve seguir o objeto TRANSFORMADO POR ULTIMO,
' nao um indice fixo de objeto.
Private Sub Caso27_MoveSegundoRetangulo()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim r2 As Shape
    Set r2 = doc.ActiveLayer.CreateRectangle2(12, 12, 15, 14)
    r2.Name = "RetanguloDois"
    r2.Fill.ApplyUniformFill CreateCMYKColor(0, 0, 100, 0)  ' amarelo

    Dim x2_0 As Double, y2_0 As Double, w2_0 As Double, h2_0 As Double
    r2.GetPosition x2_0, y2_0
    r2.GetSize w2_0, h2_0

    Dim dx As Double, dy As Double
    dx = 7: dy = -3  ' delta diferente do caso_22, para nao confundir com o outro objeto
    r2.Move dx, dy

    Dim x2_1 As Double, y2_1 As Double
    r2.GetPosition x2_1, y2_1

    ' confirma que RetanguloBase NAO se moveu
    Dim srBase As ShapeRange
    Set srBase = doc.ActivePage.Shapes.FindShapes("RetanguloBase")
    Dim xBase As Double, yBase As Double
    If srBase.Count > 0 Then srBase(1).GetPosition xBase, yBase

    SalvarCaso doc, "caso_27_move_segundo_retangulo"
    EscreverManifesto "caso_27_move_segundo_retangulo", "caso_00_base.cdr", "move_segundo_objeto_vetorial", _
        "{ ""objeto_movido"": ""RetanguloDois"", ""delta_x_cm"": " & FmtNum(dx) & ", ""delta_y_cm"": " & FmtNum(dy) & _
        ", ""posicao_antes_x_cm"": " & FmtNum(x2_0) & ", ""posicao_antes_y_cm"": " & FmtNum(y2_0) & _
        ", ""posicao_depois_x_cm"": " & FmtNum(x2_1) & ", ""posicao_depois_y_cm"": " & FmtNum(y2_1) & _
        ", ""tamanho_x_cm"": " & FmtNum(w2_0) & ", ""tamanho_y_cm"": " & FmtNum(h2_0) & _
        ", ""retangulo_base_posicao_x_cm"": " & FmtNum(xBase) & ", ""retangulo_base_posicao_y_cm"": " & FmtNum(yBase) & _
        ", ""objeto_nao_movido"": ""RetanguloBase"" }", _
        "Abre o caso_00, cria RetanguloDois (igual ao caso_26) e move SO ELE por um delta " & _
        "conhecido, deixando RetanguloBase parado. Teste decisivo: a regiao de 'geometria em " & _
        "cache' no offset 16 de page1.dat deve passar a refletir RetanguloDois, nao mais " & _
        "RetanguloBase, se a hipotese de 'cache do ultimo objeto transformado' estiver certa."
    RegistrarOk "caso_27_move_segundo_retangulo"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_27_move_segundo_retangulo", Err.Number, Err.Description
End Sub

'==========================================================================
' INFRAESTRUTURA (mesmos padroes validados nas fases anteriores)
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

Private Function FmtNum(v As Double) As String
    Dim s As String
    s = CStr(v)
    s = Replace(s, ",", ".")
    FmtNum = s
End Function

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
    Open PASTA_SAIDA & "log_geracao_1e.txt" For Append As #f
    Print #f, Format(Now, "yyyy-mm-dd hh:nn:ss") & "  " & s
    Close #f
End Sub

Private Function VersaoCorel() As String
    On Error Resume Next
    VersaoCorel = "desconhecida"
    VersaoCorel = Application.VersionMajor & "." & Application.VersionMinor & " build " & Application.VersionBuild
End Function
