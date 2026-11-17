# Deck box YGO — impressão 3D em ABS

Deck box para **90 cartas com sleeve duplo** (tamanho japonês, 62 × 89 mm): main + extra + side deck, com espaço para **forro de tecido** por dentro.
Tem tampa basculante, **fechamento com ímãs** e trava de clique, **porta-arte trocável** na frente e divisória removível, e imprime **sem suporte**.
Modelada em [SolidCraft](https://github.com/bherbruck/solidcraft), 100 % paramétrica.

![Fechada](images/shot_fechada.png)

## Qual versão imprimir

A caixa é a mesma nas duas versões; muda só a dobradiça.

| | **A — dobradiça integrada** | **B — dobradiça colada** |
|---|---|---|
| Visual | ![A](images/shot_traseira.png) | ![B](images/dobradica_impressa_montada.png) |
| Dobradiça | 5 nós impressos na própria caixa | dobradiça de 50 × 38 mm colada num rebaixo-guia: **de metal** (2") ou a **impressa print-in-place** deste repositório |
| Pino | 61,6 mm de filamento 1,75 (ou aço de 2 mm) | já vem na dobradiça |
| Abertura | até ~168° | até 180° |
| Pasta | [`stl/A-dobradica-integrada`](stl/A-dobradica-integrada) | [`stl/B-dobradica-colada`](stl/B-dobradica-colada) |

Cada pasta tem tudo que precisa ser impresso para aquela versão.

---

## Cartas, folga e forro

O interior é calculado a partir da carta com sleeve, do forro e de uma folga livre. Tudo isso são parâmetros.

| | Medida | Fonte |
|---|---|---|
| Carta Yu-Gi-Oh! | 59 × 86 mm | [Gamegenic](https://www.gamegenic.com/product/japanese-size-prime-sleeves/), [Dragon Shield](https://www.dragonshield.com/collections/japanese-size-sleeves) |
| Sleeve interno (perfect fit) | 59 × 86 mm | [Dragon Shield Perfect Fit](https://www.miniaturemarket.com/at-13051.html) |
| Sleeve externo (tamanho japonês) | 62 × 89 mm | [Gamegenic](https://www.jbhifi.com.au/products/gamegenic-prime-japanese-sized-sleeves-size-code-pink-sleeve-colour-red-62mmx89mm-60-sleeves-per-pack), [Ultimate Guard](https://ultimateguard.com/en/Cortex/Cortex-Sleeves/UGD011179) |
| Espessura por carta com sleeve duplo | ~0,65 mm (varia com a marca) | caixas comerciais: 70 cartas com sleeve duplo em ~46 mm ([guia](https://geekydomain.com/blogs/guides/best-deck-boxes-every-game)) |

**Valores de projeto** (com margem para costura do sleeve e tolerância):

| Parâmetro | Padrão | O que é |
|---|---|---|
| `card_w` × `card_h` | 62,5 × 91 | carta com sleeve, na prática |
| `card_t` | 0,68 | **calibre:** meça 40 cartas com sleeve e divida por 40 |
| `n_cards` | 90 | capacidade |
| `liner_t` | 1,0 | **forro** em todas as faces internas (feltro adesivo de 1 mm; use 0,5 para veludo adesivo e 0 sem forro) |
| `play_x` / `play_y` / `play_z` | 1,5 / 2 / 1,5 | folga livre que sobra depois do forro |

Resultado: interior de **66 × 66,8 × 94,5 mm**.

**Forro:** pode cobrir as paredes, o fundo e o teto da tampa. **Não cubra o topo do lábio** (onde ficam os ímãs) nem o degrau interno da tampa.

## Ímãs

Dois pares de **ímãs de neodímio em disco 5 × 1 mm (N35)** ficam na frente. Os do corpo vão no topo do lábio; os da tampa, no degrau interno logo acima. Com a caixa fechada, ficam face a face a 0,5 mm e puxam a tampa direto para baixo. A trava de clique continua lá.

- São **4 ímãs** por caixa. Para fechar mais firme, empilhe 2 por encaixe (8 ímãs) e mude `mag_stack` para 2.
- Para os ímãs caberem com parede em volta, a **parede da frente tem 9 mm** (as outras têm 2,8).
- **Polaridade:** cole primeiro os 2 ímãs do corpo. Depois apoie cada ímã da tampa em cima do ímã correspondente do corpo: ele "gruda" no lado certo. Marque a face de cima com caneta antes de passar cola no encaixe da tampa.
- Fixe com uma gota de super bonder no fundo do encaixe. O encaixe tem 5,3 mm (`mag_clr` 0,3).

---

## Versão A — dobradiça integrada

![Aberta](images/shot_aberta.png)

### Imprimir

| Arquivo | Orientação | Volume |
|---|---|---|
| `A_corpo.stl` | em pé, fundo na mesa | 86,4 cm³ |
| `A_tampa.stl` | de cabeça para baixo, topo na mesa | 46,1 cm³ |
| `A_divisoria.stl` | deitada | 8,8 cm³ |

Os arquivos já estão na posição de impressão. Total: ~130 g de ABS.

### Montar

1. Corte **61,6 mm de filamento 1,75** (ABS de preferência).
2. Encaixe a tampa e passe o pino por um lado através dos 5 nós.
3. Os nós das pontas são do corpo: uma gota de acetona ali solda o pino no corpo, e a tampa continua girando livre.

**Pino de aço (opcional, mais durável):** use um raio de bicicleta inox 14G (2,0 mm), corda de piano ou eixo retificado de 2 mm.
- No SolidCraft, mude `hole_body` para **2,0** e `hole_lid` para **2,35**, e gere de novo o corpo e a tampa.
- Prenda as pontas com super bonder (acetona não cola metal).

### Calibrar

| Parâmetro | Padrão | Faixa | Efeito |
|---|---|---|---|
| `fit` | 0,3 | 0,2–0,4 | folga da tampa no lábio |
| `ridge_proud` | 0,6 (B: 0,75) | 0,4–0,8 | força do clique |
| `hole_body` | 1,9 | 1,8–2,0 | pino justo nos nós do corpo |
| `hole_lid` | 2,2 | 2,1–2,4 | tampa girando solta |
| `hclr` / `hgap` | 0,35 / 0,4 | 0,3–0,5 | folgas radial e axial da dobradiça |

---

## Versão B — dobradiça colada

| Rebaixo-guia | Com dobradiça de metal | Dobradiça impressa |
|---|---|---|
| ![Guia](images/dobradica_guia.png) | ![Metal](images/dobradica_montada.png) | ![Impressa](images/dobradica_impressa.png) |

A traseira tem um **ressalto de 3 mm** com:
- um **rebaixo de 1,2 mm no tamanho exato da dobradiça**, com 0,4 mm de folga, que serve de guia para ela não ficar torta;
- um **canal para o canudo** do pino;
- **base a 45°**, para imprimir sem suporte.

### Imprimir

| Arquivo | Orientação | Volume |
|---|---|---|
| `B_corpo.stl` | em pé, fundo na mesa | 88,6 cm³ |
| `B_tampa.stl` | de cabeça para baixo, topo na mesa | 48,4 cm³ |
| `B_divisoria.stl` | deitada | 8,8 cm³ |
| `B_dobradica-impressa.stl` | deitada, lado liso na mesa (**só se não for usar a de metal**) | 3,3 cm³ |

Total: ~135 g de ABS.

### Dobradiça de metal

Use uma dobradiça pequena de 2" (50 × 38 mm, chapa de 1,2 mm), dessas vendidas em kit para portinha de armário.

**Meça a sua antes de imprimir a caixa.** Se as medidas não baterem, ajuste estes parâmetros no SolidCraft e gere de novo:

| Parâmetro | Padrão | O que medir |
|---|---|---|
| `hinge_l` | 50 | comprimento ao longo do pino |
| `hinge_w` | 38 | largura total aberta (as duas abas + o canudo) |
| `hinge_t` | 1,2 | espessura da aba (é a profundidade do rebaixo) |
| `barrel_d` | 5 | diâmetro externo do canudo |
| `pocket_clr` | 0,4 | folga em volta (0,3–0,6) |

### Dobradiça impressa (print-in-place)

Ela sai da impressora já montada: 5 nós intercalados, com o pino de 2,6 mm preso dentro dos nós.
- As folgas são de 0,4 mm entre pino e furo e de 0,5 mm entre os nós.
- Os nós que giram têm furo em gota, então o teto do furo sai a 45° e não gruda no pino.

1. **Imprima primeiro só ela** (~3,5 g): as folgas dependem da sua impressora.
2. Deitada, como está no arquivo, sem suporte. Não esmague demais a primeira camada, senão o "pé de elefante" solda os nós.
3. Ao tirar da mesa, **dobre devagar para um lado e para o outro** algumas vezes, até girar livre.
4. Se sair grudada, aumente `pip_clr` (0,45–0,5) e `pip_gap` (0,6) no SolidCraft e gere de novo.

### Colar (metal ou impressa)

1. **Teste antes sem cola.**
   - Metal: o lado em que o canudo fica mais saltado vai para fora.
   - Impressa: o lado liso (o que ficou na mesa) vai para dentro do rebaixo.
2. Lixe as abas e o fundo do rebaixo (lixa 220) e limpe com álcool isopropílico.
3. **Cole com a caixa fechada e travada no clique**, assim a tampa já fica alinhada.
4. Borrife o **ativador de cianoacrilato** nas costas das abas e espere secar uns segundos. Pingue poucas gotas de super bonder no rebaixo, **longe do canal**: cola no canudo trava a dobradiça. Encaixe e pressione por 30 s.
5. Use pouca cola: o vapor do cianoacrilato deixa o ABS esbranquiçado ("blooming").
6. Se um dia descolar, epóxi bicomponente aguenta melhor impacto.

---

## Detalhes de design (nas duas versões)

| Por dentro e porta-arte | Fundo |
|---|---|
| ![Detalhe](images/shot_detalhe.png) | ![Fundo](images/shot_fundo.png) |

- **Porta-arte deslizante:** uma janela com trilhos na frente.
  - A arte entra por cima, pela boca na linha de divisão, e com a **tampa fechada ela não sai**.
  - Imprima a arte do seu deck em papel fotográfico ou cartão de até 0,5 mm e **corte em 46 × 43,5 mm**.
  - Para trocar, abra a tampa e puxe a arte para cima.
  - A boca do porta-arte também serve de apoio para o polegar ao abrir a tampa.
- **Canelado horizontal:** 20 ranhuras em V de 0,6 mm nas laterais. Dá pegada e disfarça as linhas de camada.
- **Linha de sombra:** um degrau de 0,5 × 1,2 mm no topo do corpo, logo abaixo da tampa. Marca a divisão com uma linha escura e esconde desalinhamentos.
- **Fundo:**
  - 4 rebaixos para **pezinhos de silicone autoadesivos de 8 mm**, para a caixa não escorregar na mesa;
  - o texto "DECK BOX / 90 CARTAS · ABS" em baixo-relevo, editável pelos parâmetros `bt_title` e `bt_sub` (coloque o nome do seu deck).

| Parâmetro | Padrão | Efeito |
|---|---|---|
| `art_t` | 0,6 | espessura da fenda da arte (para papel ou cartão de até 0,5 mm) |
| `art_w` / `art_z0` | 46 / 20 | largura da arte e altura do fundo da fenda (altura da arte = 64 − `art_z0`) |
| `fl_n` / `fl_p` / `fl_d` | 20 / 2 / 0,6 | quantidade, passo e profundidade das ranhuras |
| `sg_d` / `sg_h` | 0,5 / 1,2 | profundidade e altura da linha de sombra |
| `bt_title` / `bt_sub` | texto | as duas linhas do texto no fundo |

---

## Adesivo da tampa (opcional)

Gabarito em escala real para envelopar a tampa com vinil adesivo:
- uma **faixa** para as quatro laterais, em **2 partes** porque a volta inteira não cabe numa A4. As duas emendas ficam escondidas na traseira, com **5 mm de sobreposição**: a parte 2 passa por cima da parte 1;
- uma peça para o **topo**.

| Versão A | Versão B |
|---|---|
| ![Adesivo A](images/adesivo_tampa_A.png) | ![Adesivo B](images/adesivo_tampa_B.png) |

**Arquivos:** `adesivo/adesivo_tampa_A.svg` e `adesivo/adesivo_tampa_B.svg`.
- São A4 paisagem, em mm, com as camadas Arte, Sangria, Área segura, Guias, Corte e Textos.
- Abrem no Inkscape, Illustrator, Canva e nos programas de plotter de recorte (Silhouette, Cricut).

**Medidas:**
- Faixa: 293,5 mm de contorno × 32,5 mm de altura. A parte 1 tem 261,7 mm e a parte 2, 41,8 mm.
- Topo: 68,6 × 75,6 mm, cantos R2,5.
- Embaixo da faixa, na parte da traseira, há um recorte para a dobradiça. Na versão B sobra uma tira de 7,3 mm acima do ressalto.

**Como usar:**
1. Monte a arte até a linha azul (sangria) e deixe textos e detalhes dentro da verde (área segura).
2. Imprima em **tamanho real** (100 %, sem "ajustar à página") e confira a régua de 50 mm.
3. Cole primeiro o topo, centralizado na face plana dentro do chanfro.
4. Depois a parte 1 da faixa: comece no meio da traseira, com a borda de cima logo abaixo do chanfro do topo, e dê a volta até o canto traseiro direito. Os cantos arredondados (R4) aceitam o vinil normalmente.
5. Por último a parte 2, fechando a traseira por cima das duas pontas da parte 1.
6. Se puder, aplique laminação por cima, para durar mais.

Mudou alguma medida da caixa? Ajuste os números no começo de `adesivo/gerar_guia.py` e rode:

```bash
python adesivo/gerar_guia.py
```

---

## Configuração de impressão (ABS, vale para tudo)

| | |
|---|---|
| Câmara | fechada, sem corrente de ar |
| Temperatura | mesa 100–110 °C, bico 240–250 °C |
| Ventoinha | 0–20 % (30–40 % nas pontes) |
| Camada | 0,2 mm |
| Perímetros | **6** (as paredes ficam maciças) |
| Topo e fundo | 5 camadas |
| Preenchimento | 15 % gyroid |
| Brim | **5–8 mm** no corpo e na tampa; a divisória e a dobradiça não precisam |
| Suporte | nenhum |
| Costura | atrás |

O topo da tampa e o fundo do corpo ficam com a textura da mesa (PEI texturizado ou vidro).

---

## Medidas e mecanismos

| | mm |
|---|---|
| Externa (fechada) | 71,6 × 78,6 × 98,5 (B: 81,6 de profundidade, por causa do ressalto) |
| Interna | 66 × 66,8 × 94,5 |
| Paredes / fundo / topo | 2,8 (frente 9,0) / 2,0 / 2,0 |
| Divisão corpo/tampa | 64 (as cartas ficam ~25 mm acima do lábio para pegar) |

- **Ímãs:** 2 pares de 5 × 1 mm na frente, face a face a 0,5 mm com a caixa fechada.
- **Trava de clique:** um ressalto de 0,6 mm no lábio frontal encaixa numa ranhura escondida na tampa. A interferência é de 0,3 mm (0,45 mm na versão B, ajustada depois do teste impresso), só no primeiro grau de abertura.
- **Lábio e saia:** o lábio de 5 mm do corpo entra na saia da tampa com 0,3 mm de folga. Tem chanfro de entrada e um vinco de 0,4 mm na linha de divisão.
- **Dobradiça integrada (A):** 5 nós com reforços a 45° e furos em gota, então imprime sem suporte.
- **Chanfros** nas bordas que tocam a mesa (0,8 no corpo, 1,0 na tampa), contra o pé de elefante.

![Explodida (A): tampa, arte saindo do porta-arte, divisória e pino](images/shot_explodida.png)

## Verificação

Feita com booleanas exatas do SolidCraft (`inspect.interference`):

| | A | B |
|---|---|---|
| Caixa fechada (corpo × tampa) | 0 de interferência | 0 de interferência |
| 90 cartas (62,5 × 61,2 × 91) **com 1 mm de forro em volta** + divisória | cabem: 0,75 mm de folga de cada lado e 1,5 mm em cima | igual |
| 4 ímãs 5 × 1 mm nos encaixes | assentam sem tocar; 0,5 mm entre os pares | igual |
| Arte de 46 × 43,5 × 0,5 no porta-arte | cabe sem tocar | cabe sem tocar |
| Arte empurrada 1 mm para cima | a tampa bloqueia (fica presa) | a tampa bloqueia (fica presa) |
| Pino / dobradiça montada | pino de 1,75 sem tocar | dobradiça de metal e impressa sem tocar |
| Giro da tampa | clique a 1°, livre de 2° a 168°, batente a ~169° | clique a 1°, livre até 180° |
| Dobradiça impressa sozinha | — | plana sem as abas se tocarem, dobra livre até 180° |

## Editar o modelo

Os arquivos editáveis estão em `cad/A-dobradica-integrada/` e `cad/B-dobradica-colada/`:
- `.sc` — projeto do SolidCraft, com os parâmetros de calibração marcados como favoritos;
- `.step` — para abrir em qualquer CAD;
- `_build.json` — script que reconstrói o modelo do zero.

Para mudar o tamanho (outro sleeve, mais cartas, outro forro), edite `card_w`, `card_h`, `card_t`, `n_cards` ou `liner_t`: o interior é calculado a partir deles.

Edite no app, em Parâmetros, ou reconstrua pela linha de comando:

```bash
solidcraft-cli run cad/A-dobradica-integrada/A_deckbox_build.json --save cad/A-dobradica-integrada/A_deckbox.sc
```

Depois exporte cada peça em STL pelo app. O modelo fica na posição de montagem, então vire a tampa de cabeça para baixo no fatiador.
