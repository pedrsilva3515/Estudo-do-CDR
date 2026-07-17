# Diff ZCF: `caso_00_base.cdr` vs `caso_03_add_bitmap_tiff.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | `content/data/Bitmaps.dat` |
| Identicos | `META-INF/links.xml`, `mimetype` |
| Alterados | `META-INF/container.xml`, `META-INF/metadata.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/masterPage.dat`, `content/data/page1.dat`, `content/dataFileList.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

### `content/data/Bitmaps.dat` — NOVO na variante (2693386 bytes)
```
           0  01 00 00 00 01 00 00 00 55 49 00 00 02 19 29 00  ........UI....).
          16  00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00  .... ...........
          32  02 00 00 00 ff 00 00 00 52 49 e2 18 29 00 00 00  ........RI..)...
          48  00 00 4e 00 00 00 01 00 00 00 01 00 00 00 b3 03  ..N.............
```

### `META-INF/container.xml` — ALTERADO (690 -> 690 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 396, 3 byte(s)**
```
base:
         380  72 6c 3a 69 6d 61 67 65 2d 77 69 64 74 68 3d 22  rl:image-width="
         396  33 38 33 22 20 66 75 6c 6c 2d 70 61 74 68 3d 22  383" full-path="
         412  70 72 65                                         pre
variante:
         380  72 6c 3a 69 6d 61 67 65 2d 77 69 64 74 68 3d 22  rl:image-width="
         396  32 35 36 22 20 66 75 6c 6c 2d 70 61 74 68 3d 22  256" full-path="
         412  70 72 65                                         pre
```

### `META-INF/metadata.xml` — ALTERADO (8507 -> 8678 bytes)

Tamanhos diferentes (delta +171). Prefixo comum: 276 bytes; sufixo comum: 499 bytes.
Miolo divergente: base [276..8008) = 7732 bytes, variante [276..8179) = 7903 bytes.

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

### `META-INF/textinfo.xml` — ALTERADO (673 -> 725 bytes)

Tamanhos diferentes (delta +52). Prefixo comum: 353 bytes; sufixo comum: 320 bytes.
Miolo divergente: base [353..353) = 0 bytes, variante [353..405) = 52 bytes.

```
base (inicio do miolo):
         337  20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20                  
         353  3c 2f 72 64 66 3a 42 61 67 3e 0a 20 20 20 20 20  </rdf:Bag>.     
variante (inicio do miolo):
         337  20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20                  
         353  20 20 20 20 3c 72 64 66 3a 6c 69 3e 66 6f 6e 74      <rdf:li>font
         369  65 5f 62 61 73 65 2e 74 69 66 3c 2f 72 64 66 3a  e_base.tif</rdf:
         385  6c 69 3e 0a 20 20 20 20 20 20 20 20 20 20 20 20  li>.            
         401  20 20 20 20 3c 2f 72 64 66 3a 42 61 67 3e 0a 20      </rdf:Bag>. 
         417  20 20 20 20                                          
```

### `color/color.xml` — ALTERADO (251 -> 250 bytes)

Tamanhos diferentes (delta -1). Prefixo comum: 135 bytes; sufixo comum: 112 bytes.
Miolo divergente: base [135..139) = 4 bytes, variante [135..138) = 3 bytes.

```
base (inicio do miolo):
         119  3e 3c 48 61 73 52 67 62 4f 62 6a 65 63 74 73 3e  ><HasRgbObjects>
         135  66 61 6c 73 65 3c 2f 48 61 73 52 67 62 4f 62 6a  false</HasRgbObj
         151  65 63 74 73                                      ects
variante (inicio do miolo):
         119  3e 3c 48 61 73 52 67 62 4f 62 6a 65 63 74 73 3e  ><HasRgbObjects>
         135  74 72 75 65 3c 2f 48 61 73 52 67 62 4f 62 6a 65  true</HasRgbObje
         151  63 74 73                                         cts
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
          38  35 63 66 33 35 39 62 64 2d 65 30 31 62 2d 34 31  5cf359bd-e01b-41
          54  36 30 2d 39 39 36 32 2d 37 66 65 37 33 61 34 39  60-9962-7fe73a49
          70  66 36 36 62 22 20 6e 61 6d 65 3d 22 50 61 6c 65  f66b" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/data1.dat` — ALTERADO (22357 -> 22640 bytes)

Tamanhos diferentes (delta +283). Prefixo comum: 22 bytes; sufixo comum: 58 bytes.
Miolo divergente: base [22..22299) = 22277 bytes, variante [22..22582) = 22560 bytes.

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

### `content/data/page1.dat` — ALTERADO (1545 -> 2694 bytes)

Tamanhos diferentes (delta +1149). Prefixo comum: 16 bytes; sufixo comum: 43 bytes.
Miolo divergente: base [16..1502) = 1486 bytes, variante [16..2651) = 2635 bytes.

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
          16  10 81 f1 ff 02 00 00 00 02 00 00 00 a1 d6 ea ff  ................
          32  10 81 f1 ff 02 00 00 00 02 00 00 00 a1 d6 ea ff  ................
          48  10 81 f1 ff 02 00 00 00 02 00 00 00 a1 d6 ea ff  ................
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  7b 00 00 00 04 00 00 00 14 00 00 00 28 00 00 00  {...........(...
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/dataFileList.dat` — ALTERADO (34 -> 46 bytes)

Tamanhos diferentes (delta +12). Prefixo comum: 0 bytes; sufixo comum: 34 bytes.
Miolo divergente: base [0..0) = 0 bytes, variante [0..12) = 12 bytes.

```
base (inicio do miolo):
           0  64 61 74 61 31 2e 64 61 74 0a 6d 61 73 74 65 72  data1.dat.master
variante (inicio do miolo):
           0  42 69 74 6d 61 70 73 2e 64 61 74 0a 64 61 74 61  Bitmaps.dat.data
          16  31 2e 64 61 74 0a 6d 61 73 74 65 72              1.dat.master
```

### `content/root.dat` — ALTERADO (1680 -> 2004 bytes)

Tamanhos diferentes (delta +324). Prefixo comum: 4 bytes; sufixo comum: 6 bytes.
Miolo divergente: base [4..1674) = 1670 bytes, variante [4..1998) = 1994 bytes.

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
           0  52 49 46 46 cc 07 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  1c 00 00 00 62 6d 70 74 62 6d 70 20 10 00 00 00  ....bmptbmp ....
          80  00 00 00 00 0a 19 29 00 00 00 00 00 00 00 00 00  ......).........
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/page1.png` — ALTERADO (829 -> 1875 bytes)

Tamanhos diferentes (delta +1046). Prefixo comum: 85 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [85..817) = 732 bytes, variante [85..1863) = 1778 bytes.

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
          85  06 e8 49 44 41 54 78 5e ed dc cb 6b 94 57 00 86  ..IDATx^...k.W..
         101  f1 44 91 82 0b 75 a1 b8 70 69 f5 0f f8 3a ce 17  .D...u..pi...:..
         117  73 25 e6 62 9a 10 63 68 e2 25 63 62 74 ac e2 15  s%.b..ch.%cbt...
         133  62 12 23 4d 35 13 51 1b 10 8d c4 5d c0 0b 08 46  b.#M5.Q....]...F
         149  ea e0 22 a4 d0 85 a9 f5 32 82 5d 04 dc 04 5c 74  ..".....2.]...\t
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (935 -> 4725 bytes)

Tamanhos diferentes (delta +3790). Prefixo comum: 19 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [19..923) = 904 bytes, variante [19..4713) = 4694 bytes.

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
          19  00 00 00 01 00 08 02 00 00 00 d3 10 3f 31 00 00  ............?1..
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 12 0a 49 44 41 54 78 5e ed dd f9 57 94 57  ....IDATx^...W.W
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
       17343  64 32 35 63 32 39 31 31 2d 30 34 33 30 2d 34 34  d25c2911-0430-44
       17359  33 37 2d 61 31 30 36 2d 63 31 33 39 31 61 37 62  37-a106-c1391a7b
       17375  32 37 35 36 22 2c 0a 20 20 20 20 20 20 20 20 22  2756",.        "
       17391  6e 61 6d 65                                      name
```

