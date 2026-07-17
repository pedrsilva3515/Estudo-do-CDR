Option Explicit

'==========================================================================
' GeradorCasosZCF_1d — Fase 1d do projeto de engenharia reversa do ZCF
'
' Continuacao da decifragem de geometria vetorial em page1.dat (ver
' docs/descobertas-fase3-page1.md, secoes P5/P6). Ja confirmado: a unidade
' e 100.000 unidades/cm, e a geometria de RetanguloBase vive numa regiao
' fixa perto do offset 16 do arquivo (3 blocos de 16 bytes: [X, flag=2,
' campo?, Y]), fora do "chunk nomeado" do objeto. Duas hipoteses fortes
' ficaram em aberto por falta de caso de teste:
'
'   H-Bezier: o campo "Y" de cada bloco reagiu a um resize de LARGURA
'   (nao so a movimento em Y) por ~1/3 do delta — condizente com ponto de
'   controle de curva Bezier cubica (regra 1/3-2/3), nao posicao pura.
'   Se estiver certa, um resize de ALTURA deveria mexer no campo "X" de
'   forma simetrica (~1/3 do delta de altura), nao no campo Y.
'
'   H-Segundo-objeto: nao se sabe se cada objeto tem sua PROPRIA regiao de
'   3 blocos, nem onde ela fica (logo apos a do primeiro objeto? em outro
'   lugar determinado pela ordem de criacao?).
'
' Nao investigado ainda: onde fica a ROTACAO de um objeto.
'
'   caso_24  redimensiona RetanguloBase (so a ALTURA, +4cm)  -> testa H-Bezier simetrico
'   caso_25  rotaciona RetanguloBase em 30 graus              -> localiza rotacao
'   caso_26  cria um SEGUNDO retangulo nomeado, em posicao conhecida -> testa H-Segundo-objeto
'
' Todos partem do caso_00_base.cdr (precisa existir na PASTA_SAIDA).
'
' Compativel com CorelDRAW 2025 OEM: nenhum form, constantes numericas no
' lugar de vbXxx (48/64 no MsgBox), Chr(13) para quebra de linha.
' LICAO DA FASE 1c: GetPosition/GetSize recebem os parametros SEM CDbl() —
' CDbl(x) cria um valor temporario e nao recebe o ByRef de volta, o que
' zerou os manifestos da rodada anterior. Aqui os parametros vao direto.
'
' COMO USAR: cole este modulo no editor VBA (Alt+F11 > GlobalMacros >
' inserir modulo > colar) e execute a Sub GerarCasosDeTeste1d (F5).
' Log em log_geracao_1d.txt na pasta de saida.
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
Public Sub GerarCasosDeTeste1d()
    On Error GoTo TrataErroFatal
    m_ok = 0
    m_falhas = 0

    If Dir(PASTA_SAIDA & "caso_00_base.cdr") = "" Then
        MsgBox "caso_00_base.cdr nao encontrado em " & PASTA_SAIDA & Chr(13) & _
               "Rode a Fase 1 (GerarCasosDeTeste) antes.", MB_ERRO, "Gerador ZCF 1d"
        Exit Sub
    End If

    LogMsg "=================================================="
    LogMsg "Inicio da geracao Fase 1d"
    LogMsg "CorelDRAW: " & VersaoCorel()

    Caso24_RedimensionaAltura
    Caso25_RotacionaRetangulo
    Caso26_SegundoRetangulo

    LogMsg "Fim da geracao 1d: " & m_ok & " casos OK, " & m_falhas & " falhas"
    MsgBox "Geracao 1d concluida." & Chr(13) & _
           "Casos OK: " & m_ok & Chr(13) & _
           "Falhas:   " & m_falhas & Chr(13) & _
           "Pasta:    " & PASTA_SAIDA & Chr(13) & _
           "Detalhes em log_geracao_1d.txt", MB_INFO, "Gerador ZCF 1d"
    Exit Sub

TrataErroFatal:
    LogMsg "ERRO FATAL: #" & Err.Number & " - " & Err.Description
    MsgBox "Erro fatal na geracao 1d: " & Err.Description, MB_ERRO, "Gerador ZCF 1d"
End Sub

'==========================================================================
' CASOS DE TESTE
'==========================================================================

' Redimensiona SO a altura (espelha o caso_23 da Fase 1c, que mexeu so na
' largura, com o MESMO delta de 4cm) para testar se o campo "X" reage de
' forma simetrica (~1/3 do delta) — confirmaria a hipotese de ponto de
' controle de curva Bezier para os dois eixos.
Private Sub Caso24_RedimensionaAltura()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes("RetanguloBase")
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "RetanguloBase nao encontrado"

    Dim x0 As Double, y0 As Double, w0 As Double, h0 As Double
    sr(1).GetPosition x0, y0
    sr(1).GetSize w0, h0

    Dim novaAltura As Double
    novaAltura = h0 + 4  ' mesmo delta (4cm) do caso_23, mas no eixo oposto

    sr(1).SetSize w0, novaAltura

    Dim x1 As Double, y1 As Double, w1 As Double, h1 As Double
    sr(1).GetPosition x1, y1
    sr(1).GetSize w1, h1

    SalvarCaso doc, "caso_24_resize_altura"
    EscreverManifesto "caso_24_resize_altura", "caso_00_base.cdr", "redimensiona_objeto_vetorial", _
        "{ ""objeto"": ""RetanguloBase"", ""eixo"": ""altura"", " & _
        """tamanho_antes_x_cm"": " & FmtNum(w0) & ", ""tamanho_antes_y_cm"": " & FmtNum(h0) & _
        ", ""tamanho_depois_x_cm"": " & FmtNum(w1) & ", ""tamanho_depois_y_cm"": " & FmtNum(h1) & _
        ", ""posicao_antes_x_cm"": " & FmtNum(x0) & ", ""posicao_antes_y_cm"": " & FmtNum(y0) & _
        ", ""posicao_depois_x_cm"": " & FmtNum(x1) & ", ""posicao_depois_y_cm"": " & FmtNum(y1) & " }", _
        "Abre o caso_00 e aumenta so a ALTURA de RetanguloBase em 4cm (mesmo delta do caso_23, " & _
        "eixo oposto). Objetivo: testar se o campo X reage a ~1/3 do delta, espelhando o que o " & _
        "campo Y fez no caso_23 (hipotese de ponto de controle Bezier)."
    RegistrarOk "caso_24_resize_altura"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_24_resize_altura", Err.Number, Err.Description
End Sub

' Rotaciona o retangulo em torno do proprio centro por um angulo conhecido,
' sem mover nem redimensionar — isola rotacao de posicao/tamanho.
Private Sub Caso25_RotacionaRetangulo()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim sr As ShapeRange
    Set sr = doc.ActivePage.Shapes.FindShapes("RetanguloBase")
    If sr.Count = 0 Then Err.Raise ERRO_CUSTOM, , "RetanguloBase nao encontrado"

    Dim x0 As Double, y0 As Double, w0 As Double, h0 As Double
    sr(1).GetPosition x0, y0
    sr(1).GetSize w0, h0

    Dim angulo As Double
    angulo = 30  ' graus, sentido anti-horario (padrao CorelDRAW)
    sr(1).Rotate angulo

    SalvarCaso doc, "caso_25_rotaciona_retangulo"
    EscreverManifesto "caso_25_rotaciona_retangulo", "caso_00_base.cdr", "rotaciona_objeto_vetorial", _
        "{ ""objeto"": ""RetanguloBase"", ""angulo_graus"": " & FmtNum(angulo) & _
        ", ""tamanho_x_cm"": " & FmtNum(w0) & ", ""tamanho_y_cm"": " & FmtNum(h0) & _
        ", ""posicao_x_cm"": " & FmtNum(x0) & ", ""posicao_y_cm"": " & FmtNum(y0) & " }", _
        "Abre o caso_00 e rotaciona RetanguloBase em 30 graus em torno do proprio centro, sem " & _
        "mover nem redimensionar. Objetivo: localizar onde a rotacao e armazenada em page1.dat."
    RegistrarOk "caso_25_rotaciona_retangulo"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_25_rotaciona_retangulo", Err.Number, Err.Description
End Sub

' Cria um SEGUNDO retangulo nomeado, em posicao e tamanho conhecidos e
' distintos do primeiro, sem mover o RetanguloBase original. Objetivo:
' descobrir se cada objeto tem sua propria regiao de "3 blocos" e onde
' ela fica em relacao a do primeiro objeto.
Private Sub Caso26_SegundoRetangulo()
    Dim doc As Document
    On Error GoTo Falha
    Set doc = AbrirCdr("caso_00_base.cdr")

    Dim r2 As Shape
    Set r2 = doc.ActiveLayer.CreateRectangle2(12, 12, 15, 14)
    r2.Name = "RetanguloDois"
    r2.Fill.ApplyUniformFill CreateCMYKColor(0, 0, 100, 0)  ' amarelo, cor distinta

    Dim x2 As Double, y2 As Double, w2 As Double, h2 As Double
    r2.GetPosition x2, y2
    r2.GetSize w2, h2

    SalvarCaso doc, "caso_26_segundo_retangulo"
    EscreverManifesto "caso_26_segundo_retangulo", "caso_00_base.cdr", "add_segundo_objeto_vetorial", _
        "{ ""objeto_novo"": ""RetanguloDois"", ""cor"": ""CMYK 0,0,100,0"", " & _
        """posicao_x_cm"": " & FmtNum(x2) & ", ""posicao_y_cm"": " & FmtNum(y2) & _
        ", ""tamanho_x_cm"": " & FmtNum(w2) & ", ""tamanho_y_cm"": " & FmtNum(h2) & _
        ", ""objeto_original_inalterado"": ""RetanguloBase"" }", _
        "Abre o caso_00 e cria um SEGUNDO retangulo nomeado (RetanguloDois), em posicao e cor " & _
        "distintas, sem alterar RetanguloBase. Objetivo: achar a regiao de geometria do segundo " & _
        "objeto e ver onde fica em relacao a do primeiro."
    RegistrarOk "caso_26_segundo_retangulo"
    Exit Sub
Falha:
    TratarFalhaCaso doc, "caso_26_segundo_retangulo", Err.Number, Err.Description
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
    Open PASTA_SAIDA & "log_geracao_1d.txt" For Append As #f
    Print #f, Format(Now, "yyyy-mm-dd hh:nn:ss") & "  " & s
    Close #f
End Sub

Private Function VersaoCorel() As String
    On Error Resume Next
    VersaoCorel = "desconhecida"
    VersaoCorel = Application.VersionMajor & "." & Application.VersionMinor & " build " & Application.VersionBuild
End Function
