Attribute VB_Name = "LeitorPedidos"
' Leitor de Pedidos CDR - macro para o CorelDRAW 2025 (versao 26)
'
' Abre a janela do Leitor de Pedidos: analisa o arquivo aberto (a analise roda
' fora do Corel, pela pasta Documentos\Estudo-do-CDR) e, ao clicar num item,
' seleciona no desenho a peca que o programa interpretou.
'
' Restricoes deste VBA: sem constantes vbXxx (usar numeros) e Chr(13) no lugar
' de vbCrLf. Unidade cdrCentimeter = 4 (conferido na biblioteca do Corel 26).
Option Explicit

Private mFormas As ShapeRange
Private mEsq() As Double, mDir() As Double, mBase() As Double, mTopo() As Double
Private mN As Long
Private mDx As Double, mDy As Double

Public Sub AbrirLeitorPedidos()
    frmLeitor.Show 0
End Sub

Public Function PastaProjeto() As String
    PastaProjeto = Environ("USERPROFILE") & "\Documents\Estudo-do-CDR"
End Function

Private Function ArquivoResultado() As String
    ArquivoResultado = Environ("TEMP") & "\leitor_corel_resultado.txt"
End Function

' Chama scripts\ponte_corel.bat (analise ou gravacao). Devolve False se o .bat nao existe.
Private Function RodarPonte(ByVal arg1 As String, ByVal arg2 As String, ByVal modo As String) As Boolean
    Dim bat As String, comando As String
    bat = PastaProjeto() & "\scripts\ponte_corel.bat"
    If Dir(bat) = "" Then Exit Function
    comando = "cmd /c " & Chr(34) & Chr(34) & bat & Chr(34) & " " & Chr(34) & arg1 & Chr(34) _
        & " " & Chr(34) & arg2 & Chr(34) & " " & modo & Chr(34)
    CreateObject("WScript.Shell").Run comando, 0, True
    RodarPonte = True
End Function

' Roda a analise (fora do Corel) e devolve as linhas do resultado.
Public Function RodarAnalise(ByVal caminho As String, ByVal modo As String) As Collection
    Dim linhas As New Collection
    Dim saida As String, f As Integer, linha As String

    saida = ArquivoResultado()
    If Dir(saida) <> "" Then Kill saida
    If Not RodarPonte(caminho, saida, modo) Then
        linhas.Add "ERRO" & Chr(9) & "Nao encontrei " & PastaProjeto() & "\scripts\ponte_corel.bat"
        Set RodarAnalise = linhas
        Exit Function
    End If

    If Dir(saida) = "" Then
        linhas.Add "ERRO" & Chr(9) & "A analise nao gerou resultado."
    Else
        f = FreeFile
        Open saida For Input As #f
        Do While Not EOF(f)
            Line Input #f, linha
            If Len(linha) > 0 Then linhas.Add linha
        Loop
        Close #f
    End If
    Set RodarAnalise = linhas
End Function

' Grava a correcao como pacote de revisao (mesmo formato do aplicativo).
' Devolve "OK<TAB>caminho do pacote" ou "ERRO<TAB>mensagem".
Public Function SalvarCorrecao(ByVal cdr As String, ByVal conteudo As String) As String
    Dim arq As String, resposta As String, f As Integer, linha As String
    arq = Environ("TEMP") & "\leitor_corel_correcao.txt"
    resposta = arq & ".ok"
    If Dir(resposta) <> "" Then Kill resposta
    f = FreeFile
    Open arq For Output As #f
    Print #f, "ORIGINAL" & Chr(9) & ArquivoResultado() & ".json"
    Print #f, conteudo
    Close #f
    If Not RodarPonte(cdr, arq, "salvar") Then
        SalvarCorrecao = "ERRO" & Chr(9) & "Nao encontrei " & PastaProjeto() & "\scripts\ponte_corel.bat"
        Exit Function
    End If
    If Dir(resposta) = "" Then
        SalvarCorrecao = "ERRO" & Chr(9) & "A gravacao nao respondeu."
        Exit Function
    End If
    f = FreeFile
    Open resposta For Input As #f
    Line Input #f, linha
    Close #f
    SalvarCorrecao = linha
End Function

' Le a selecao atual do Corel: caixa (cm, nas coordenadas da analise) e a lista
' dos objetos (StaticID:tipo). Devolve quantos objetos estao selecionados.
Public Function LerSelecao(ByRef e As Double, ByRef d As Double, ByRef b As Double, ByRef t As Double, _
                           ByRef objs As String) As Long
    Dim sr As ShapeRange, unidade As Long, i As Long
    Set sr = ActiveSelectionRange
    If sr Is Nothing Then Exit Function
    If sr.Count = 0 Then Exit Function
    unidade = ActiveDocument.Unit
    ActiveDocument.Unit = 4
    e = sr.LeftX - mDx: d = sr.RightX - mDx
    b = sr.BottomY - mDy: t = sr.TopY - mDy
    objs = ""
    For i = 1 To sr.Count
        objs = objs & CStr(sr(i).StaticID) & ":" & CStr(sr(i).Type) & ";"
    Next i
    ActiveDocument.Unit = unidade
    LerSelecao = sr.Count
End Function

' Guarda a caixa (em cm) de todos os objetos da pagina, inclusive dentro de grupos.
Public Sub CarregarFormas()
    Dim unidade As Long, i As Long, s As Shape
    unidade = ActiveDocument.Unit
    ActiveDocument.Unit = 4
    Set mFormas = ActivePage.Shapes.FindShapes()
    mN = mFormas.Count
    ReDim mEsq(1 To mN + 1): ReDim mDir(1 To mN + 1)
    ReDim mBase(1 To mN + 1): ReDim mTopo(1 To mN + 1)
    For i = 1 To mN
        Set s = mFormas(i)
        mEsq(i) = s.LeftX: mDir(i) = s.RightX
        mBase(i) = s.BottomY: mTopo(i) = s.TopY
    Next i
    ActiveDocument.Unit = unidade
End Sub

' As coordenadas da analise tem origem no centro da pagina; as do Corel dependem
' da origem do documento. Descobre o deslocamento comparando pecas de mesma medida.
Public Sub CalibrarDeslocamento(e() As Double, d() As Double, b() As Double, t() As Double, _
                                tem() As Boolean, ByVal n As Long)
    Dim votos As Object, valores As Object, c As Variant, par As Variant
    Dim k As Long, i As Long, chave As String, melhor As String, maior As Long
    Dim unidade As Long
    Set votos = CreateObject("Scripting.Dictionary")
    Set valores = CreateObject("Scripting.Dictionary")

    For k = 1 To n
        If tem(k) Then
            For i = 1 To mN
                If Abs((mDir(i) - mEsq(i)) - (d(k) - e(k))) < 0.15 And Abs((mTopo(i) - mBase(i)) - (t(k) - b(k))) < 0.15 Then
                    chave = CStr(Round(mEsq(i) - e(k), 1)) & "|" & CStr(Round(mBase(i) - b(k), 1))
                    If votos.Exists(chave) Then
                        votos(chave) = votos(chave) + 1
                    Else
                        votos.Add chave, 1
                        valores.Add chave, Array(mEsq(i) - e(k), mBase(i) - b(k))
                    End If
                End If
            Next i
        End If
    Next k

    maior = 0
    For Each c In votos.Keys
        If votos(c) > maior Then maior = votos(c): melhor = CStr(c)
    Next c
    If maior > 0 Then
        par = valores.Item(melhor)
        mDx = par(0)
        mDy = par(1)
    Else
        unidade = ActiveDocument.Unit
        ActiveDocument.Unit = 4
        mDx = ActivePage.SizeWidth / 2
        mDy = ActivePage.SizeHeight / 2
        ActiveDocument.Unit = unidade
    End If
End Sub

' Seleciona os objetos que formam a peca da regiao (coordenadas da analise, em cm).
' Devolve quantos objetos foram selecionados.
Public Function SelecionarRegiao(ByVal e As Double, ByVal d As Double, ByVal b As Double, ByVal t As Double) As Long
    Const TOL As Double = 0.3
    Dim dentro As Object, i As Long, p As Shape, q As Shape, ancestralDentro As Boolean
    Dim faixa As ShapeRange

    e = e + mDx: d = d + mDx: b = b + mDy: t = t + mDy
    Set dentro = CreateObject("Scripting.Dictionary")
    For i = 1 To mN
        If mEsq(i) >= e - TOL And mDir(i) <= d + TOL And mBase(i) >= b - TOL And mTopo(i) <= t + TOL Then
            dentro(CStr(mFormas(i).StaticID)) = i
        End If
    Next i

    ' Fica so com os objetos de fora: se o grupo inteiro esta na regiao, seleciona o grupo.
    Set faixa = CreateShapeRange
    For i = 1 To mN
        If dentro.Exists(CStr(mFormas(i).StaticID)) Then
            ancestralDentro = False
            On Error Resume Next
            Set p = Nothing
            Set p = mFormas(i).ParentGroup
            Do While Not p Is Nothing
                If dentro.Exists(CStr(p.StaticID)) Then ancestralDentro = True: Exit Do
                Set q = Nothing
                Set q = p.ParentGroup
                Set p = q
            Loop
            On Error GoTo 0
            If Not ancestralDentro Then faixa.Add mFormas(i)
        End If
    Next i

    If faixa.Count > 0 Then
        faixa.CreateSelection
        ActiveWindow.ActiveView.ToFitShapeRange faixa
    End If
    SelecionarRegiao = faixa.Count
End Function
