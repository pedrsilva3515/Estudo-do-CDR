# Diff ZCF: `caso_12_dois_objetos.cdr` vs `caso_15_powerclip.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | — |
| Identicos | `META-INF/links.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `content/data/masterPage.dat`, `content/dataFileList.dat`, `mimetype` |
| Alterados | `META-INF/container.xml`, `META-INF/metadata.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/page1.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

### `META-INF/container.xml` — ALTERADO (690 -> 690 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 396, 3 byte(s)**
```
base:
         380  72 6c 3a 69 6d 61 67 65 2d 77 69 64 74 68 3d 22  rl:image-width="
         396  32 35 36 22 20 66 75 6c 6c 2d 70 61 74 68 3d 22  256" full-path="
         412  70 72 65                                         pre
variante:
         380  72 6c 3a 69 6d 61 67 65 2d 77 69 64 74 68 3d 22  rl:image-width="
         396  33 38 33 22 20 66 75 6c 6c 2d 70 61 74 68 3d 22  383" full-path="
         412  70 72 65                                         pre
```

### `META-INF/metadata.xml` — ALTERADO (8605 -> 8680 bytes)

Tamanhos diferentes (delta +75). Prefixo comum: 1181 bytes; sufixo comum: 500 bytes.
Miolo divergente: base [1181..8105) = 6924 bytes, variante [1181..8180) = 6999 bytes.

```
base (inicio do miolo):
        1165  20 3c 64 63 3a 69 64 65 6e 74 69 66 69 65 72 3e   <dc:identifier>
        1181  34 65 63 64 30 64 37 64 2d 63 36 65 63 2d 34 39  4ecd0d7d-c6ec-49
        1197  39 35 2d 61 37 33 38 2d 35 33 30 36 66 32 36 36  95-a738-5306f266
        1213  65 66 32 66 3c 2f 64 63 3a 69 64 65 6e 74 69 66  ef2f</dc:identif
        1229  69 65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20  ier>.           
        1245  20 3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65   <xmpMM:Instance
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
        1165  20 3c 64 63 3a 69 64 65 6e 74 69 66 69 65 72 3e   <dc:identifier>
        1181  31 39 64 64 66 34 66 34 2d 63 30 35 37 2d 34 31  19ddf4f4-c057-41
        1197  35 38 2d 61 62 65 33 2d 65 39 38 37 35 39 33 33  58-abe3-e9875933
        1213  62 35 65 36 3c 2f 64 63 3a 69 64 65 6e 74 69 66  b5e6</dc:identif
        1229  69 65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20  ier>.           
        1245  20 3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65   <xmpMM:Instance
  ... (regiao truncada; tamanho real 96 bytes)
```

### `color/docPalette.xml` — ALTERADO (237 -> 260 bytes)

Tamanhos diferentes (delta +23). Prefixo comum: 38 bytes; sufixo comum: 47 bytes.
Miolo divergente: base [38..190) = 152 bytes, variante [38..213) = 175 bytes.

```
base (inicio do miolo):
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  30 37 32 31 61 35 64 38 2d 34 65 63 38 2d 34 65  0721a5d8-4ec8-4e
          54  35 63 2d 39 65 63 30 2d 39 66 34 66 35 33 62 63  5c-9ec0-9f4f53bc
          70  64 37 66 64 22 20 6e 61 6d 65 3d 22 50 61 6c 65  d7fd" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  32 38 33 66 36 33 30 35 2d 64 33 39 64 2d 34 35  283f6305-d39d-45
          54  35 38 2d 38 33 35 33 2d 31 63 35 66 37 61 61 62  58-8353-1c5f7aab
          70  63 63 61 34 22 20 6e 61 6d 65 3d 22 50 61 6c 65  cca4" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/data1.dat` — ALTERADO (22509 -> 23515 bytes)

Tamanhos diferentes (delta +1006). Prefixo comum: 21664 bytes; sufixo comum: 8 bytes.
Miolo divergente: base [21664..22501) = 837 bytes, variante [21664..23507) = 1843 bytes.

```
base (inicio do miolo):
       21648  6f 00 64 00 65 00 00 00 30 00 00 00 68 8a f4 ff  o.d.e...0...h...
       21664  db d9 f7 ff 48 7d fe ff fb e6 ed ff 01 00 00 00  ....H}..........
       21680  13 00 00 00 01 00 00 00 00 00 00 00 04 00 07 00  ................
       21696  07 00 00 00 00 00 06 00 00 00 4e 00 61 00 6d 00  ..........N.a.m.
       21712  65 00 00 00 77 00 65 00 62 00 63 00 67 00 6d 00  e...w.e.b.c.g.m.
       21728  00 00 47 00 65 00 6e 00 65 00 72 00 61 00 6c 00  ..G.e.n.e.r.a.l.
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
       21648  6f 00 64 00 65 00 00 00 30 00 00 00 68 8a f4 ff  o.d.e...0...h...
       21664  4b 09 f4 ff f8 b9 fd ff fb e6 ed ff 01 00 00 00  K...............
       21680  13 00 00 00 01 00 00 00 00 00 00 00 04 00 07 00  ................
       21696  07 00 00 00 00 00 06 00 00 00 4e 00 61 00 6d 00  ..........N.a.m.
       21712  65 00 00 00 77 00 65 00 62 00 63 00 67 00 6d 00  e...w.e.b.c.g.m.
       21728  00 00 47 00 65 00 6e 00 65 00 72 00 61 00 6c 00  ..G.e.n.e.r.a.l.
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/page1.dat` — ALTERADO (2305 -> 1653 bytes)

Tamanhos diferentes (delta -652). Prefixo comum: 654 bytes; sufixo comum: 274 bytes.
Miolo divergente: base [654..2031) = 1377 bytes, variante [654..1379) = 725 bytes.

```
base (inicio do miolo):
         638  61 00 6d 00 61 00 64 00 61 00 20 00 31 00 00 00  a.m.a.d.a. .1...
         654  2e 9d 7e 59 a7 de 3e 4f 8b d8 1b 4c d6 44 a6 18  ..~Y..>O...L.D..
         670  80 e5 f9 ff f3 d5 f7 ff 60 79 fe ff 13 42 f3 ff  ........`y...B..
         686  80 e5 f9 ff f3 d5 f7 ff 60 79 fe ff 13 42 f3 ff  ........`y...B..
         702  98 e1 f9 ff db d9 f7 ff 48 7d fe ff 2b 3e f3 ff  ........H}..+>..
         718  e0 01 00 00 06 00 00 00 14 00 00 00 30 00 00 00  ............0...
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
         638  61 00 6d 00 61 00 64 00 61 00 20 00 31 00 00 00  a.m.a.d.a. .1...
         654  5e 27 39 11 66 5c 87 4a b4 44 a4 5f 2b 29 11 a2  ^'9.f\.J.D._+)..
         670  50 8e f4 ff 63 05 f4 ff 10 b6 fd ff e3 ea ed ff  P...c...........
         686  50 8e f4 ff 63 05 f4 ff 10 b6 fd ff e3 ea ed ff  P...c...........
         702  68 8a f4 ff 4b 09 f4 ff f8 b9 fd ff fb e6 ed ff  h...K...........
         718  98 02 00 00 0a 00 00 00 14 00 00 00 40 00 00 00  ............@...
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/root.dat` — ALTERADO (2028 -> 2148 bytes)

Tamanhos diferentes (delta +120). Prefixo comum: 4 bytes; sufixo comum: 6 bytes.
Miolo divergente: base [4..2022) = 2018 bytes, variante [4..2142) = 2138 bytes.

```
base (inicio do miolo):
           0  52 49 46 46 e4 07 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  c0 01 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  ....doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           0  52 49 46 46 5c 08 00 00 43 44 52 54 66 76 65 72  RIFF\...CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  34 03 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  4...doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/page1.png` — ALTERADO (1612 -> 1021 bytes)

Tamanhos diferentes (delta -591). Prefixo comum: 85 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [85..1600) = 1515 bytes, variante [85..1009) = 924 bytes.

```
base (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  05 e1 49 44 41 54 78 5e ed da 4d 88 dc 77 1d c7  ..IDATx^..M..w..
         101  f1 68 83 55 10 9f 8a 37 eb c1 83 60 d1 0a d3 64  .h.U...7...`...d
         117  66 1f 66 1f 5a b3 c1 25 c9 26 bb 93 dd 74 a3 17  f.f.Z..%.&...t..
         133  25 04 db c6 5a dd 16 1f 50 10 62 84 36 d6 b6 c6  %...Z...P.b.6...
         149  40 1a b0 41 0b 89 0a 01 e9 c5 46 42 0f f5 62 65  @..A......FB..be
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  03 92 49 44 41 54 78 5e ed d2 3f 6b 9d 05 18 87  ..IDATx^..?k....
         101  e1 0c a2 b8 f8 09 f4 03 b4 e3 db f4 7d 7b 6a 9b  ............}{j.
         117  66 e9 10 2c 35 a6 a6 b5 e0 54 8a e0 e2 26 e2 ac  f..,5....T...&..
         133  75 a8 83 a2 14 74 d1 cd 7f 50 71 ed d2 41 17 37  u....t...Pq..A.7
         149  17 17 17 1d dc 84 6e 81 0c 19 94 52 14 39 e2 7d  ......n....R.9.}
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (3737 -> 2240 bytes)

Tamanhos diferentes (delta -1497). Prefixo comum: 19 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [19..3725) = 3706 bytes, variante [19..2228) = 2209 bytes.

```
base (inicio do miolo):
           3  47 0d 0a 1a 0a 00 00 00 0d 49 48 44 52 00 00 01  G........IHDR...
          19  00 00 00 01 00 08 02 00 00 00 d3 10 3f 31 00 00  ............?1..
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 0e 2e 49 44 41 54 78 5e ed dd 79 58 14 f7  ....IDATx^..yX..
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           3  47 0d 0a 1a 0a 00 00 00 0d 49 48 44 52 00 00 01  G........IHDR...
          19  7f 00 00 01 00 08 02 00 00 00 d4 52 e1 24 00 00  ...........R.$..
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 08 55 49 44 41 54 78 5e ed dd db 8f dc 65  ...UIDATx^.....e
  ... (regiao truncada; tamanho real 96 bytes)
```

### `styles/document.cdss` — ALTERADO (17499 -> 17499 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 17343, 36 byte(s)**
```
base:
       17327  20 20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22         "guid": "
       17343  39 62 38 61 63 65 62 65 2d 36 36 33 35 2d 34 61  9b8acebe-6635-4a
       17359  39 34 2d 39 38 62 65 2d 34 66 32 65 37 66 64 62  94-98be-4f2e7fdb
       17375  39 37 66 33 22 2c 0a 20 20 20 20 20 20 20 20 22  97f3",.        "
       17391  6e 61 6d 65                                      name
variante:
       17327  20 20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22         "guid": "
       17343  36 64 30 35 33 32 63 34 2d 34 63 37 63 2d 34 31  6d0532c4-4c7c-41
       17359  31 30 2d 39 33 38 63 2d 33 33 30 65 65 35 38 62  10-938c-330ee58b
       17375  66 39 65 64 22 2c 0a 20 20 20 20 20 20 20 20 22  f9ed",.        "
       17391  6e 61 6d 65                                      name
```

