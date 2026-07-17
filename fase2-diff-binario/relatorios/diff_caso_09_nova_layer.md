# Diff ZCF: `caso_00_base.cdr` vs `caso_09_nova_layer.cdr`

## Resumo

| Situacao | Membros |
|---|---|
| So no base | — |
| So na variante | — |
| Identicos | `META-INF/container.xml`, `META-INF/links.xml`, `color/color.xml`, `content/dataFileList.dat`, `mimetype`, `previews/page1.png`, `previews/thumbnail.png` |
| Alterados | `META-INF/metadata.xml`, `META-INF/textinfo.xml`, `color/docPalette.xml`, `content/data/data1.dat`, `content/data/masterPage.dat`, `content/data/page1.dat`, `content/root.dat`, `styles/document.cdss` |

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

### `META-INF/textinfo.xml` — ALTERADO (673 -> 722 bytes)

Tamanhos diferentes (delta +49). Prefixo comum: 504 bytes; sufixo comum: 169 bytes.
Miolo divergente: base [504..504) = 0 bytes, variante [504..553) = 49 bytes.

```
base (inicio do miolo):
         488  20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20                  
         504  3c 2f 72 64 66 3a 42 61 67 3e 0a 20 20 20 20 20  </rdf:Bag>.     
variante (inicio do miolo):
         488  20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20                  
         504  20 20 20 20 3c 72 64 66 3a 6c 69 3e 43 61 6d 61      <rdf:li>Cama
         520  64 61 54 65 73 74 65 3c 2f 72 64 66 3a 6c 69 3e  daTeste</rdf:li>
         536  0a 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20  .               
         552  20 3c 2f 72 64 66 3a 42 61 67 3e 0a 20 20 20 20   </rdf:Bag>.    
         568  20                                                
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
          38  61 32 39 32 64 62 34 32 2d 38 62 33 31 2d 34 65  a292db42-8b31-4e
          54  32 36 2d 38 33 33 62 2d 66 63 38 66 39 36 61 62  26-833b-fc8f96ab
          70  61 38 61 61 22 20 6e 61 6d 65 3d 22 50 61 6c 65  a8aa" name="Pale
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

### `content/data/page1.dat` — ALTERADO (1545 -> 1764 bytes)

Tamanhos diferentes (delta +219). Prefixo comum: 80 bytes; sufixo comum: 43 bytes.
Miolo divergente: base [80..1502) = 1422 bytes, variante [80..1721) = 1641 bytes.

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

### `content/root.dat` — ALTERADO (1680 -> 1776 bytes)

Tamanhos diferentes (delta +96). Prefixo comum: 4 bytes; sufixo comum: 6 bytes.
Miolo divergente: base [4..1674) = 1670 bytes, variante [4..1770) = 1766 bytes.

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
           0  52 49 46 46 e8 06 00 00 43 44 52 54 66 76 65 72  RIFF....CDRTfver
          16  10 00 00 00 ff ff ff ff 08 00 00 00 28 0a 01 00  ............(...
          32  00 00 1a 00 76 72 73 6e 10 00 00 00 ff ff ff ff  ....vrsn........
          48  02 00 00 00 28 0a 00 00 00 00 00 00 4c 49 53 54  ....(.......LIST
          64  60 01 00 00 64 6f 63 20 6d 63 66 67 10 00 00 00  `...doc mcfg....
          80  00 00 00 00 08 1f 00 00 00 00 00 00 00 00 00 00  ................
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
       17343  30 62 37 30 63 39 65 39 2d 34 30 39 39 2d 34 32  0b70c9e9-4099-42
       17359  61 62 2d 39 66 32 30 2d 37 30 33 35 30 30 62 62  ab-9f20-703500bb
       17375  34 33 39 66 22 2c 0a 20 20 20 20 20 20 20 20 22  439f",.        "
       17391  6e 61 6d 65                                      name
```

