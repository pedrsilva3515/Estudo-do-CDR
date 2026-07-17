# Diff ZCF: `caso_00_base.cdr` vs `caso_11_texto.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | `embed/embedding0`, `font/fontTable.dat` |
| Identicos | `META-INF/links.xml`, `color/color.xml`, `content/dataFileList.dat`, `mimetype` |
| Alterados | `META-INF/container.xml`, `META-INF/metadata.xml`, `META-INF/textinfo.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/masterPage.dat`, `content/data/page1.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

### `embed/embedding0` — NOVO na variante (1048605 bytes)
```
           0  01 00 00 00 03 08 00 00 02 56 00 65 00 72 00 73  .........V.e.r.s
          16  00 69 00 6f 00 6e 00 20 00 37 00 2e 00 30 00 35  .i.o.n. .7...0.5
          32  00 00 00 5a 15 1b fd 7f 00 00 88 a9 2f 67 ac 00  ...Z......../g..
          48  00 00 00 00 00 00 00 00 00 00 ea 07 07 00 11 00  ................
```

### `font/fontTable.dat` — NOVO na variante (443 bytes)
```
           0  00 00 00 00 b3 01 00 00 03 00 00 00 00 00 00 00  ................
          16  83 00 00 00 0c 00 00 00 40 00 00 00 02 0b 06 04  ........@.......
          32  02 02 02 02 02 04 06 00 00 00 41 00 72 00 69 00  ..........A.r.i.
          48  61 00 6c 00 00 00 00 08 00 00 00 57 00 65 00 73  a.l........W.e.s
```

### `META-INF/container.xml` — ALTERADO (690 -> 690 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 397, 2 byte(s)**
```
base:
         381  6c 3a 69 6d 61 67 65 2d 77 69 64 74 68 3d 22 33  l:image-width="3
         397  38 33 22 20 66 75 6c 6c 2d 70 61 74 68 3d 22 70  83" full-path="p
         413  72 65                                            re
variante:
         381  6c 3a 69 6d 61 67 65 2d 77 69 64 74 68 3d 22 33  l:image-width="3
         397  30 38 22 20 66 75 6c 6c 2d 70 61 74 68 3d 22 70  08" full-path="p
         413  72 65                                            re
```

### `META-INF/metadata.xml` — ALTERADO (8507 -> 8796 bytes)

Tamanhos diferentes (delta +289). Prefixo comum: 276 bytes; sufixo comum: 496 bytes.
Miolo divergente: base [276..8011) = 7735 bytes, variante [276..8300) = 8024 bytes.

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

### `META-INF/textinfo.xml` — ALTERADO (673 -> 798 bytes)

Tamanhos diferentes (delta +125). Prefixo comum: 247 bytes; sufixo comum: 426 bytes.
Miolo divergente: base [247..247) = 0 bytes, variante [247..372) = 125 bytes.

```
base (inicio do miolo):
         231  22 3e 0a 20 20 20 20 20 20 20 20 20 20 20 20 3c  ">.            <
         247  4f 62 6a 65 63 74 4e 61 6d 65 73 3e 0a 20 20 20  ObjectNames>.   
variante (inicio do miolo):
         231  22 3e 0a 20 20 20 20 20 20 20 20 20 20 20 20 3c  ">.            <
         247  54 65 78 74 53 74 72 65 61 6d 3e 0a 20 20 20 20  TextStream>.    
         263  20 20 20 20 20 20 20 20 20 20 20 20 3c 54 65 78              <Tex
         279  74 52 75 6e 20 62 72 65 61 6b 3d 22 70 61 72 61  tRun break="para
         295  22 20 6c 61 6e 67 3d 22 31 30 34 36 22 3e 54 65  " lang="1046">Te
         311  73 74 65 20 5a 43 46 20 31 32 33 3c 2f 54 65 78  ste ZCF 123</Tex
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
          38  31 34 66 61 62 30 34 66 2d 64 37 31 31 2d 34 33  14fab04f-d711-43
          54  65 38 2d 61 35 39 35 2d 38 66 33 30 34 61 35 39  e8-a595-8f304a59
          70  64 36 35 61 22 20 6e 61 6d 65 3d 22 50 61 6c 65  d65a" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/data1.dat` — ALTERADO (22357 -> 24188 bytes)

Tamanhos diferentes (delta +1831). Prefixo comum: 22 bytes; sufixo comum: 3 bytes.
Miolo divergente: base [22..22354) = 22332 bytes, variante [22..24185) = 24163 bytes.

```
base (inicio do miolo):
           6  00 00 00 00 00 00 20 0b 20 00 90 51 2d 00 0f 00  ...... . ..Q-...
          22  01 00 01 00 00 00 00 00 00 00 00 00 01 00 00 00  ................
          38  01 00 00 00 40 9c 00 00 00 00 00 00 00 00 00 00  ....@...........
          54  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
          70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
          86  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           6  00 00 00 00 00 00 20 0b 20 00 90 51 2d 00 0f 00  ...... . ..Q-...
          22  00 00 01 00 00 00 00 00 00 00 00 00 01 00 00 00  ................
          38  01 00 00 00 40 9c 00 00 00 00 00 00 00 00 00 00  ....@...........
          54  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
          70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
          86  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
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

### `content/data/page1.dat` — ALTERADO (1545 -> 9649 bytes)

Tamanhos diferentes (delta +8104). Prefixo comum: 16 bytes; sufixo comum: 43 bytes.
Miolo divergente: base [16..1502) = 1486 bytes, variante [16..9606) = 9590 bytes.

```
base (inicio do miolo):
           0  ca e3 0e 25 44 cf 60 4e 93 c6 5f 71 47 19 94 06  ...%D.`N.._qG...
          16  50 8e f4 ff 02 00 00 00 02 00 00 00 e3 ea ed ff  P...............
          32  50 8e f4 ff 02 00 00 00 02 00 00 00 e3 ea ed ff  P...............
          48  68 8a f4 ff 02 00 00 00 02 00 00 00 fb e6 ed ff  h...............
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  6f 00 00 00 03 00 00 00 14 00 00 00 24 00 00 00  o...........$...
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           0  ca e3 0e 25 44 cf 60 4e 93 c6 5f 71 47 19 94 06  ...%D.`N.._qG...
          16  ab 88 f1 ff 02 00 00 00 02 00 00 00 e3 ea ed ff  ................
          32  ab 88 f1 ff 02 00 00 00 02 00 00 00 e3 ea ed ff  ................
          48  ab 88 f1 ff 02 00 00 00 02 00 00 00 fb e6 ed ff  ................
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  7b 00 00 00 04 00 00 00 14 00 00 00 28 00 00 00  {...........(...
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/root.dat` — ALTERADO (1680 -> 2160 bytes)

Tamanhos diferentes (delta +480). Prefixo comum: 4 bytes; sufixo comum: 6 bytes.
Miolo divergente: base [4..1674) = 1670 bytes, variante [4..2154) = 2150 bytes.

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
           0  52 49 46 46 68 08 00 00 43 44 52 54 66 76 65 72  RIFFh...CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  14 02 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  ....doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/page1.png` — ALTERADO (829 -> 1166 bytes)

Tamanhos diferentes (delta +337). Prefixo comum: 85 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [85..817) = 732 bytes, variante [85..1154) = 1069 bytes.

```
base (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  02 d2 49 44 41 54 78 5e ed d2 3b 4a 43 01 14 45  ..IDATx^..;JC..E
         101  51 c7 14 21 7e 50 10 3b 5b ed b4 13 67 e2 a7 d0  Q..!~P.;[...g...
         117  42 51 04 a7 a0 e0 24 74 20 8e c0 2e 90 22 85 b6  BQ....$t ...."..
         133  12 70 07 e4 15 0f 59 8b 53 dd ea 16 7b ed 0b 7e  .p....Y.S...{..~
         149  b7 b6 7c 80 1f f4 41 d1 07 45 1f 14 7d 50 f4 41  ..|...A..E..}P.A
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  04 23 49 44 41 54 78 5e ed d6 31 6f 13 67 00 80  .#IDATx^..1o.g..
         101  61 7e 53 48 70 a9 5a a9 ea d6 31 69 a6 76 ab 2c  a~SHp.Z...1i.v.,
         117  7e 01 f0 07 d2 74 68 87 02 55 a5 4e 61 ae a3 ae  ~....th..U.Na...
         133  61 0e 5d c9 ec b1 0a 33 dd d0 31 30 18 89 93 4e  a.]....3..10...N
         149  96 05 6f 10 8d d2 08 3d 8f be c1 fe ce df f9 a4  ..o....=........
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (935 -> 2823 bytes)

Tamanhos diferentes (delta +1888). Prefixo comum: 19 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [19..923) = 904 bytes, variante [19..2811) = 2792 bytes.

```
base (inicio do miolo):
           3  47 0d 0a 1a 0a 00 00 00 0d 49 48 44 52 00 00 01  G........IHDR...
          19  7f 00 00 01 00 08 02 00 00 00 d4 52 e1 24 00 00  ...........R.$..
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 03 3c 49 44 41 54 78 5e ed d4 41 11 c2 30  ...<IDATx^..A..0
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           3  47 0d 0a 1a 0a 00 00 00 0d 49 48 44 52 00 00 01  G........IHDR...
          19  34 00 00 01 00 08 02 00 00 00 b2 08 1d 73 00 00  4............s..
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 0a 9c 49 44 41 54 78 5e ed 9c bf 6e e3 56  ....IDATx^...n.V
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
       17343  64 39 32 33 36 39 64 66 2d 39 66 32 30 2d 34 62  d92369df-9f20-4b
       17359  66 31 2d 38 37 30 31 2d 65 66 61 61 37 34 34 31  f1-8701-efaa7441
       17375  36 32 36 30 22 2c 0a 20 20 20 20 20 20 20 20 22  6260",.        "
       17391  6e 61 6d 65                                      name
```

