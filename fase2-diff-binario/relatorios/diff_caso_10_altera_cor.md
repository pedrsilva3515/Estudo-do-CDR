# Diff ZCF: `caso_00_base.cdr` vs `caso_10_altera_cor.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | — |
| Identicos | `META-INF/container.xml`, `META-INF/links.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `content/dataFileList.dat`, `mimetype` |
| Alterados | `META-INF/metadata.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/masterPage.dat`, `content/data/page1.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

### `META-INF/metadata.xml` — ALTERADO (8507 -> 8606 bytes)

Tamanhos diferentes (delta +99). Prefixo comum: 276 bytes; sufixo comum: 5435 bytes.
Miolo divergente: base [276..3072) = 2796 bytes, variante [276..3171) = 2895 bytes.

```
base (inicio do miolo):
         260  6e 74 73 2f 31 2e 31 2f 22 20 78 6d 6c 6e 73 3a  nts/1.1/" xmlns:
         276  63 64 72 69 6e 66 6f 3d 22 68 74 74 70 3a 2f 2f  cdrinfo="http://
         292  6e 61 6d 65 73 70 61 63 65 2e 63 6f 72 65 6c 2e  namespace.corel.
         308  63 6f 6d 2f 63 64 72 2f 6d 65 74 61 64 61 74 61  com/cdr/metadata
         324  2f 31 2e 30 2f 66 69 6c 65 69 6e 66 6f 2f 22 20  /1.0/fileinfo/" 
         340  78 6d 6c 6e 73 3a 63 72 6c 3d 22 68 74 74 70 3a  xmlns:crl="http:
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
         260  6e 74 73 2f 31 2e 31 2f 22 20 78 6d 6c 6e 73 3a  nts/1.1/" xmlns:
         276  78 6d 70 4d 4d 3d 22 68 74 74 70 3a 2f 2f 6e 73  xmpMM="http://ns
         292  2e 61 64 6f 62 65 2e 63 6f 6d 2f 78 61 70 2f 31  .adobe.com/xap/1
         308  2e 30 2f 6d 6d 2f 22 20 78 6d 6c 6e 73 3a 63 64  .0/mm/" xmlns:cd
         324  72 69 6e 66 6f 3d 22 68 74 74 70 3a 2f 2f 6e 61  rinfo="http://na
         340  6d 65 73 70 61 63 65 2e 63 6f 72 65 6c 2e 63 6f  mespace.corel.co
  ... (regiao truncada; tamanho real 96 bytes)
```

### `color/docPalette.xml` — ALTERADO (180 -> 237 bytes)

Tamanhos diferentes (delta +57). Prefixo comum: 38 bytes; sufixo comum: 33 bytes.
Miolo divergente: base [38..147) = 109 bytes, variante [38..204) = 166 bytes.

```
base (inicio do miolo):
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  39 38 39 32 30 63 66 65 2d 62 31 31 36 2d 34 30  98920cfe-b116-40
          54  64 36 2d 39 38 35 34 2d 30 66 35 65 64 66 64 36  d6-9854-0f5edfd6
          70  66 66 36 31 22 20 6e 61 6d 65 3d 22 50 61 6c 65  ff61" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  64 36 36 61 39 33 39 38 2d 39 65 39 39 2d 34 33  d66a9398-9e99-43
          54  34 65 2d 61 63 37 34 2d 37 65 65 35 38 63 62 37  4e-ac74-7ee58cb7
          70  35 31 33 66 22 20 6e 61 6d 65 3d 22 50 61 6c 65  513f" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/data1.dat` — ALTERADO (22357 -> 22357 bytes)

Mesmo tamanho; 3 regiao(oes) alterada(s):

**Regiao 1: offset 22, 1 byte(s)**
```
base:
           6  00 00 00 00 00 00 20 0b 20 00 90 51 2d 00 0f 00  ...... . ..Q-...
          22  01 00 01 00 00 00 00 00 00 00 00 00 01 00 00 00  ................
          38  01                                               .
variante:
           6  00 00 00 00 00 00 20 0b 20 00 90 51 2d 00 0f 00  ...... . ..Q-...
          22  00 00 01 00 00 00 00 00 00 00 00 00 01 00 00 00  ................
          38  01                                               .
```

**Regiao 2: offset 22011, 50 byte(s)**
```
base:
       21995  00 00 00 00 01 00 00 00 60 09 00 00 10 00 00 00  ........`.......
       22011  4c dd e2 be ac c8 d1 45 94 41 e9 1c f5 2e 7e b3  L......E.A....~.
       22027  14 05 00 00 4d 00 00 00 01 00 14 05 00 00 3b 00  ....M.........;.
       22043  00 00 01 0c 00 00 00 02 00 05 00 00 00 00 00 00  ................
       22059  64 64 00 07 10 00 00 00 00 00 00 00 00 00 00 00  dd..............
       22075  00 00                                            ..
variante:
       21995  00 00 00 00 01 00 00 00 60 09 00 00 10 00 00 00  ........`.......
       22011  7f 98 a3 1b 94 a0 a6 4d ba c2 2a 5d 0b 0e 80 ad  .......M..*]....
       22027  14 05 00 00 4d 00 00 00 01 00 14 05 00 00 3b 00  ....M.........;.
       22043  00 00 01 0c 00 00 00 02 00 05 00 00 00 00 00 64  ...............d
       22059  00 00 00 07 10 00 00 00 00 00 00 00 00 00 00 00  ................
       22075  00 00                                            ..
```

**Regiao 3: offset 22132, 16 byte(s)**
```
base:
       22116  00 00 00 00 01 00 00 00 0b 00 00 00 10 00 00 00  ................
       22132  77 7e 11 42 26 74 22 43 89 f2 13 d8 4f 27 35 5c  w~.B&t"C....O'5\
       22148  03 00 00 00 04 00 00 00 40 4b 4c 00 02 00 00 00  ........@KL.....
variante:
       22116  00 00 00 00 01 00 00 00 0b 00 00 00 10 00 00 00  ................
       22132  47 95 32 cf 29 bd ba 4d a1 9a 20 98 fe 2f a9 41  G.2.)..M.. ../.A
       22148  03 00 00 00 04 00 00 00 40 4b 4c 00 02 00 00 00  ........@KL.....
```

### `content/data/masterPage.dat` — ALTERADO (541 -> 577 bytes)

Tamanhos diferentes (delta +36). Prefixo comum: 80 bytes; sufixo comum: 81 bytes.
Miolo divergente: base [80..460) = 380 bytes, variante [80..496) = 416 bytes.

```
base (inicio do miolo):
          64  97 8c 6f e0 db 4e 13 48 9e 4e dc 4e d7 20 cc 7b  ..o..N.H.N.N. .{
          80  8f 00 00 00 04 00 00 00 14 00 00 00 28 00 00 00  ............(...
          96  0c 00 00 00 38 00 00 00 48 00 00 00 4c 00 00 00  ....8...H...L...
         112  77 00 00 00 8f 00 00 00 e8 03 00 00 d0 07 00 00  w...............
         128  81 3e 00 00 72 9c 00 00 07 3e 37 bd 5d 1f 46 45  .>..r....>7.].FE
         144  9e b3 c9 53 cc ad ac 05 02 00 00 00 01 0c 00 00  ...S............
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          64  97 8c 6f e0 db 4e 13 48 9e 4e dc 4e d7 20 cc 7b  ..o..N.H.N.N. .{
          80  9b 00 00 00 05 00 00 00 14 00 00 00 2c 00 00 00  ............,...
          96  0c 00 00 00 40 00 00 00 50 00 00 00 54 00 00 00  ....@...P...T...
         112  58 00 00 00 83 00 00 00 9b 00 00 00 e8 03 00 00  X...............
         128  d0 07 00 00 e0 2e 00 00 81 3e 00 00 72 9c 00 00  .........>..r...
         144  07 3e 37 bd 5d 1f 46 45 9e b3 c9 53 cc ad ac 05  .>7.].FE...S....
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/page1.dat` — ALTERADO (1545 -> 1615 bytes)

Tamanhos diferentes (delta +70). Prefixo comum: 80 bytes; sufixo comum: 43 bytes.
Miolo divergente: base [80..1502) = 1422 bytes, variante [80..1572) = 1492 bytes.

```
base (inicio do miolo):
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  6f 00 00 00 03 00 00 00 14 00 00 00 24 00 00 00  o...........$...
          96  0c 00 00 00 30 00 00 00 40 00 00 00 44 00 00 00  ....0...@...D...
         112  6f 00 00 00 d0 07 00 00 81 3e 00 00 72 9c 00 00  o........>..r...
         128  07 3e 37 bd 5d 1f 46 45 9e b3 c9 53 cc ad ac 05  .>7.].FE...S....
         144  02 00 00 00 01 0c 00 00 00 05 00 05 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  7b 00 00 00 04 00 00 00 14 00 00 00 28 00 00 00  {...........(...
          96  0c 00 00 00 38 00 00 00 48 00 00 00 4c 00 00 00  ....8...H...L...
         112  50 00 00 00 7b 00 00 00 d0 07 00 00 e0 2e 00 00  P...{...........
         128  81 3e 00 00 72 9c 00 00 07 3e 37 bd 5d 1f 46 45  .>..r....>7.].FE
         144  9e b3 c9 53 cc ad ac 05 02 00 00 00 00 00 00 00  ...S............
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/root.dat` — ALTERADO (1680 -> 1680 bytes)

Mesmo tamanho; 11 regiao(oes) alterada(s):

**Regiao 1: offset 624, 1 byte(s)**
```
base:
         608  6c 67 6f 62 6c 6f 64 61 10 00 00 00 01 00 00 00  lgobloda........
         624  8f 00 00 00 50 00 00 00 00 00 00 00 4c 49 53 54  ....P.......LIST
         640  58                                               X
variante:
         608  6c 67 6f 62 6c 6f 64 61 10 00 00 00 01 00 00 00  lgobloda........
         624  9b 00 00 00 50 00 00 00 00 00 00 00 4c 49 53 54  ....P.......LIST
         640  58                                               X
```

**Regiao 2: offset 688, 37 byte(s)**
```
base:
         672  73 70 69 64 10 00 00 00 01 00 00 00 10 00 00 00  spid............
         688  df 00 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
         704  6c 67 6f 62 6c 6f 64 61 10 00 00 00 01 00 00 00  lgobloda........
         720  8d 00 00 00 ef 00 00 00 00 00 00 00 4c 49 53 54  ............LIST
         736  58 00 00 00 6c                                   X...l
variante:
         672  73 70 69 64 10 00 00 00 01 00 00 00 10 00 00 00  spid............
         688  eb 00 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
         704  6c 67 6f 62 6c 6f 64 61 10 00 00 00 01 00 00 00  lgobloda........
         720  99 00 00 00 fb 00 00 00 00 00 00 00 4c 49 53 54  ............LIST
         736  58 00 00 00 6c                                   X...l
```

**Regiao 3: offset 760, 61 byte(s)**
```
base:
         744  66 6c 67 73 10 00 00 00 ff ff ff ff 04 00 00 00  flgs............
         760  1a 01 01 98 00 00 00 00 73 70 69 64 10 00 00 00  ........spid....
         776  01 00 00 00 10 00 00 00 7c 01 00 00 00 00 00 00  ........|.......
         792  4c 49 53 54 1c 00 00 00 6c 67 6f 62 6c 6f 64 61  LIST....lgobloda
         808  10 00 00 00 01 00 00 00 91 00 00 00 8c 01 00 00  ................
         824  00 00 00 00 4c 49 53 54 4c 03 00 00 70           ....LISTL...p
variante:
         744  66 6c 67 73 10 00 00 00 ff ff ff ff 04 00 00 00  flgs............
         760  5a 01 01 98 00 00 00 00 73 70 69 64 10 00 00 00  Z.......spid....
         776  01 00 00 00 10 00 00 00 94 01 00 00 00 00 00 00  ................
         792  4c 49 53 54 1c 00 00 00 6c 67 6f 62 6c 6f 64 61  LIST....lgobloda
         808  10 00 00 00 01 00 00 00 9d 00 00 00 a4 01 00 00  ................
         824  00 00 00 00 4c 49 53 54 4c 03 00 00 70           ....LISTL...p
```

**Regiao 4: offset 1032, 1 byte(s)**
```
base:
        1016  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1032  6f 00 00 00 50 00 00 00 00 00 00 00 4c 49 53 54  o...P.......LIST
        1048  58                                               X
variante:
        1016  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1032  7b 00 00 00 50 00 00 00 00 00 00 00 4c 49 53 54  {...P.......LIST
        1048  58                                               X
```

**Regiao 5: offset 1096, 37 byte(s)**
```
base:
        1080  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1096  bf 00 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
        1112  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1128  63 00 00 00 cf 00 00 00 00 00 00 00 4c 49 53 54  c...........LIST
        1144  58 00 00 00 6c                                   X...l
variante:
        1080  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1096  cb 00 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
        1112  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1128  6f 00 00 00 db 00 00 00 00 00 00 00 4c 49 53 54  o...........LIST
        1144  58 00 00 00 6c                                   X...l
```

**Regiao 6: offset 1192, 37 byte(s)**
```
base:
        1176  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1192  32 01 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  2.......LIST....
        1208  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1224  8f 00 00 00 42 01 00 00 00 00 00 00 4c 49 53 54  ....B.......LIST
        1240  54 01 00 00 6c                                   T...l
variante:
        1176  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1192  4a 01 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  J.......LIST....
        1208  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1224  9b 00 00 00 5a 01 00 00 00 00 00 00 4c 49 53 54  ....Z.......LIST
        1240  54 01 00 00 6c                                   T...l
```

**Regiao 7: offset 1288, 38 byte(s)**
```
base:
        1272  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1288  d1 01 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
        1304  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1320  7d 00 00 00 e1 01 00 00 00 00 00 00 4c 49 53 54  }...........LIST
        1336  f4 00 00 00 6f 62                                ....ob
variante:
        1272  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1288  f5 01 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
        1304  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1320  89 00 00 00 05 02 00 00 00 00 00 00 4c 49 53 54  ............LIST
        1336  f4 00 00 00 6f 62                                ....ob
```

**Regiao 8: offset 1408, 49 byte(s)**
```
base:
        1392  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1408  5e 02 00 00 00 00 00 00 62 62 6f 78 10 00 00 00  ^.......bbox....
        1424  02 00 00 00 10 00 00 00 6e 02 00 00 00 00 00 00  ........n.......
        1440  6f 62 62 78 10 00 00 00 02 00 00 00 20 00 00 00  obbx........ ...
        1456  7e 02 00 00 00 00 00 00 75 73 64 6e 10 00 00 00  ~.......usdn....
        1472  ff                                               .
variante:
        1392  73 70 69 64 10 00 00 00 02 00 00 00 10 00 00 00  spid............
        1408  8e 02 00 00 00 00 00 00 62 62 6f 78 10 00 00 00  ........bbox....
        1424  02 00 00 00 10 00 00 00 9e 02 00 00 00 00 00 00  ................
        1440  6f 62 62 78 10 00 00 00 02 00 00 00 20 00 00 00  obbx........ ...
        1456  ae 02 00 00 00 00 00 00 75 73 64 6e 10 00 00 00  ........usdn....
        1472  ff                                               .
```

**Regiao 9: offset 1512, 29 byte(s)**
```
base:
        1496  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1512  68 02 00 00 9e 02 00 00 00 00 00 00 66 74 69 6c  h...........ftil
        1528  10 00 00 00 02 00 00 00 30 00 00 00 06 05 00 00  ........0.......
        1544  00 00 00 00 4c 49 53 54 1c 00 00 00 74           ....LIST....t
variante:
        1496  6c 67 6f 62 6c 6f 64 61 10 00 00 00 02 00 00 00  lgobloda........
        1512  72 02 00 00 ce 02 00 00 00 00 00 00 66 74 69 6c  r...........ftil
        1528  10 00 00 00 02 00 00 00 30 00 00 00 40 05 00 00  ........0...@...
        1544  00 00 00 00 4c 49 53 54 1c 00 00 00 74           ....LIST....t
```

**Regiao 10: offset 1576, 1 byte(s)**
```
base:
        1560  74 72 66 64 10 00 00 00 02 00 00 00 60 00 00 00  trfd........`...
        1576  36 05 00 00 00 00 00 00 4c 49 53 54 58 00 00 00  6.......LISTX...
        1592  6c                                               l
variante:
        1560  74 72 66 64 10 00 00 00 02 00 00 00 60 00 00 00  trfd........`...
        1576  70 05 00 00 00 00 00 00 4c 49 53 54 58 00 00 00  p.......LISTX...
        1592  6c                                               l
```

**Regiao 11: offset 1612, 61 byte(s)**
```
base:
        1596  66 6c 67 73 10 00 00 00 ff ff ff ff 04 00 00 00  flgs............
        1612  1a 01 01 98 00 00 00 00 73 70 69 64 10 00 00 00  ........spid....
        1628  02 00 00 00 10 00 00 00 96 05 00 00 00 00 00 00  ................
        1644  4c 49 53 54 1c 00 00 00 6c 67 6f 62 6c 6f 64 61  LIST....lgobloda
        1660  10 00 00 00 02 00 00 00 63 00 00 00 a6 05 00 00  ........c.......
        1676  00 00 00 00                                      ....
variante:
        1596  66 6c 67 73 10 00 00 00 ff ff ff ff 04 00 00 00  flgs............
        1612  5a 01 01 98 00 00 00 00 73 70 69 64 10 00 00 00  Z.......spid....
        1628  02 00 00 00 10 00 00 00 d0 05 00 00 00 00 00 00  ................
        1644  4c 49 53 54 1c 00 00 00 6c 67 6f 62 6c 6f 64 61  LIST....lgobloda
        1660  10 00 00 00 02 00 00 00 6f 00 00 00 e0 05 00 00  ........o.......
        1676  00 00 00 00                                      ....
```

### `previews/page1.png` — ALTERADO (829 -> 843 bytes)

Tamanhos diferentes (delta +14). Prefixo comum: 86 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [86..817) = 731 bytes, variante [86..831) = 745 bytes.

```
base (inicio do miolo):
          70  00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00 02  ..........o.d...
          86  d2 49 44 41 54 78 5e ed d2 3b 4a 43 01 14 45 51  .IDATx^..;JC..EQ
         102  c7 14 21 7e 50 10 3b 5b ed b4 13 67 e2 a7 d0 42  ..!~P.;[...g...B
         118  51 04 a7 a0 e0 24 74 20 8e c0 2e 90 22 85 b6 12  Q....$t ...."...
         134  70 07 e4 15 0f 59 8b 53 dd ea 16 7b ed 0b 7e b7  p....Y.S...{..~.
         150  b6 7c 80 1f f4 41 d1 07 45 1f 14 7d 50 f4 41 d1  .|...A..E..}P.A.
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          70  00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00 02  ..........o.d...
          86  e0 49 44 41 54 78 5e ed d2 31 4a 9b 01 18 c7 e1  .IDATx^..1J.....
         102  0c 8e 5e a0 9b d7 a8 56 11 ba 74 75 d5 a1 88 43  ..^....V..tu...C
         118  6f e0 01 d2 4d 5a 69 a2 43 4f d0 41 0b 5e 22 17  o...MZi.CO.A.^".
         134  f1 04 5d 02 19 32 e8 2a 81 fe 02 e1 1b 3e e4 79  ..]..2.*.....>.y
         150  f8 4f ef f4 0e bf c9 0b fc df 64 f3 00 6f e8 83  .O........d..o..
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (935 -> 946 bytes)

Tamanhos diferentes (delta +11). Prefixo comum: 86 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [86..923) = 837 bytes, variante [86..934) = 848 bytes.

```
base (inicio do miolo):
          70  00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00 03  ..........o.d...
          86  3c 49 44 41 54 78 5e ed d4 41 11 c2 30 00 00 41  <IDATx^..A..0..A
         102  34 a5 6d ea b4 62 0a 96 f0 c0 07 06 07 b9 cf ce  4.m..b..........
         118  ac 86 7d 9c fb 01 b0 de e3 dc 8f 6b 9b f7 00 58  ..}........k...X
         134  e4 da e6 77 9f d7 98 ef 71 02 ac f1 1c f6 01 0a  ...w....q.......
         150  f6 01 1a f6 01 1a f6 01 1a f6 01 1a f6 01 1a f6  ................
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          70  00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00 03  ..........o.d...
          86  47 49 44 41 54 78 5e ed d4 31 0d c2 50 00 40 c1  GIDATx^..1..P.@.
         102  2a a0 7b 75 d0 60 ac 32 0a 63 6d 20 a0 a0 09 0b  *.{u.`.2.cm ....
         118  2c 24 38 f8 6f b9 e4 34 dc 74 bb ae 00 e3 4d b7  ,$8.o..4.t....M.
         134  eb ba 6c c7 bc 9f 00 63 2c db f1 db e7 f2 78 4f  ..l....c,.....xO
         150  cf 0f c0 18 f3 fd 65 1f 20 60 1f a0 61 1f a0 61  ......e. `..a..a
  ... (regiao truncada; tamanho real 96 bytes)
```

### `styles/document.cdss` — ALTERADO (17499 -> 17499 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 17343, 36 byte(s)**
```
base:
       17327  20 20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22         "guid": "
       17343  33 39 63 66 62 64 38 65 2d 35 39 34 32 2d 34 33  39cfbd8e-5942-43
       17359  66 31 2d 38 34 64 30 2d 36 61 34 35 66 65 37 31  f1-84d0-6a45fe71
       17375  66 64 61 63 22 2c 0a 20 20 20 20 20 20 20 20 22  fdac",.        "
       17391  6e 61 6d 65                                      name
variante:
       17327  20 20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22         "guid": "
       17343  35 65 61 37 65 39 36 35 2d 33 33 30 31 2d 34 65  5ea7e965-3301-4e
       17359  63 62 2d 38 37 38 35 2d 62 33 30 38 35 63 33 30  cb-8785-b3085c30
       17375  31 66 35 66 22 2c 0a 20 20 20 20 20 20 20 20 22  1f5f",.        "
       17391  6e 61 6d 65                                      name
```

