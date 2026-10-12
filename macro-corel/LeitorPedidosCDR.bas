Attribute VB_Name = "LeitorPedidosCDR"
' Envia o documento ativo para o Leitor de pedidos CDR.
' Instalado por instalar-leitor-pedidos.ps1, que cria o ambiente em
' %LOCALAPPDATA%\LeitorPedidosCDR.

Option Explicit

Private Function PastaInstalacao() As String
    PastaInstalacao = Environ("LOCALAPPDATA") & "\LeitorPedidosCDR"
End Function

Sub AnalisarPedidoAtivo()
    If ActiveDocument Is Nothing Then
        MsgBox "Nenhum documento aberto.", 0
        Exit Sub
    End If

    Dim doc As Document
    Set doc = ActiveDocument

    If doc.FullFileName = "" Then
        MsgBox "Salve o documento antes de analisar o pedido.", 0
        Exit Sub
    End If

    If doc.Dirty Then
        If MsgBox("O documento tem alterações não salvas." & Chr(13) & _
                  "Salvar agora para analisar a versão atual?", 4) = 6 Then
            doc.Save
        End If
    End If

    Dim pythonw As String
    pythonw = PastaInstalacao() & "\venv\Scripts\pythonw.exe"
    If Dir(pythonw) = "" Then
        MsgBox "Leitor de pedidos não encontrado em:" & Chr(13) & pythonw & Chr(13) & Chr(13) & _
               "Execute novamente o instalar-leitor-pedidos.ps1.", 0
        Exit Sub
    End If

    Shell """" & pythonw & """ -m zcfreader.gui """ & doc.FullFileName & """", 1
End Sub
