# Diff ZCF: `caso_01_add_bitmap_jpeg.cdr` vs `caso_16_dois_bitmaps_diferentes.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | — |
| Identicos | `META-INF/links.xml`, `color/color.xml`, `content/data/masterPage.dat`, `content/dataFileList.dat`, `mimetype` |
| Alterados | `META-INF/container.xml`, `META-INF/metadata.xml`, `META-INF/textinfo.xml`, `color/docPalette.xml`, `content/data/Bitmaps.dat`, `content/data/data1.dat`, `content/data/page1.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

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
         396  34 37 39 22 20 66 75 6c 6c 2d 70 61 74 68 3d 22  479" full-path="
         412  70 72 65                                         pre
```

### `META-INF/metadata.xml` — ALTERADO (8678 -> 8751 bytes)

Tamanhos diferentes (delta +73). Prefixo comum: 1181 bytes; sufixo comum: 515 bytes.
Miolo divergente: base [1181..8163) = 6982 bytes, variante [1181..8236) = 7055 bytes.

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
        1181  63 62 39 34 62 38 33 64 2d 33 63 61 31 2d 34 31  cb94b83d-3ca1-41
        1197  64 64 2d 38 65 34 34 2d 64 38 35 32 64 33 63 32  dd-8e44-d852d3c2
        1213  65 64 39 63 3c 2f 64 63 3a 69 64 65 6e 74 69 66  ed9c</dc:identif
        1229  69 65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20  ier>.           
        1245  20 3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65   <xmpMM:Instance
  ... (regiao truncada; tamanho real 96 bytes)
```

### `META-INF/textinfo.xml` — ALTERADO (725 -> 776 bytes)

Tamanhos diferentes (delta +51). Prefixo comum: 371 bytes; sufixo comum: 354 bytes.
Miolo divergente: base [371..371) = 0 bytes, variante [371..422) = 51 bytes.

```
base (inicio do miolo):
         355  20 20 3c 72 64 66 3a 6c 69 3e 66 6f 6e 74 65 5f    <rdf:li>fonte_
         371  62 61 73 65 2e 6a 70 67 3c 2f 72 64 66 3a 6c 69  base.jpg</rdf:li
variante (inicio do miolo):
         355  20 20 3c 72 64 66 3a 6c 69 3e 66 6f 6e 74 65 5f    <rdf:li>fonte_
         371  61 6c 74 2e 6a 70 67 3c 2f 72 64 66 3a 6c 69 3e  alt.jpg</rdf:li>
         387  0a 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20  .               
         403  20 20 20 20 20 3c 72 64 66 3a 6c 69 3e 66 6f 6e       <rdf:li>fon
         419  74 65 5f 62 61 73 65 2e 6a 70 67 3c 2f 72 64 66  te_base.jpg</rdf
         435  3a 6c 69                                         :li
```

### `color/docPalette.xml` — ALTERADO (203 -> 203 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 38, 35 byte(s)**
```
base:
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  66 65 62 35 30 32 33 64 2d 63 62 65 63 2d 34 66  feb5023d-cbec-4f
          54  36 63 2d 39 34 32 64 2d 36 63 38 36 35 32 38 35  6c-942d-6c865285
          70  39 65 38 37 22 20 6e 61 6d 65 3d 22 50 61 6c 65  9e87" name="Pale
          86  74 61 20                                         ta 
variante:
          22  0a 3c 70 61 6c 65 74 74 65 20 67 75 69 64 3d 22  .<palette guid="
          38  36 62 31 38 34 34 37 63 2d 37 66 61 37 2d 34 64  6b18447c-7fa7-4d
          54  61 35 2d 38 39 65 37 2d 61 37 63 61 32 62 63 37  a5-89e7-a7ca2bc7
          70  66 39 62 37 22 20 6e 61 6d 65 3d 22 50 61 6c 65  f9b7" name="Pale
          86  74 61 20                                         ta 
```

### `content/data/Bitmaps.dat` — ALTERADO (2693386 -> 5386772 bytes)

Tamanhos diferentes (delta +2693386). Prefixo comum: 2693386 bytes; sufixo comum: 0 bytes.
Miolo divergente: base [2693386..2693386) = 0 bytes, variante [2693386..5386772) = 2693386 bytes.

```
base (inicio do miolo):
     2693370  26 38 3a 26 25 21 55 2c 2f 3e 36 3e 27 5c 5c ff  &8:&%!U,/>6>'\\.
variante (inicio do miolo):
     2693370  26 38 3a 26 25 21 55 2c 2f 3e 36 3e 27 5c 5c ff  &8:&%!U,/>6>'\\.
     2693386  02 00 00 00 01 00 00 00 55 49 00 00 02 19 29 00  ........UI....).
     2693402  00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00  .... ...........
     2693418  02 00 00 00 ff 00 00 00 52 49 e2 18 29 00 00 00  ........RI..)...
     2693434  00 00 4e 00 00 00 01 00 00 00 01 00 00 00 b3 03  ..N.............
     2693450  00 00 b3 03 00 00 01 00 00 00 18 00 00 00 1c 0b  ................
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/data1.dat` — ALTERADO (22640 -> 22640 bytes)

Mesmo tamanho; 3 regiao(oes) alterada(s):

**Regiao 1: offset 21668, 4 byte(s)**
```
base:
       21652  65 00 00 00 30 00 00 00 10 81 f1 ff a3 12 f7 ff  e...0...........
       21668  10 bd fd ff a3 d6 ea ff 01 00 00 00 13 00 00 00  ................
       21684  01 00 00 00                                      ....
variante:
       21652  65 00 00 00 30 00 00 00 10 81 f1 ff a3 12 f7 ff  e...0...........
       21668  70 6b 08 00 a3 d6 ea ff 01 00 00 00 13 00 00 00  pk..............
       21684  01 00 00 00                                      ....
```

**Regiao 2: offset 22415, 16 byte(s)**
```
base:
       22399  00 00 00 00 02 00 00 00 0b 00 00 00 10 00 00 00  ................
       22415  ed d9 b9 60 d7 2f 9c 49 8b 52 d1 38 dd 32 5b 7b  ...`./.I.R.8.2[{
       22431  03 00 00 00 04 00 00 00 40 4b 4c 00 02 00 00 00  ........@KL.....
variante:
       22399  00 00 00 00 02 00 00 00 0b 00 00 00 10 00 00 00  ................
       22415  67 7e cc b7 0a a6 a6 4c 8a ba d9 3b fd c0 8b 24  g~.....L...;...$
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
       22580  00 00 00 00 00 00 40 a5 ae 02 3c 00 00 00 00 00  ......@...<.....
       22596  00 00                                            ..
```

### `content/data/page1.dat` — ALTERADO (2694 -> 3781 bytes)

Tamanhos diferentes (delta +1087). Prefixo comum: 24 bytes; sufixo comum: 410 bytes.
Miolo divergente: base [24..2284) = 2260 bytes, variante [24..3371) = 3347 bytes.

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
          24  70 6b 08 00 a3 d6 ea ff 10 81 f1 ff 02 00 00 00  pk..............
          40  70 6b 08 00 a3 d6 ea ff 10 81 f1 ff 02 00 00 00  pk..............
          56  70 6b 08 00 a3 d6 ea ff f8 df 80 7b af c7 7f 41  pk.........{...A
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
          64  34 00 00 00 62 6d 70 74 62 6d 70 20 10 00 00 00  4...bmptbmp ....
          80  00 00 00 00 0a 19 29 00 00 00 00 00 00 00 00 00  ......).........
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/page1.png` — ALTERADO (2034 -> 3874 bytes)

Tamanhos diferentes (delta +1840). Prefixo comum: 85 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [85..2022) = 1937 bytes, variante [85..3862) = 3777 bytes.

```
base (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  07 87 49 44 41 54 78 5e ed dc 4b 4c 14 77 00 c7  ..IDATx^..KL.w..
         101  71 67 35 c6 34 4d d4 43 5f 49 7b ab f1 cc 08 33  qg5.4M.C_I{....3
         117  80 2e c6 8a f8 a0 54 b1 f8 02 45 2a 6a 5b 82 4d  ......T...E*j[.M
         133  a8 18 88 8f 20 63 b5 36 46 45 3d d5 34 d6 78 50  .... c.6FE=.4.xP
         149  53 89 07 f1 60 a2 56 8d ee a8 07 1a 3d 68 3c f4  S...`.V.....=h<.
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
          69  73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64 00 00  s..........o.d..
          85  0e b7 49 44 41 54 78 5e ed dd 79 50 d3 f7 9f c7  ..IDATx^..yP....
         101  71 43 ed 6f 3a bb bf f9 b5 fd fd 7e ed 76 ad 75  qC.o:......~.v.u
         117  f4 57 4b 6a f5 a7 25 42 22 60 00 91 1b 81 c8 8d  .WKj..%B"`......
         133  5c c1 18 2e c3 7d 85 33 24 04 8c 40 10 f1 a8 d0  \....}.3$..@....
         149  2a 5a 0f 3c a8 28 68 3d 10 b1 0a c1 13 6f 6d 6b  *Z.<.(h=.....omk
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (10051 -> 29614 bytes)

Tamanhos diferentes (delta +19563). Prefixo comum: 19 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [19..10039) = 10020 bytes, variante [19..29602) = 29583 bytes.

```
base (inicio do miolo):
           3  47 0d 0a 1a 0a 00 00 00 0d 49 48 44 52 00 00 01  G........IHDR...
          19  00 00 00 01 00 08 02 00 00 00 d3 10 3f 31 00 00  ............?1..
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 26 d8 49 44 41 54 78 5e ed 9d 89 9f 54 d5  ..&.IDATx^....T.
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
           3  47 0d 0a 1a 0a 00 00 00 0d 49 48 44 52 00 00 01  G........IHDR...
          19  df 00 00 01 00 08 02 00 00 00 7d 0a eb f5 00 00  ..........}.....
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 73 43 49 44 41 54 78 5e ed bd 05 54 db 69  ..sCIDATx^...T.i
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
       17343  62 34 33 39 34 34 61 61 2d 33 36 36 64 2d 34 61  b43944aa-366d-4a
       17359  32 62 2d 39 66 39 65 2d 36 31 64 30 34 30 39 30  2b-9f9e-61d04090
       17375  34 38 63 66 22 2c 0a 20 20 20 20 20 20 20 20 22  48cf",.        "
       17391  6e 61 6d 65                                      name
```

