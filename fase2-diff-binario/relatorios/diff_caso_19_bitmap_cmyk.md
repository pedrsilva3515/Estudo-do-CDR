# Diff ZCF: `caso_00_base.cdr` vs `caso_19_bitmap_cmyk.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | `content/data/Bitmaps.dat` |
| Identicos | `META-INF/links.xml`, `mimetype` |
| Alterados | `META-INF/container.xml`, `META-INF/metadata.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/masterPage.dat`, `content/data/page1.dat`, `content/dataFileList.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

### `content/data/Bitmaps.dat` — NOVO na variante (3587354 bytes)
```
           0  01 00 00 00 01 00 00 00 55 49 00 00 12 bd 36 00  ........UI....6.
          16  00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00  .... ...........
          32  02 00 00 00 ff 00 00 00 52 49 f2 bc 36 00 00 00  ........RI..6...
          48  00 00 4e 00 00 00 03 00 00 00 01 00 00 00 b3 03  ..N.............
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
         369  65 5f 63 6d 79 6b 2e 74 69 66 3c 2f 72 64 66 3a  e_cmyk.tif</rdf:
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
          38  35 39 65 39 65 34 35 66 2d 30 65 32 63 2d 34 61  59e9e45f-0e2c-4a
          54  32 30 2d 61 30 32 66 2d 33 38 64 35 35 66 64 63  20-a02f-38d55fdc
          70  62 64 61 63 22 20 6e 61 6d 65 3d 22 50 61 6c 65  bdac" name="Pale
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
          80  00 00 00 00 1a bd 36 00 00 00 00 00 00 00 00 00  ......6.........
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/page1.png` — ALTERADO (829 -> 2912 bytes)

Tamanhos diferentes (delta +2083). Prefixo comum: 85 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [85..817) = 732 bytes, variante [85..2900) = 2815 bytes.

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
          85  0a f5 49 44 41 54 78 5e ed dc eb 53 54 e7 1d c0  ..IDATx^...ST...
         101  71 de f4 af e8 8b ce f4 45 33 49 ea 8b 66 9a 4c  q.......E3I..f.L
         117  33 e9 a4 13 63 87 7a e3 0e 02 72 07 b9 ac 5c e5  3...c.z...r...\.
         133  ea 2e 0b 0b ec e5 ec 2e bb b0 a0 08 51 62 54 f0  ............QbT.
         149  02 2a e2 05 15 a3 a4 12 83 80 58 10 a3 4d 4c eb  .*........X..ML.
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (935 -> 8202 bytes)

Tamanhos diferentes (delta +7267). Prefixo comum: 19 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [19..923) = 904 bytes, variante [19..8190) = 8171 bytes.

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
          83  00 00 1f 9f 49 44 41 54 78 5e ed dd 69 70 14 67  ....IDATx^..ip.g
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
       17344  64 35 33 32 31 35 36 2d 65 61 64 66 2d 34 63 61  d532156-eadf-4ca
       17360  32 2d 61 37 39 34 2d 39 63 65 36 62 33 35 37 37  2-a794-9ce6b3577
       17376  33 37 35 22 2c 0a 20 20 20 20 20 20 20 20 22 6e  375",.        "n
       17392  61 6d 65                                         ame
```

