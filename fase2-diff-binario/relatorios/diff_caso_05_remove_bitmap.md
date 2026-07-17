# Diff ZCF: `caso_01_add_bitmap_jpeg.cdr` vs `caso_05_remove_bitmap.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | `content/data/Bitmaps.dat` |
| So na variante | — |
| Identicos | `META-INF/links.xml`, `content/data/masterPage.dat`, `mimetype` |
| Alterados | `META-INF/container.xml`, `META-INF/metadata.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/page1.dat`, `content/dataFileList.dat`, `content/root.dat`, `previews/page1.png`, `previews/thumbnail.png`, `styles/document.cdss` |

### `content/data/Bitmaps.dat` — REMOVIDO na variante (tinha 2693386 bytes)

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

### `META-INF/metadata.xml` — ALTERADO (8678 -> 8680 bytes)

Tamanhos diferentes (delta +2). Prefixo comum: 1181 bytes; sufixo comum: 499 bytes.
Miolo divergente: base [1181..8179) = 6998 bytes, variante [1181..8181) = 7000 bytes.

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
        1181  39 33 37 32 66 61 37 66 2d 35 62 37 38 2d 34 33  9372fa7f-5b78-43
        1197  38 34 2d 38 62 63 36 2d 32 36 32 35 61 32 34 61  84-8bc6-2625a24a
        1213  66 36 36 65 3c 2f 64 63 3a 69 64 65 6e 74 69 66  f66e</dc:identif
        1229  69 65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20  ier>.           
        1245  20 3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65   <xmpMM:Instance
  ... (regiao truncada; tamanho real 96 bytes)
```

### `META-INF/textinfo.xml` — ALTERADO (725 -> 673 bytes)

Tamanhos diferentes (delta -52). Prefixo comum: 353 bytes; sufixo comum: 320 bytes.
Miolo divergente: base [353..405) = 52 bytes, variante [353..353) = 0 bytes.

```
base (inicio do miolo):
         337  20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20                  
         353  20 20 20 20 3c 72 64 66 3a 6c 69 3e 66 6f 6e 74      <rdf:li>font
         369  65 5f 62 61 73 65 2e 6a 70 67 3c 2f 72 64 66 3a  e_base.jpg</rdf:
         385  6c 69 3e 0a 20 20 20 20 20 20 20 20 20 20 20 20  li>.            
         401  20 20 20 20 3c 2f 72 64 66 3a 42 61 67 3e 0a 20      </rdf:Bag>. 
         417  20 20 20 20                                          
variante (inicio do miolo):
         337  20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20                  
         353  3c 2f 72 64 66 3a 42 61 67 3e 0a 20 20 20 20 20  </rdf:Bag>.     
```

### `color/color.xml` — ALTERADO (250 -> 251 bytes)

Tamanhos diferentes (delta +1). Prefixo comum: 135 bytes; sufixo comum: 112 bytes.
Miolo divergente: base [135..138) = 3 bytes, variante [135..139) = 4 bytes.

```
base (inicio do miolo):
         119  3e 3c 48 61 73 52 67 62 4f 62 6a 65 63 74 73 3e  ><HasRgbObjects>
         135  74 72 75 65 3c 2f 48 61 73 52 67 62 4f 62 6a 65  true</HasRgbObje
         151  63 74 73                                         cts
variante (inicio do miolo):
         119  3e 3c 48 61 73 52 67 62 4f 62 6a 65 63 74 73 3e  ><HasRgbObjects>
         135  66 61 6c 73 65 3c 2f 48 61 73 52 67 62 4f 62 6a  false</HasRgbObj
         151  65 63 74 73                                      ects
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
          38  32 30 38 61 38 34 31 31 2d 66 39 65 35 2d 34 31  208a8411-f9e5-41
          54  32 39 2d 39 33 34 61 2d 35 35 39 64 30 30 66 64  29-934a-559d00fd
          70  38 65 39 30 22 20 6e 61 6d 65 3d 22 50 61 6c 65  8e90" name="Pale
          86  74 61 20 64                                      ta d
```

### `content/data/data1.dat` — ALTERADO (22640 -> 22357 bytes)

Tamanhos diferentes (delta -283). Prefixo comum: 21660 bytes; sufixo comum: 62 bytes.
Miolo divergente: base [21660..22578) = 918 bytes, variante [21660..22295) = 635 bytes.

```
base (inicio do miolo):
       21644  77 00 4d 00 6f 00 64 00 65 00 00 00 30 00 00 00  w.M.o.d.e...0...
       21660  10 81 f1 ff a3 12 f7 ff 10 bd fd ff a3 d6 ea ff  ................
       21676  01 00 00 00 13 00 00 00 01 00 00 00 00 00 00 00  ................
       21692  04 00 07 00 07 00 00 00 00 00 06 00 00 00 4e 00  ..............N.
       21708  61 00 6d 00 65 00 00 00 77 00 65 00 62 00 63 00  a.m.e...w.e.b.c.
       21724  67 00 6d 00 00 00 47 00 65 00 6e 00 65 00 72 00  g.m...G.e.n.e.r.
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
       21644  77 00 4d 00 6f 00 64 00 65 00 00 00 30 00 00 00  w.M.o.d.e...0...
       21660  68 8a f4 ff 4b 09 f4 ff f8 b9 fd ff fb e6 ed ff  h...K...........
       21676  01 00 00 00 13 00 00 00 01 00 00 00 00 00 00 00  ................
       21692  04 00 07 00 07 00 00 00 00 00 06 00 00 00 4e 00  ..............N.
       21708  61 00 6d 00 65 00 00 00 77 00 65 00 62 00 63 00  a.m.e...w.e.b.c.
       21724  67 00 6d 00 00 00 47 00 65 00 6e 00 65 00 72 00  g.m...G.e.n.e.r.
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/page1.dat` — ALTERADO (2694 -> 1617 bytes)

Tamanhos diferentes (delta -1077). Prefixo comum: 16 bytes; sufixo comum: 410 bytes.
Miolo divergente: base [16..2284) = 2268 bytes, variante [16..1207) = 1191 bytes.

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
          16  50 8e f4 ff 02 00 00 00 02 00 00 00 e3 ea ed ff  P...............
          32  50 8e f4 ff 02 00 00 00 02 00 00 00 e3 ea ed ff  P...............
          48  68 8a f4 ff 02 00 00 00 02 00 00 00 fb e6 ed ff  h...............
          64  f8 df 80 7b af c7 7f 41 a3 ba f2 f0 cd 18 c9 c2  ...{...A........
          80  7b 00 00 00 04 00 00 00 14 00 00 00 28 00 00 00  {...........(...
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/dataFileList.dat` — ALTERADO (46 -> 34 bytes)

Tamanhos diferentes (delta -12). Prefixo comum: 0 bytes; sufixo comum: 34 bytes.
Miolo divergente: base [0..12) = 12 bytes, variante [0..0) = 0 bytes.

```
base (inicio do miolo):
           0  42 69 74 6d 61 70 73 2e 64 61 74 0a 64 61 74 61  Bitmaps.dat.data
          16  31 2e 64 61 74 0a 6d 61 73 74 65 72              1.dat.master
variante (inicio do miolo):
           0  64 61 74 61 31 2e 64 61 74 0a 6d 61 73 74 65 72  data1.dat.master
```

### `content/root.dat` — ALTERADO (2004 -> 1680 bytes)

Tamanhos diferentes (delta -324). Prefixo comum: 4 bytes; sufixo comum: 6 bytes.
Miolo divergente: base [4..1998) = 1994 bytes, variante [4..1674) = 1670 bytes.

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
           0  52 49 46 46 88 06 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  60 01 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  `...doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/page1.png` — ALTERADO (2034 -> 829 bytes)

Tamanhos diferentes (delta -1205). Prefixo comum: 85 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [85..2022) = 1937 bytes, variante [85..817) = 732 bytes.

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
          85  02 d2 49 44 41 54 78 5e ed d2 3b 4a 43 01 14 45  ..IDATx^..;JC..E
         101  51 c7 14 21 7e 50 10 3b 5b ed b4 13 67 e2 a7 d0  Q..!~P.;[...g...
         117  42 51 04 a7 a0 e0 24 74 20 8e c0 2e 90 22 85 b6  BQ....$t ...."..
         133  12 70 07 e4 15 0f 59 8b 53 dd ea 16 7b ed 0b 7e  .p....Y.S...{..~
         149  b7 b6 7c 80 1f f4 41 d1 07 45 1f 14 7d 50 f4 41  ..|...A..E..}P.A
  ... (regiao truncada; tamanho real 96 bytes)
```

### `previews/thumbnail.png` — ALTERADO (10051 -> 935 bytes)

Tamanhos diferentes (delta -9116). Prefixo comum: 19 bytes; sufixo comum: 12 bytes.
Miolo divergente: base [19..10039) = 10020 bytes, variante [19..923) = 904 bytes.

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
          19  7f 00 00 01 00 08 02 00 00 00 d4 52 e1 24 00 00  ...........R.$..
          35  00 01 73 52 47 42 00 ae ce 1c e9 00 00 00 04 67  ..sRGB.........g
          51  41 4d 41 00 00 b1 8f 0b fc 61 05 00 00 00 09 70  AMA......a.....p
          67  48 59 73 00 00 0e c3 00 00 0e c3 01 c7 6f a8 64  HYs..........o.d
          83  00 00 03 3c 49 44 41 54 78 5e ed d4 41 11 c2 30  ...<IDATx^..A..0
  ... (regiao truncada; tamanho real 96 bytes)
```

### `styles/document.cdss` — ALTERADO (17499 -> 17499 bytes)

Mesmo tamanho; 1 regiao(oes) alterada(s):

**Regiao 1: offset 17344, 35 byte(s)**
```
base:
       17328  20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22 35        "guid": "5
       17344  64 32 66 36 63 31 31 2d 63 33 38 61 2d 34 65 64  d2f6c11-c38a-4ed
       17360  33 2d 62 36 62 37 2d 65 34 32 31 66 31 36 37 30  3-b6b7-e421f1670
       17376  35 37 63 22 2c 0a 20 20 20 20 20 20 20 20 22 6e  57c",.        "n
       17392  61 6d 65                                         ame
variante:
       17328  20 20 20 20 20 20 22 67 75 69 64 22 3a 20 22 35        "guid": "5
       17344  32 65 65 30 32 62 62 2d 31 61 39 38 2d 34 36 61  2ee02bb-1a98-46a
       17360  31 2d 62 62 62 39 2d 36 33 64 61 35 39 66 64 34  1-bbb9-63da59fd4
       17376  37 62 62 22 2c 0a 20 20 20 20 20 20 20 20 22 6e  7bb",.        "n
       17392  61 6d 65                                         ame
```

