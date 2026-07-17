Option Explicit

'==========================================================================
' GeradorCasosZCF_1c — Fase 1c do projeto de engenharia reversa do ZCF
'
' Casos para decifrar a GEOMETRIA de objetos vetoriais em page1.dat.
'
' Contexto: a Fase 3 (parser Python) achou, dentro do "chunk" que guarda o
' retangulo RetanguloBase, uma tabela de offsets que aponta com precisao
' para o nome do objeto e para o bloco JSON de estilo (fill/outline). Logo
' apos o fim desse JSON aparecem 4 numeros em ponto flutuante (float32):
' 10.1444091796875, 9.52587890625, 1.875, 1.875 — candidatos fortes a
' geometria (posicao/tamanho), mas SEM um caso de teste que isole um
' movimento ou redimensionamento conhecido, nao da pra confirmar qual e
' qual (a mesma limitacao que motivou o par caso_07/caso_08 de DPI na
' Fase 1b, agora para geometria vetorial).
'
'   caso_22  move RetanguloBase (+5 cm X, -1 cm Y)     -> quais floats mudam?
'   caso_23  redimensiona RetanguloBase (so a largura)  -> isola tamanho de posicao
'
' Ambos partem do caso_00_base.cdr (precisa existir na PASTA_SAIDA — rode a
' Fase 1 antes desta).
'
' Compativel com CorelDRAW 2025 OEM: nenhum form, constantes numericas no
' lugar de vbXxx (48/64 no MsgBox), Chr(13) para quebra de linha.
'
' COMO USAR: cole este modulo no editor VBA (Alt+F11 > GlobalMacros >
' inserir modulo > colar) e execute a Sub GerarCasosDeTeste1c (F5).
' Log em log_geracao_1c.txt na pasta de saida.
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
Public Sub GerarCasosDeTeste1c()
    On Error GoTo TrataErroFatal
    m_ok = 0
    m_falhas = 0

    If Dir(PASTA_SAIDA & "caso_00_base.cdr") = "" Then
        MsgBox "caso_00_base.cdr nao encontrado em " & PASTA_SAIDA & Chr(13) & _
               "Rode a Fase 1 (GerarCasosDeTeste) antes.", MB_ERRO, "Gerador ZCF 1c"
        Exit Sub
    End If

    LogMsg "=================================================="
    LogMsg "Inicio da geracao Fase 1c"
    LogMsg "CorelDRAW: " & VersaoCorel()

    Caso22_MoveRetangulo
    Caso23_RedimensionaRetangulo

    LogMsg "Fim da geracao 1c: " & m_ok & " casos OK, " & m_falhas & " falhas"
    MsgBox "Geracao 1c concluida." & Chr(13) & _
           "Casos OK: " & m_ok & Chr(13) & _
           "Falhas:   " & m_falhas & Chr(13) & _
           "Pasta:    " & PASTA_SAIDA & Chr(13) & _
           "Detalhes em log_geracao_1c.txt", MB_INFO, "Gerador ZCF 1c"
    Exit Sub

TrataErroFatal:
    LogMsg "ERRO FATAL: #" & Err.Number & " - " & Err.Description
    MsgBox "Erro fatal na geracao 1c: " & Err.Description, MB_ERRO, "Gerador ZCF 1c"
End Sub

'==========================================================================
' CASOS DE TESTE
'==========================================================================

' Move o retangulo por um delta conhecido e assimetrico (X != Y, os dois
' diferentes de zero) para conseguir identificar sem ambiguidade quais
' floats correspondem a X e quais a Y.
Private Sub Caso22_MoveRetangulo()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes("RetanguloBase")
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "RetanguloBase nao encontrado"

    Dim x0 As Double, y0 As Double, w0 As Double, h0 As Double
    sr(1).GetPosition CDbl(x0), CDbl(y0)
    sr(1).GetSize CDbl(w0), CDbl(h0)

    Dim dx As Double, dy As Double
    dx = 5: dy = -1
    sr(1).Move dx, dy

    Dim x1 As Double, y1 As Double
    sr(1).GetPosition CDbl(x1), CDbl(y1)

    SalvarCaso doc, "caso_22_move_retangulo"
    EscreverManifesto "caso_22_move_retangulo", "caso_00_base.cdr", "move_objeto_vetorial", _
        "{ ""objeto"": ""RetanguloBase"", ""delta_x_cm"": " & FmtNum(dx) & ", ""delta_y_cm"": " & FmtNum(dy) & _
        ", ""posicao_antes_x_cm"": " & FmtNum(x0) & ", ""posicao_antes_y_cm"": " & FmtNum(y0) & _
        ", ""posicao_depois_x_cm"": " & FmtNum(x1) & ", ""posicao_depois_y_cm"": " & FmtNum(y1) & _
        ", ""tamanho_x_cm"": " & FmtNum(w0) & ", ""tamanho_y_cm"": " & FmtNum(h0) & " }", _
        "Abre o caso_00 e move RetanguloBase (unico objeto vetorial) por um delta conhecido " & _
        "e assimetrico. Objetivo: achar os campos de POSICAO na arvore de chunks de page1.dat, " & _
        "comparando com o caso_00 (so deve mudar posicao, nao tamanho nem estilo)."
    RegistrarOk "caso_22_move_retangulo"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_22_move_retangulo", Err.Number, Err.Description
End Sub

' Redimensiona SO a largura do retangulo, mantendo a altura, para isolar
' tamanho de posicao (GetPosition deve ficar igual ou quase igual ao
' caso_00 — SetSize normalmente mantem o canto/centro de referencia).
Private Sub Caso23_RedimensionaRetangulo()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes("RetanguloBase")
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "RetanguloBase nao encontrado"

    Dim x0 As Double, y0 As Double, w0 As Double, h0 As Double
    sr(1).GetPosition CDbl(x0), CDbl(y0)
    sr(1).GetSize CDbl(w0), CDbl(h0)

    Dim novaLargura As Double
    novaLargura = w0 + 4  ' cresce 4 cm so na largura; altura fica igual

    sr(1).SetSize novaLargura, h0

    Dim x1 As Double, y1 As Double, w1 As Double, h1 As Double
    sr(1).GetPosition CDbl(x1), CDbl(y1)
    sr(1).GetSize CDbl(w1), CDbl(h1)

    SalvarCaso doc, "caso_23_resize_retangulo"
    EscreverManifesto "caso_23_resize_retangulo", "caso_00_base.cdr", "redimensiona_objeto_vetorial", _
        "{ ""objeto"": ""RetanguloBase"", " & _
        """tamanho_antes_x_cm"": " & FmtNum(w0) & ", ""tamanho_antes_y_cm"": " & FmtNum(h0) & _
        ", ""tamanho_depois_x_cm"": " & FmtNum(w1) & ", ""tamanho_depois_y_cm"": " & FmtNum(h1) & _
        ", ""posicao_antes_x_cm"": " & FmtNum(x0) & ", ""posicao_antes_y_cm"": " & FmtNum(y0) & _
        ", ""posicao_depois_x_cm"": " & FmtNum(x1) & ", ""posicao_depois_y_cm"": " & FmtNum(y1) & " }", _
        "Abre o caso_00 e aumenta so a largura de RetanguloBase em 4 cm (altura fica igual). " & _
        "Objetivo: isolar o(s) campo(s) de TAMANHO na arvore de chunks de page1.dat, distinguindo-os " & _
        "dos campos de posicao achados no caso_22."
    RegistrarOk "caso_23_resize_retangulo"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_23_resize_retangulo", Err.Number, Err.Description
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

' Formata numero com ponto decimal fixo (evita virgula de locale pt-BR
' quebrar o JSON do manifesto).
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
    Open PASTA_SAIDA & "log_geracao_1c.txt" For Append As #f
    Print #f, Format(Now, "yyyy-mm-dd hh:nn:ss") & "  " & s
    Close #f
End Sub

Private Function VersaoCorel() As String
    On Error Resume Next
    VersaoCorel = "desconhecida"
    VersaoCorel = Application.VersionMajor & "." & Application.VersionMinor & " build " & Application.VersionBuild
End Function
