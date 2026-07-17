# Diff ZCF: `caso_01_add_bitmap_jpeg.cdr` vs `caso_17_bitmap_duplicado.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | — |
| Identicos | `META-INF/container.xml`, `META-INF/links.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `content/data/Bitmaps.dat`, `content/data/masterPage.dat`, `content/dataFileList.dat`, `mimetype` |
| Alterados | `META-INF/metadata.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/page1.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

### `META-INF/metadata.xml` — ALTERADO (8678 -> 8750 bytes)

Tamanhos diferentes (delta +72). Prefixo comum: 1181 bytes; sufixo comum: 515 bytes.
Miolo divergente: base [1181..8163) = 6982 bytes, variante [1181..8235) = 7054 bytes.

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
        1181  35 31 32 34 34 66 32 35 2d 32 34 62 32 2d 34 65  51244f25-24b2-4e
        1197  64 64 2d 62 66 33 33 2d 38 37 64 37 61 63 34 30  dd-bf33-87d7ac40
        1213  31 32 61 31 3c 2f 64 63 3a 69 64 65 6e 74 69 66  12a1</dc:identif
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
          38  33 64 33 64 62 64 34 39 2d 64 31 39 38 2d 34 35  3d3dbd49-d198-45
          54  33 37 2d 62 39 36 35 2d 30 30 65 31 39 39 37 62  37-b965-00e1997b
          70  37 62 38 64 22 20 6e 61 6d 65 3d 22 50 61 6c 65  7b8d" name="Pale
          86  74 61 20 64                                      ta d
```

### `content/data/data1.dat` — ALTERADO (22640 -> 22877 bytes)

Tamanhos diferentes (delta +237). Prefixo comum: 21668 bytes; sufixo comum: 58 bytes.
Miolo divergente: base [21668..22582) = 914 bytes, variante [21668..22819) = 1151 bytes.

```
base (inicio do miolo):
       21652  65 00 00 00 30 00 00 00 10 81 f1 ff a3 12 f7 ff  e...0...........
       21668  10 bd fd ff a3 d6 ea ff 01 00 00 00 13 00 00 00  ................
       21684  01 00 00 00 00 00 00 00 04 00 07 00 07 00 00 00  ................
       21700  00 00 06 00 00 00 4e 00 61 00 6d 00 65 00 00 00  ......N.a.m.e...
       21716  77 00 65 00 62 00 63 00 67 00 6d 00 00 00 47 00  w.e.b.c.g.m...G.
       21732  65 00 6e 00 65 00 72 00 61 00 6c 00 00 00 47 00  e.n.e.r.a.l...G.
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
       21652  65 00 00 00 30 00 00 00 10 81 f1 ff a3 12 f7 ff  e...0...........
       21668  50 ca 00 00 63 c9 e7 ff 01 00 00 00 13 00 00 00  P...c...........
       21684  01 00 00 00 00 00 00 00 04 00 07 00 07 00 00 00  ................
       21700  00 00 06 00 00 00 4e 00 61 00 6d 00 65 00 00 00  ......N.a.m.e...
       21716  77 00 65 00 62 00 63 00 67 00 6d 00 00 00 47 00  w.e.b.c.g.m...G.
       21732  65 00 6e 00 65 00 72 00 61 00 6c 00 00 00 47 00  e.n.e.r.a.l...G.
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/page1.dat` — ALTERADO (2694 -> 3795 bytes)

Tamanhos diferentes (delta +1101). Prefixo comum: 24 bytes; sufixo comum: 410 bytes.
Miolo divergente: base [24..2284) = 2260 bytes, variante [24..3385) = 3361 bytes.

```
base (inicio do miolo):
           8  93 c6 5f 71 47 19 94 06 10 81 f1 ff 02 00 00 00  .._qG...........
          24  02 00 00 00 a3 d6 ea ff 10 81 f1 ff 02 00 00 00  ................
          40  02 00 00 00 a3 d6 ea ff 10 81 f1 ff 02 00 00 00  ................
          56  02 00 00 00 a3 d6 ea ff f8 df 80 7b af c7 7f 41  ...........{...A
          72  a3 ba f2 f0 cd 18 c9 c2 7b 00 00 00 04 00 00 00  ........{.......
          88  14 00 00 00 28 00 00 00 0c 00 00 00 38 00 00 00  ....(.......8...
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           8  93 c6 5f 71 47 19 94 06 10 81 f1 ff 02 00 00 00  .._qG...........
          24  50 ca 00 00 63 c9 e7 ff 10 81 f1 ff 02 00 00 00  P...c...........
          40  50 ca 00 00 63 c9 e7 ff 10 81 f1 ff 02 00 00 00  P...c...........
          56  50 ca 00 00 63 c9 e7 ff f8 df 80 7b af c7 7f 41  P...c......{...A
          72  a3 ba f2 f0 cd 18 c9 c2 7b 00 00 00 04 00 00 00  ........{.......
          88  14 00 00 00 28 00 00 00 0c 00 00 00 38 00 00 00  ....(.......8...
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/root.dat` — ALTERADO (2004 -> 2256 bytes)

Tamanhos diferentes (delta +252). Prefixo comum: 4 bytes; sufixo comum: 6 bytes.
Miolo divergente: base [4..1998) = 1994 bytes, variante [4..2250) = 2246 bytes.

```
base (inicio do miolo):
           0  52 49 46 46 cc 07 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  1c 00 00 00 62 6d 70 74 62 6d 70 20 10 00 00 00  ....bmptbmp ....
          80  00 00 00 00 0a 19 29 00 00 00 00 00 00 00 00 00  ......).........
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           0  52 49 46 46 c8 08 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  1c 00 00 00 62 6d 70 74 62 6d 70 20 10 00 00 00  ....bmptbmp ....
          80  00 00 00 00 0a 19 29 00 00 00 00 00 00 00 00 00  ......).........
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/page1.png` — ALTERADO (2034 -> 2075 bytes)

Tamanhos diferentes (delta +41). Prefixo comum: 86 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [86..2022) = 1936 bytes, variante [86..2063) = 1977 bytes.

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
          86  b0 49 44 41 54 78 5e ed dc 4d 6c 14 65 00 c6 71  .IDATx^..Ml.e..q
         102  66 6d 08 31 26 c0 c1 af 44 6f 92 9e 3b b4 33 6d  fm.1&...Do..;.3m
         118  61 4b 90 52 3e 6a 85 62 f9 6a a5 54 0a 7e 34 c5  aK.R>j.b.j.T.~4.
         134  a4 52 d2 06 30 6d 07 41 0c 01 aa 9c 24 06 09 07  .R..0m.A....$...
         150  20 d2 70 00 0e 24 80 48 60 07 3d 60 f0 80 f1 e0   .p..$.H`.=`....
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (10051 -> 9451 bytes)

Tamanhos diferentes (delta -600). Prefixo comum: 85 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [85..10039) = 9954 bytes, variante [85..9439) = 9354 bytes.

```
base (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  26 d8 49 44 41 54 78 5e ed 9d 89 9f 54 d5 b5 ef  &.IDATx^....T...
         101  eb 9c aa 6a 40 34 38 c5 a8 d1 c4 98 d9 24 d4 d9  ...j@48......$..
         117  7b 9f b1 ba 1a 9a 49 26 99 04 05 01 05 04 01 a5  {.....I&........
         133  11 22 08 32 75 d7 19 9a c4 bc 38 44 63 bc 19 d4  .".2u.....8Dc...
         149  98 9b 9b 68 14 63 62 12 71 02 ba 6b 6e d0 9b 44  ...h.cb.q..kn..D
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  24 80 49 44 41 54 78 5e ed 9d 8b 7b 54 d5 bd f7  $.IDATx^...{T...
         101  67 ef 99 04 22 b4 22 b6 c7 b7 6f eb b1 f5 d0 6a  g..."."...o....j
         117  8f 1e d9 6b ad 7d 9d 10 90 3b 91 fb 1d 02 11 04  ...k.}...;......
         133  15 b9 8b 5c 04 04 32 7b ef 49 b5 6a 95 a2 b6 b4  ...\..2{.I.j....
         149  b5 f6 6d d5 63 bd e0 b5 5a 2f 8d 42 32 d7 a0 e7  ..m.c...Z/.B2...
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
       17343  36 62 31 38 31 62 31 30 2d 64 36 31 37 2d 34 38  6b181b10-d617-48
       17359  30 35 2d 61 38 30 63 2d 33 63 65 62 38 35 61 66  05-a80c-3ceb85af
       17375  36 36 66 34 22 2c 0a 20 20 20 20 20 20 20 20 22  66f4",.        "
       17391  6e 61 6d 65                                      name
```

