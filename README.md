# Deck box YGO — impressão 3D em ABS

Deck box para **90 cartas com sleeve duplo** (tamanho japonês, 62 × 89 mm): main + extra + side deck.
Tem tampa basculante, trava de clique escondida, **porta-arte trocável** na frente e divisória removível, e imprime **sem suporte**.
Modelada em [SolidCraft](https://github.com/bherbruck/solidcraft), 100 % paramétrica.

![Fechada](images/shot_fechada.png)

## Qual versão imprimir

A caixa é a mesma nas duas versões; muda só a dobradiça.

| | **A — dobradiça integrada** | **B — dobradiça colada** |
|---|---|---|
| Visual | ![A](images/shot_traseira.png) | ![B](images/dobradica_impressa_montada.png) |
| Dobradiça | 5 nós impressos na própria caixa | dobradiça de 50 × 38 mm colada num rebaixo-guia: **de metal** (2") ou a **impressa print-in-place** deste repositório |
| Pino | 59,6 mm de filamento 1,75 (ou aço de 2 mm) | já vem na dobradiça |
| Abertura | até ~168° | até 180° |
| Pasta | [`stl/A-dobradica-integrada`](stl/A-dobradica-integrada) | [`stl/B-dobradica-colada`](stl/B-dobradica-colada) |

Cada pasta tem tudo que precisa ser impresso para aquela versão.

---

## Versão A — dobradiça integrada

![Aberta](images/shot_aberta.png)

### Imprimir

| Arquivo | Orientação | Volume |
|---|---|---|
| `A_corpo.stl` | em pé, fundo na mesa | 52,8 cm³ |
| `A_tampa.stl` | de cabeça para baixo, topo na mesa | 28,1 cm³ |
| `A_divisoria.stl` | deitada | 8,6 cm³ |

Os arquivos já estão na posição de impressão. Total: ~90 g de ABS.

### Montar

1. Corte **59,6 mm de filamento 1,75** (ABS de preferência).
2. Encaixe a tampa e passe o pino por um lado através dos 5 nós.
3. Os nós das pontas são do corpo: uma gota de acetona ali solda o pino no corpo, e a tampa continua girando livre.

**Pino de aço (opcional, mais durável):** use um raio de bicicleta inox 14G (2,0 mm), corda de piano ou eixo retificado de 2 mm.
- No SolidCraft, mude `hole_body` para **2,0** e `hole_lid` para **2,35**, e gere de novo o corpo e a tampa.
- Prenda as pontas com super bonder (acetona não cola metal).

### Calibrar

| Parâmetro | Padrão | Faixa | Efeito |
|---|---|---|---|
| `fit` | 0,3 | 0,2–0,4 | folga da tampa no lábio |
| `ridge_proud` | 0,6 (B: 0,7) | 0,4–0,8 | força do clique |
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
| `B_corpo.stl` | em pé, fundo na mesa | 55,1 cm³ |
| `B_tampa.stl` | de cabeça para baixo, topo na mesa | 30,5 cm³ |
| `B_divisoria.stl` | deitada | 8,6 cm³ |
| `B_dobradica-impressa.stl` | deitada, lado liso na mesa (**só se não for usar a de metal**) | 3,3 cm³ |

Total: ~95 g de ABS.

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
- **Nervuras internas:** 4 filetes verticais nas laterais de dentro. Centralizam o deck e reduzem o atrito ao tirar as cartas. A divisória foi estreitada para 62,2 mm, para passar entre elas em qualquer posição.
- **Fundo:**
  - 4 rebaixos para **pezinhos de silicone autoadesivos de 8 mm**, para a caixa não escorregar na mesa;
  - o texto "DECK BOX / 90 CARTAS · ABS" em baixo-relevo, editável pelos parâmetros `bt_title` e `bt_sub` (coloque o nome do seu deck).

| Parâmetro | Padrão | Efeito |
|---|---|---|
| `art_t` | 0,6 | espessura da fenda da arte (para papel ou cartão de até 0,5 mm) |
| `art_w` / `art_z0` | 46 / 20 | largura da arte e altura do fundo da fenda (altura da arte = 64 − `art_z0`) |
| `fl_n` / `fl_p` / `fl_d` | 20 / 2 / 0,6 | quantidade, passo e profundidade das ranhuras |
| `sg_d` / `sg_h` | 0,5 / 1,2 | profundidade e altura da linha de sombra |
| `rib_p` | 0,5 | quanto as nervuras avançam para dentro |
| `bt_title` / `bt_sub` | texto | as duas linhas do texto no fundo |

---

## Adesivo da tampa (opcional)

Gabarito em escala real para envelopar a tampa com vinil adesivo. São duas peças:
- uma **faixa** para as quatro laterais, com a emenda escondida na traseira e **5 mm de sobreposição** (o fim passa por cima do começo);
- uma peça para o **topo**.

| Versão A | Versão B |
|---|---|
| ![Adesivo A](images/adesivo_tampa_A.png) | ![Adesivo B](images/adesivo_tampa_B.png) |

**Arquivos:** `adesivo/adesivo_tampa_A.svg` e `adesivo/adesivo_tampa_B.svg`.
- São A4 paisagem, em mm, com as camadas Arte, Sangria, Área segura, Guias, Corte e Textos.
- Abrem no Inkscape, Illustrator, Canva e nos programas de plotter de recorte (Silhouette, Cricut).

**Medidas:**
- Faixa: 272,5 × 28,5 mm. Topo: 66,6 × 64,6 mm, cantos R2,5.
- Embaixo da faixa, na parte da traseira, há um recorte para a dobradiça. Na versão B sobra só uma tira de 3,3 mm acima do ressalto.

**Como usar:**
1. Monte a arte até a linha azul (sangria) e deixe textos e detalhes dentro da verde (área segura).
2. Imprima em **tamanho real** (100 %, sem "ajustar à página") e confira a régua de 50 mm.
3. Cole primeiro o topo, centralizado na face plana dentro do chanfro.
4. Depois a faixa: comece no meio da traseira, com a borda de cima logo abaixo do chanfro do topo, e dê a volta. Os cantos arredondados (R4) aceitam o vinil normalmente.
5. Se puder, aplique laminação por cima, para durar mais.

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
| Externa (fechada) | 69,6 × 67,6 × 94,5 (B: 70,6 de profundidade, por causa do ressalto) |
| Interna | 64 × 62 × 90,5 |
| Paredes / fundo / topo | 2,8 / 2,0 / 2,0 |
| Divisão corpo/tampa | 64 (as cartas ficam ~22 mm acima do lábio para pegar) |

- **Trava de clique:** um ressalto de 0,6 mm no lábio frontal encaixa numa ranhura escondida na tampa. A interferência é de 0,3 mm (0,4 mm na versão B), só nos primeiros 1–2° de abertura.
- **Lábio e saia:** o lábio de 5 mm do corpo entra na saia da tampa com 0,3 mm de folga. Tem chanfro de entrada e um vinco de 0,4 mm na linha de divisão.
- **Dobradiça integrada (A):** 5 nós com reforços a 45° e furos em gota, então imprime sem suporte.
- **Chanfros** nas bordas que tocam a mesa (0,8 no corpo, 1,0 na tampa), contra o pé de elefante.

![Explodida (A): tampa, arte saindo do porta-arte, divisória e pino](images/shot_explodida.png)

## Verificação

Feita com booleanas exatas do SolidCraft (`inspect.interference`):

| | A | B |
|---|---|---|
| Caixa fechada (corpo × tampa) | 0 de interferência | 0 de interferência |
| 90 cartas (62 × 55,8 × 89) + divisória | 0 | 0 |
| Divisória em cima das nervuras | passa | passa |
| Arte de 46 × 43,5 × 0,5 no porta-arte | cabe sem tocar | cabe sem tocar |
| Arte empurrada 1 mm para cima | a tampa bloqueia (fica presa) | a tampa bloqueia (fica presa) |
| Pino / dobradiça montada | pino de 1,75 sem tocar | dobradiça de metal e impressa sem tocar |
| Giro da tampa | clique a 1–2°, livre de 3° a 168°, batente a ~169° | clique a 1–2°, livre até 180° |
| Dobradiça impressa sozinha | — | plana sem as abas se tocarem, dobra livre até 180° |

## Editar o modelo

Os arquivos editáveis estão em `cad/A-dobradica-integrada/` e `cad/B-dobradica-colada/`:
- `.sc` — projeto do SolidCraft, com os parâmetros de calibração marcados como favoritos;
- `.step` — para abrir em qualquer CAD;
- `_build.json` — script que reconstrói o modelo do zero.

Para mudar o tamanho (outro sleeve, mais cartas), edite `in_x`, `in_y` ou `in_z`.

Edite no app, em Parâmetros, ou reconstrua pela linha de comando:

```bash
solidcraft-cli run cad/A-dobradica-integrada/A_deckbox_build.json --save cad/A-dobradica-integrada/A_deckbox.sc
```

Depois exporte cada peça em STL pelo app. O modelo fica na posição de montagem, então vire a tampa de cabeça para baixo no fatiador.
