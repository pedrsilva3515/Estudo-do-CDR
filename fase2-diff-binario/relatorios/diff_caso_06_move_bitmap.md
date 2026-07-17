# Diff ZCF: `caso_01_add_bitmap_jpeg.cdr` vs `caso_06_move_bitmap.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | — |
| Identicos | `META-INF/container.xml`, `META-INF/links.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `content/data/Bitmaps.dat`, `content/data/masterPage.dat`, `content/dataFileList.dat`, `mimetype`, `previews/thumbnail.png` |
| Alterados | `META-INF/metadata.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/page1.dat`, `content/root.dat`, `previews/page1.png`, `styles/document.cdss` |

### `META-INF/metadata.xml` — ALTERADO (8678 -> 8750 bytes)

Tamanhos diferentes (delta +72). Prefixo comum: 1181 bytes; sufixo comum: 499 bytes.
Miolo divergente: base [1181..8179) = 6998 bytes, variante [1181..8251) = 7070 bytes.

```
base (inicio do miolo):
        1165  20 3c 64 63 3a 69 64 65 6e 74 69 66 69 65 72 3e   <dc:identifier>
        1181  31 30 31 38 37 66 32 38 2d 65 62 33 62 2d 34 63  10187f28-eb3b-4c
        1197  33 63 2d 62 61 30 33 2d 39 63 37 31 63 36 61 62  3c-ba03-9c71c6ab
        1213  34 32 64 39 3c 2f 64 63 3a 69 64 65 6e 74 69 66  42d9</dc:identif
        1229  69 65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20  ier>.           
        1245  20 3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65   <xmpMM:Instance
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
        1165  20 3c 64 63 3a 69 64 65 6e 74 69 66 69 65 72 3e   <dc:identifier>
        1181  63 63 36 61 34 32 35 32 2d 38 31 33 34 2d 34 39  cc6a4252-8134-49
        1197  32 34 2d 38 30 34 66 2d 38 33 37 61 39 38 65 30  24-804f-837a98e0
        1213  64 31 39 39 3c 2f 64 63 3a 69 64 65 6e 74 69 66  d199</dc:identif
        1229  69 65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20  ier>.           
        1245  20 3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65   <xmpMM:Instance
  ... (regiao truncada; tamanho real 96 bytes)
```

### `color/docPalette.xml` — ALTERADO (203 -> 203 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 38, 36 byte(s)**
```
base:
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  66 65 62 35 30 32 33 64 2d 63 62 65 63 2d 34 66  feb5023d-cbec-4f
          54  36 63 2d 39 34 32 64 2d 36 63 38 36 35 32 38 35  6c-942d-6c865285
          70  39 65 38 37 22 20 6e 61 6d 65 3d 22 50 61 6c 65  9e87" name="Pale
          86  74 61 20 64                                      ta d
variante:
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  61 30 34 39 62 32 31 38 2d 62 34 30 65 2d 34 34  a049b218-b40e-44
          54  38 62 2d 39 65 37 36 2d 61 38 63 39 37 65 35 65  8b-9e76-a8c97e5e
          70  32 36 35 31 22 20 6e 61 6d 65 3d 22 50 61 6c 65  2651" name="Pale
          86  74 61 20 64                                      ta d
```

### `content/data/data1.dat` — ALTERADO (22640 -> 22640 bytes)

Mesmo tamanho; 3 regiao(oes) alterada(s):

**Regiao 1: offset 21660, 15 byte(s)**
```
base:
       21644  77 00 4d 00 6f 00 64 00 65 00 00 00 30 00 00 00  w.M.o.d.e...0...
       21660  10 81 f1 ff a3 12 f7 ff 10 bd fd ff a3 d6 ea ff  ................
       21676  01 00 00 00 13 00 00 00 01 00 00 00 00 00 00     ...............
variante:
       21644  77 00 4d 00 6f 00 64 00 65 00 00 00 30 00 00 00  w.M.o.d.e...0...
       21660  68 8a f4 ff 4b 09 f4 ff 50 ca 00 00 63 c9 e7 ff  h...K...P...c...
       21676  01 00 00 00 13 00 00 00 01 00 00 00 00 00 00     ...............
```

**Regiao 2: offset 22415, 16 byte(s)**
```
base:
       22399  00 00 00 00 02 00 00 00 0b 00 00 00 10 00 00 00  ................
       22415  ed d9 b9 60 d7 2f 9c 49 8b 52 d1 38 dd 32 5b 7b  ...`./.I.R.8.2[{
       22431  03 00 00 00 04 00 00 00 40 4b 4c 00 02 00 00 00  ........@KL.....
variante:
       22399  00 00 00 00 02 00 00 00 0b 00 00 00 10 00 00 00  ................
       22415  7e bb 65 ed d4 b8 c4 43 b5 f8 7e 47 ad d4 43 00  ~.e....C..~G..C.
       22431  03 00 00 00 04 00 00 00 40 4b 4c 00 02 00 00 00  ........@KL.....
```

**Regiao 3: offset 22580, 2 byte(s)**
```
base:
       22564  00 00 05 00 05 00 00 00 00 00 00 00 00 00 00 00  ................
       22580  92 d9 00 00 00 00 40 a5 ae 02 3c 00 00 00 00 00  ......@...<.....
       22596  00 00                                            ..
variante:
       22564  00 00 05 00 05 00 00 00 00 00 00 00 00 00 00 00  ................
       22580  32 c5 00 00 00 00 40 a5 ae 02 3c 00 00 00 00 00  2.....@...<.....
       22596  00 00                                            ..
```

### `content/data/page1.dat` — ALTERADO (2694 -> 2706 bytes)

Tamanhos diferentes (delta +12). Prefixo comum: 16 bytes; sufixo comum: 972 bytes.
Miolo divergente: base [16..1722) = 1706 bytes, variante [16..1734) = 1718 bytes.

```
base (inicio do miolo):
           0  ca e3 0e 25 44 cf 60 4e 93 c6 5f 71 47 19 94 06  ...%D.`N.._qG...
          16  10 81 f1 ff 02 00 00 00 02 00 00 00 a3 d6 ea ff  ................
          32  10 81 f1 ff 02 00 00 00 02 00 00 00 a3 d6 ea ff  ................
          48  10 81 f1 ff 02 00 00 00 02 00 00 00 a3 d6 ea ff  ................
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  7b 00 00 00 04 00 00 00 14 00 00 00 28 00 00 00  {...........(...
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           0  ca e3 0e 25 44 cf 60 4e 93 c6 5f 71 47 19 94 06  ...%D.`N.._qG...
          16  50 8e f4 ff 02 00 00 00 50 ca 00 00 63 c9 e7 ff  P.......P...c...
          32  50 8e f4 ff 02 00 00 00 50 ca 00 00 63 c9 e7 ff  P.......P...c...
          48  68 8a f4 ff 02 00 00 00 50 ca 00 00 63 c9 e7 ff  h.......P...c...
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  7b 00 00 00 04 00 00 00 14 00 00 00 28 00 00 00  {...........(...
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/root.dat` — ALTERADO (2004 -> 2004 bytes)

Mesmo tamanho; 7 regiao(oes) alterada(s):

**Regiao 1: offset 1584, 29 byte(s)**
```
base:
        1568  6c 67 6f 62 6c 6f 64 61 10 00 00 00 03 00 00 00  lgobloda........
        1584  65 03 00 00 ce 02 00 00 00 00 00 00 66 74 69 6c  e...........ftil
        1600  10 00 00 00 03 00 00 00 30 00 00 00 33 06 00 00  ........0...3...
        1616  00 00 00 00 4c 49 53 54 1c 00 00 00 74           ....LIST....t
variante:
        1568  6c 67 6f 62 6c 6f 64 61 10 00 00 00 03 00 00 00  lgobloda........
        1584  71 03 00 00 ce 02 00 00 00 00 00 00 66 74 69 6c  q...........ftil
        1600  10 00 00 00 03 00 00 00 30 00 00 00 3f 06 00 00  ........0...?...
        1616  00 00 00 00 4c 49 53 54 1c 00 00 00 74           ....LIST....t
```

**Regiao 2: offset 1648, 1 byte(s)**
```
base:
        1632  74 72 66 64 10 00 00 00 03 00 00 00 60 00 00 00  trfd........`...
        1648  63 06 00 00 00 00 00 00 4c 49 53 54 f4 00 00 00  c.......LIST....
        1664  6f                                               o
variante:
        1632  74 72 66 64 10 00 00 00 03 00 00 00 60 00 00 00  trfd........`...
        1648  6f 06 00 00 00 00 00 00 4c 49 53 54 f4 00 00 00  o.......LIST....
        1664  6f                                               o
```

**Regiao 3: offset 1732, 49 byte(s)**
```
base:
        1716  73 70 69 64 10 00 00 00 03 00 00 00 10 00 00 00  spid............
        1732  c3 06 00 00 00 00 00 00 62 62 6f 78 10 00 00 00  ........bbox....
        1748  03 00 00 00 10 00 00 00 d3 06 00 00 00 00 00 00  ................
        1764  6f 62 62 78 10 00 00 00 03 00 00 00 20 00 00 00  obbx........ ...
        1780  e3 06 00 00 00 00 00 00 75 73 64 6e 10 00 00 00  ........usdn....
        1796  ff                                               .
variante:
        1716  73 70 69 64 10 00 00 00 03 00 00 00 10 00 00 00  spid............
        1732  cf 06 00 00 00 00 00 00 62 62 6f 78 10 00 00 00  ........bbox....
        1748  03 00 00 00 10 00 00 00 df 06 00 00 00 00 00 00  ................
        1764  6f 62 62 78 10 00 00 00 03 00 00 00 20 00 00 00  obbx........ ...
        1780  ef 06 00 00 00 00 00 00 75 73 64 6e 10 00 00 00  ........usdn....
        1796  ff                                               .
```

**Regiao 4: offset 1840, 25 byte(s)**
```
base:
        1824  6c 6f 64 61 10 00 00 00 03 00 00 00 74 02 00 00  loda........t...
        1840  03 07 00 00 00 00 00 00 66 74 69 6c 10 00 00 00  ........ftil....
        1856  03 00 00 00 30 00 00 00 77 09 00 00 00 00 00 00  ....0...w.......
        1872  4c 49 53 54 1c 00 00 00 74                       LIST....t
variante:
        1824  6c 6f 64 61 10 00 00 00 03 00 00 00 74 02 00 00  loda........t...
        1840  0f 07 00 00 00 00 00 00 66 74 69 6c 10 00 00 00  ........ftil....
        1856  03 00 00 00 30 00 00 00 83 09 00 00 00 00 00 00  ....0...........
        1872  4c 49 53 54 1c 00 00 00 74                       LIST....t
```

**Regiao 5: offset 1900, 1 byte(s)**
```
base:
        1884  74 72 66 64 10 00 00 00 03 00 00 00 60 00 00 00  trfd........`...
        1900  a7 09 00 00 00 00 00 00 4c 49 53 54 58 00 00 00  ........LISTX...
        1916  6c                                               l
variante:
        1884  74 72 66 64 10 00 00 00 03 00 00 00 60 00 00 00  trfd........`...
        1900  b3 09 00 00 00 00 00 00 4c 49 53 54 58 00 00 00  ........LISTX...
        1916  6c                                               l
```

**Regiao 6: offset 1960, 1 byte(s)**
```
base:
        1944  73 70 69 64 10 00 00 00 03 00 00 00 10 00 00 00  spid............
        1960  07 0a 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
        1976  6c                                               l
variante:
        1944  73 70 69 64 10 00 00 00 03 00 00 00 10 00 00 00  spid............
        1960  13 0a 00 00 00 00 00 00 4c 49 53 54 1c 00 00 00  ........LIST....
        1976  6c                                               l
```

**Regiao 7: offset 1996, 1 byte(s)**
```
base:
        1980  6c 6f 64 61 10 00 00 00 03 00 00 00 6f 00 00 00  loda........o...
        1996  17 0a 00 00 00 00 00 00                          ........
variante:
        1980  6c 6f 64 61 10 00 00 00 03 00 00 00 6f 00 00 00  loda........o...
        1996  23 0a 00 00 00 00 00 00                          #.......
```

### `previews/page1.png` — ALTERADO (2034 -> 1999 bytes)

Tamanhos diferentes (delta -35). Prefixo comum: 86 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [86..2022) = 1936 bytes, variante [86..1987) = 1901 bytes.

```
base (inicio do miolo):
          70  00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00 07  ..........o.d...
          86  87 49 44 41 54 78 5e ed dc 4b 4c 14 77 00 c7 71  .IDATx^..KL.w..q
         102  67 35 c6 34 4d d4 43 5f 49 7b ab f1 cc 08 33 80  g5.4M.C_I{....3.
         118  2e c6 8a f8 a0 54 b1 f8 02 45 2a 6a 5b 82 4d a8  .....T...E*j[.M.
         134  18 88 8f 20 63 b5 36 46 45 3d d5 34 d6 78 50 53  ... c.6FE=.4.xPS
         150  89 07 f1 60 a2 56 8d ee a8 07 1a 3d 68 3c f4 e4  ...`.V.....=h<..
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          70  00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00 07  ..........o.d...
          86  64 49 44 41 54 78 5e ed dc 4b 4c 54 67 00 86 61  dIDATx^..KLTg..a
         102  cf 68 4c d3 34 51 17 bd 25 ed ae 86 35 47 66 0e  .hL.4Q..%...5Gf.
         118  b7 81 58 11 51 4a 15 c5 1b a3 40 41 6d 4b a0 09  ..X.QJ....@AmK..
         134  15 03 f1 12 e0 58 ac 8d 51 51 d2 45 4d 63 8d 0b  .....X..QQ.EMc..
         150  b5 4a 5d a8 0b 13 b1 6a 74 8e ba 30 d1 05 c6 45  .J]....jt..0...E
  ... (regiao truncada; tamanho real 96 bytes)
```

### `styles/document.cdss` — ALTERADO (17499 -> 17499 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 17343, 36 byte(s)**
```
base:
       17327  20 20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22         "guid": "
       17343  35 64 32 66 36 63 31 31 2d 63 33 38 61 2d 34 65  5d2f6c11-c38a-4e
       17359  64 33 2d 62 36 62 37 2d 65 34 32 31 66 31 36 37  d3-b6b7-e421f167
       17375  30 35 37 63 22 2c 0a 20 20 20 20 20 20 20 20 22  057c",.        "
       17391  6e 61 6d 65                                      name
variante:
       17327  20 20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22         "guid": "
       17343  62 35 66 37 62 62 66 35 2d 64 63 63 32 2d 34 31  b5f7bbf5-dcc2-41
       17359  65 39 2d 61 61 37 39 2d 32 32 36 30 39 35 31 34  e9-aa79-22609514
       17375  62 39 35 35 22 2c 0a 20 20 20 20 20 20 20 20 22  b955",.        "
       17391  6e 61 6d 65                                      name
```

