# Diff ZCF: `caso_12_dois_objetos.cdr` vs `caso_13_grupo.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | — |
| Identicos | `META-INF/container.xml`, `META-INF/links.xml`, `META-INF/textinfo.xml`, `color/color.xml`, `content/data/masterPage.dat`, `content/dataFileList.dat`, `mimetype`, `previews/page1.png`, `previews/thumbnail.png` |
| Alterados | `META-INF/metadata.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/page1.dat`, `content/root.dat`, `styles/document.cdss` |

### `META-INF/metadata.xml` — ALTERADO (8605 -> 8679 bytes)

Tamanhos diferentes (delta +74). Prefixo comum: 1182 bytes; sufixo comum: 4327 bytes.
Miolo divergente: base [1182..4278) = 3096 bytes, variante [1182..4352) = 3170 bytes.

```
base (inicio do miolo):
        1166  3c 64 63 3a 69 64 65 6e 74 69 66 69 65 72 3e 34  <dc:identifier>4
        1182  65 63 64 30 64 37 64 2d 63 36 65 63 2d 34 39 39  ecd0d7d-c6ec-499
        1198  35 2d 61 37 33 38 2d 35 33 30 36 66 32 36 36 65  5-a738-5306f266e
        1214  66 32 66 3c 2f 64 63 3a 69 64 65 6e 74 69 66 69  f2f</dc:identifi
        1230  65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20 20  er>.            
        1246  3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65 49  <xmpMM:InstanceI
  ... (regiao truncada; tamanho real 96 bytes)
variante (inicio do miolo):
        1166  3c 64 63 3a 69 64 65 6e 74 69 66 69 65 72 3e 34  <dc:identifier>4
        1182  33 63 31 38 62 32 36 2d 33 62 64 34 2d 34 39 30  3c18b26-3bd4-490
        1198  35 2d 61 32 63 39 2d 36 34 35 37 61 38 37 33 65  5-a2c9-6457a873e
        1214  37 65 35 3c 2f 64 63 3a 69 64 65 6e 74 69 66 69  7e5</dc:identifi
        1230  65 72 3e 0a 20 20 20 20 20 20 20 20 20 20 20 20  er>.            
        1246  3c 78 6d 70 4d 4d 3a 49 6e 73 74 61 6e 63 65 49  <xmpMM:InstanceI
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
          38  63 63 31 30 30 66 35 62 2d 32 34 34 63 2d 34 39  cc100f5b-244c-49
          54  62 32 2d 39 34 39 66 2d 30 30 32 63 65 65 32 38  b2-949f-002cee28
          70  33 66 37 65 22 20 6e 61 6d 65 3d 22 50 61 6c 65  3f7e" name="Pale
          86  74 61 20 64 65 20 64 6f 63 75 6d 65 6e 74 6f 73  ta de documentos
         102  22 3e 3c 63 6f 6c 6f 72 73 3e 3c 70 61 67 65 3e  "><colors><page>
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/data1.dat` — ALTERADO (22509 -> 22746 bytes)

Tamanhos diferentes (delta +237). Prefixo comum: 22284 bytes; sufixo comum: 209 bytes.
Miolo divergente: base [22284..22300) = 16 bytes, variante [22284..22537) = 253 bytes.

```
base (inicio do miolo):
       22268  00 00 00 00 01 00 00 00 0b 00 00 00 10 00 00 00  ................
       22284  c4 32 fe 03 86 cf b8 42 af 4b 11 5a 71 d5 fe 5b  .2.....B.K.Zq..[
       22300  03 00 00 00 04 00 00 00 40 4b 4c 00 02 00 00 00  ........@KL.....
variante (inicio do miolo):
       22268  00 00 00 00 01 00 00 00 0b 00 00 00 10 00 00 00  ................
       22284  47 95 32 cf 29 bd ba 4d a1 9a 20 98 fe 2f a9 41  G.2.)..M.. ../.A
       22300  03 00 00 00 04 00 00 00 40 4b 4c 00 02 00 00 00  ........@KL.....
       22316  2b 00 00 00 01 0c 00 00 00 02 00 05 00 00 00 00  +...............
       22332  00 00 00 00 64 07 10 00 00 00 00 00 00 00 00 00  ....d...........
       22348  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01  ................
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/data/page1.dat` — ALTERADO (2305 -> 2405 bytes)

Tamanhos diferentes (delta +100). Prefixo comum: 654 bytes; sufixo comum: 1110 bytes.
Miolo divergente: base [654..1195) = 541 bytes, variante [654..1295) = 641 bytes.

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
         654  66 c4 9d a2 68 76 8e 4d a2 8a be 2d d4 2b 32 49  f...hv.M...-.+2I
         670  50 8e f4 ff f3 d5 f7 ff 60 79 fe ff e3 ea ed ff  P.......`y......
         686  50 8e f4 ff f3 d5 f7 ff 60 79 fe ff e3 ea ed ff  P.......`y......
         702  68 8a f4 ff db d9 f7 ff 48 7d fe ff fb e6 ed ff  h.......H}......
         718  18 00 00 00 00 00 00 00 14 00 00 00 18 00 00 00  ................
  ... (regiao truncada; tamanho real 96 bytes)
```

### `content/root.dat` — ALTERADO (2028 -> 2220 bytes)

Tamanhos diferentes (delta +192). Prefixo comum: 4 bytes; sufixo comum: 7 bytes.
Miolo divergente: base [4..2021) = 2017 bytes, variante [4..2213) = 2209 bytes.

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
           0  52 49 46 46 a4 08 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  d8 01 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  ....doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
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
       17343  32 38 32 61 33 32 64 38 2d 36 62 62 38 2d 34 64  282a32d8-6bb8-4d
       17359  64 39 2d 39 39 31 62 2d 38 33 35 62 31 35 31 64  d9-991b-835b151d
       17375  63 37 30 62 22 2c 0a 20 20 20 20 20 20 20 20 22  c70b",.        "
       17391  6e 61 6d 65                                      name
```

