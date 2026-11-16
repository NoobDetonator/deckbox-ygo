# Deck box YGO — impressão 3D em ABS

Deck box para **90 cartas com sleeve duplo** (tamanho japonês, 62 × 89 mm): main + extra + side deck.
Tampa basculante com dobradiça de 5 nós e pino de filamento, trava de clique escondida, divisória removível.
Imprime **sem suporte**. Modelada em [SolidCraft](https://github.com/bherbruck/solidcraft), 100 % paramétrica.

![Fechada](images/shot_fechada.png)

| Aberta (90 cartas + divisória) | Explodida | Dobradiça |
|---|---|---|
| ![Aberta](images/shot_aberta.png) | ![Explodida](images/shot_explodida.png) | ![Traseira](images/shot_traseira.png) |

![Detalhe da trava, do cavado do polegar e da etiqueta](images/shot_detalhe.png)

## Medidas

| | mm |
|---|---|
| Externa (fechada) | 69,6 × 67,6 × 94,5 |
| Interna | 64 × 62 × 90,5 |
| Paredes / fundo / topo | 2,8 / 2,0 / 2,0 |
| Divisão corpo/tampa | 64 (as cartas ficam ~22 mm acima do lábio para pegar) |

## Peças

| Arquivo | Orientação de impressão | Volume |
|---|---|---|
| `stl/deckbox_corpo.stl` | em pé, fundo na mesa | 55,4 cm³ |
| `stl/deckbox_tampa.stl` | de cabeça para baixo, topo na mesa | 28,1 cm³ |
| `stl/deckbox_divisoria.stl` | deitada | 8,7 cm³ |
| Pino | 59,6 mm de filamento 1,75 | — |

Fonte em `cad/`: `deckbox_ygo.sc` (SolidCraft), `deckbox_ygo.step` (montagem, para qualquer CAD) e `deckbox_build.json` (script que reconstrói o modelo do zero).

## Mecanismos

- **Dobradiça:** 5 nós intercalados (corpo, tampa, corpo, tampa, corpo) com reforços a 45° e furos em gota, então imprime sem suporte. A tampa abre livre até ~168° e para nos reforços.
- **Trava de clique:** um ressalto de 0,6 mm no lábio frontal encaixa numa ranhura escondida na saia da tampa. A interferência fica em 0,3 mm só nos primeiros 2° de abertura.
- **Lábio e saia:** o lábio de 5 mm do corpo entra na saia da tampa com folga de 0,3 mm. Tem chanfro de entrada e um vinco de 0,4 mm na linha de divisão.
- **Cavado do polegar** na frente, logo abaixo da tampa, para abrir com uma mão.
- **Rebaixo de 44 × 30 × 0,6 mm** na frente, para adesivo com o nome do deck.
- **Chanfros** nas bordas que tocam a mesa (0,8 no corpo, 1,0 na tampa), contra o "pé de elefante".

## Impressão em ABS

- Câmara fechada, sem corrente de ar. Mesa 100–110 °C, bico 240–250 °C, ventoinha 0–20 % (30–40 % nas pontes).
- Camada 0,2 mm, **6 perímetros**, 5 camadas de topo e de fundo, 15 % gyroid.
- **Brim de 5–8 mm** no corpo e na tampa.
- Sem suporte. Costura posicionada atrás.
- O topo da tampa e o fundo do corpo ficam com a textura da mesa (PEI texturizado ou vidro).
- Consumo: ~90 g de ABS.

## Montagem

1. Corte 59,6 mm de filamento 1,75 (ABS de preferência).
2. Encaixe a tampa e passe o pino por um lado através dos 5 nós.
3. Os nós das pontas são do corpo: uma gota de acetona ali solda o pino no corpo, e a tampa continua girando livre.

## Calibração

Os parâmetros de ajuste estão marcados como favoritos no SolidCraft:

| Parâmetro | Padrão | Faixa | Efeito |
|---|---|---|---|
| `fit` | 0,3 | 0,2–0,4 | folga da tampa no lábio |
| `ridge_proud` | 0,6 | 0,4–0,8 | força do clique (`ridge_proud - fit`) |
| `hole_body` | 1,9 | 1,8–2,0 | pino justo nos nós do corpo |
| `hole_lid` | 2,2 | 2,1–2,4 | tampa girando solta |
| `hclr` / `hgap` | 0,35 / 0,4 | 0,3–0,5 | folgas radial e axial da dobradiça |

Para mudar outros tamanhos (outro tamanho de sleeve, mais cartas), edite `in_x`, `in_y` ou `in_z`.

Edite no app (Parâmetros) ou reconstrua pela linha de comando:

```bash
solidcraft-cli run cad/deckbox_build.json --save cad/deckbox_ygo.sc
```

Depois exporte cada peça em STL pelo app. O modelo está na posição de montagem, então vire a tampa de cabeça para baixo no fatiador.

## Verificação

Feita com booleanas exatas do SolidCraft (`inspect.interference`):

- Caixa fechada, corpo × tampa: 0 de interferência.
- 90 cartas (62 × 55,8 × 89) + divisória em pé + pino de 1,75: 0 de interferência.
- Giro da tampa, de 1° a 180°: só o ressalto da trava encosta a 1–2° (o clique). De 3° a 168° fica livre, e o batente fica em ~169°.
