# Diff ZCF: `caso_00_base.cdr` vs `caso_14_segunda_pagina.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | `content/data/page2.dat`, `previews/page2.png` |
| Identicos | `META-INF/links.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `mimetype`, `previews/page1.png`, `previews/thumbnail.png` |
| Alterados | `META-INF/container.xml`, `META-INF/metadata.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/masterPage.dat`, `content/data/page1.dat`, `content/dataFileList.dat`, `content/root.dat`, `styles/document.cdss` |

### `content/data/page2.dat` — NOVO na variante (781 bytes)
```
           0  3f 5d 6b 10 79 09 c1 4a 8a 0e 72 1b 5f b8 20 61  ?]k.y..J..r._. a
          16  fe ff ff ff 02 00 00 00 02 00 00 00 fe ff ff ff  ................
          32  fe ff ff ff 02 00 00 00 02 00 00 00 fe ff ff ff  ................
          48  fe ff ff ff 02 00 00 00 02 00 00 00 fe ff ff ff  ................
```

### `previews/page2.png` — NOVO na variante (711 bytes)
```
           0  89 50 4e 47 0d 0a 1a 0a 00 00 00 0d 49 48 44 52  .PNG........IHDR
          16  00 00 00 b5 00 00 01 00 08 02 00 00 00 7a 41 a0  .............zA.
          32  8c 00 00 00 01 73 52 47 42 00 ae ce 1c e9 00 00  .....sRGB.......
          48  00 04 67 41 4d 41 00 00 b1 8f 0b fc 61 05 00 00  ..gAMA......a...
```

### `META-INF/container.xml` — ALTERADO (690 -> 888 bytes)

Tamanhos diferentes (delta +198). Prefixo comum: 664 bytes; sufixo comum: 26 bytes.
Miolo divergente: base [664..664) = 0 bytes, variante [664..862) = 198 bytes.

```
base (inicio do miolo):
         648  61 67 65 2f 70 6e 67 22 20 2f 3e 0a 20 20 20 20  age/png" />.    
         664  3c 2f 72 6f 6f 74 66 69 6c 65 73 3e 0a 3c 2f 63  </rootfiles>.</c
variante (inicio do miolo):
         648  61 67 65 2f 70 6e 67 22 20 2f 3e 0a 20 20 20 20  age/png" />.    
         664  20 20 20 20 3c 72 6f 6f 74 66 69 6c 65 20 63 72      <rootfile cr
         680  6c 3a 63 61 70 74 69 6f 6e 3d 22 3a 5b 50 c3 a1  l:caption=":[P..
         696  67 69 6e 61 20 32 5d 3b 62 72 3a 5b 50 c3 a1 67  gina 2];br:[P..g
         712  69 6e 61 20 32 5d 3b 22 20 63 72 6c 3a 66 69 6c  ina 2];" crl:fil
         728  65 2d 6b 69 6e 64 3d 22 70 61 67 65 22 20 63 72  e-kind="page" cr
  ... (regiao truncada; tamanho real 96 bytes)
```

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

### `color/docPalette.xml` — ALTERADO (180 -> 203 bytes)

Tamanhos diferentes (delta +23). Prefixo comum: 38 bytes; sufixo comum: 47 bytes.
Miolo divergente: base [38..133) = 95 bytes, variante [38..156) = 118 bytes.

```
base (inicio do miolo):
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  39 38 39 32 30 63 66 65 2d 62 31 31 36 2d 34 30  98920cfe-b116-40
          54  64 36 2d 39 38 35 34 2d 30 66 35 65 64 66 64 36  d6-9854-0f5edfd6
          70  66 66 36 31 22 20 6e 61 6d 65 3d 22 50 61 6c 65  ff61" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 95 bytes)
variante (inicio do miolo):
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  36 65 66 36 36 61 64 38 2d 36 38 37 64 2d 34 62  6ef66ad8-687d-4b
          54  35 32 2d 62 30 38 66 2d 61 64 65 37 37 31 36 39  52-b08f-ade77169
          70  61 37 61 31 22 20 6e 61 6d 65 3d 22 50 61 6c 65  a7a1" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/data1.dat` — ALTERADO (22357 -> 22357 bytes)

Mesmo tamanho; 2 regiao(oes) alterada(s):

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

**Regiao 2: offset 22132, 16 byte(s)**
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

### `content/data/page1.dat` — ALTERADO (1545 -> 1617 bytes)

Tamanhos diferentes (delta +72). Prefixo comum: 80 bytes; sufixo comum: 43 bytes.
Miolo divergente: base [80..1502) = 1422 bytes, variante [80..1574) = 1494 bytes.

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

### `content/dataFileList.dat` — ALTERADO (34 -> 44 bytes)

Tamanhos diferentes (delta +10). Prefixo comum: 34 bytes; sufixo comum: 0 bytes.
Miolo divergente: base [34..34) = 0 bytes, variante [34..44) = 10 bytes.

```
base (inicio do miolo):
          18  67 65 2e 64 61 74 0a 70 61 67 65 31 2e 64 61 74  ge.dat.page1.dat
variante (inicio do miolo):
          18  67 65 2e 64 61 74 0a 70 61 67 65 31 2e 64 61 74  ge.dat.page1.dat
          34  0a 70 61 67 65 32 2e 64 61 74                    .page2.dat
```

### `content/root.dat` — ALTERADO (1680 -> 2280 bytes)

Tamanhos diferentes (delta +600). Prefixo comum: 4 bytes; sufixo comum: 6 bytes.
Miolo divergente: base [4..1674) = 1670 bytes, variante [4..2274) = 2270 bytes.

```
base (inicio do miolo):
           0  52 49 46 46 88 06 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  60 01 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  `...doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           0  52 49 46 46 e0 08 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  60 01 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  `...doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
```

### `styles/document.cdss` — ALTERADO (17499 -> 17499 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 17344, 35 byte(s)**
```
base:
       17328  20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22 33        "guid": "3
       17344  39 63 66 62 64 38 65 2d 35 39 34 32 2d 34 33 66  9cfbd8e-5942-43f
       17360  31 2d 38 34 64 30 2d 36 61 34 35 66 65 37 31 66  1-84d0-6a45fe71f
       17376  64 61 63 22 2c 0a 20 20 20 20 20 20 20 20 22 6e  dac",.        "n
       17392  61 6d 65                                         ame
variante:
       17328  20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22 33        "guid": "3
       17344  38 39 30 32 34 65 39 2d 32 32 63 31 2d 34 63 33  89024e9-22c1-4c3
       17360  63 2d 61 30 63 32 2d 34 33 39 62 38 37 63 32 34  c-a0c2-439b87c24
       17376  31 39 37 22 2c 0a 20 20 20 20 20 20 20 20 22 6e  197",.        "n
       17392  61 6d 65                                         ame
```

