# Caixa D "asas" — em andamento

Caixa nova inspirada no vídeo da "Caixa de Deck Mecânica EDH" (Cults): duas portas abrem como asas e o berço
sobe por engrenagem e cremalheira. Projeto do zero, para Yu-Gi-Oh (90 cartas com sleeve duplo, mesmo berço da C).

![esquema 2D](D_esquema_2d.png)

## Como gerar

```
pip install shapely
python cad/D-asas/geo_d.py        # só as checagens 2D (rápido)
python cad/D-asas/gerar_d.py      # escreve D_asas_build.json e D_verificacao.json
solidcraft-cli run cad/D-asas/D_asas_build.json --save cad/D-asas/D_asas.sc --quiet   # ~2 min
python cad/D-asas/verificar_d.py  # roda as 29 checagens no solidcraft-cli e diz ok/FALHA (~12 min)
python cad/D-asas/exportar_stl_d.py   # STLs na posição de impressão em stl/D-asas/ (~40 s)
python cad/D-asas/render_d.py         # imagens do README em images/D_*.png (~1 min)
python cad/D-asas/animar_d.py         # GIFs de montagem e funcionamento (Blender 5.3; --export refaz os STLs)
```

O `.sc` não vai para o git enquanto o projeto muda (23 MB); ele sai do build JSON com o comando acima.
`D_verificacao.json` é uma lista de chamadas `batch` do MCP do SolidCraft; `verificar_d.py` roda as mesmas sem o MCP
(`--reuse` só reanalisa a última saída).

## Decisões (e por quê)

- **Medidas:** 74,2 × 85,6 × 100,1 mm (+5 mm da dobradiça de cada lado). A divisão base/portas fica em z = 55.
- **Eixos das portas:** paralelos a Y, a 1,5 mm por fora das laterais. Um eixo por dentro faria a borda da porta varrer o berço.
- **Engrenagem:** m 1,5, z 42 (R 31,5), α 20°, folga de 0,075 por flanco em cada peça.
  - Cada porta leva 2 placas-setor (frente e trás), com 10 dentes evolventes.
  - As placas engrenam em 2 cremalheiras duplas (frente e trás).
- **Engrenadas desde 0°:** as portas abrem juntas. Uma espera com a cremalheira parada não funciona: com cremalheira reta, os dentes do setor varrem a faixa dos dentes dela parada e batem.
- **Espera de 12° por folga morta:** a cremalheira corre 6,6 mm numa cauda de andorinha do berço antes de pegar nele. As cartas não batem no teto da porta: folga mínima de 2,5 mm em todo o giro, porque a espera de 12° mantém o berço parado (com 10° seria 1,9 mm a 26°).
- **Duas cremalheiras (frente e trás):** com uma só atrás, o berço trava. O peso fica a ~38 mm do ponto de apoio, e a guia que sobra com o berço em cima (~18 mm) é menor que 72·μ ≈ 25 mm.
- **Subida:** curso da cremalheira 42,9 mm e berço +36,3 mm a 78°.
- **Segurar aberta:** um arco concêntrico (tipo Genebra) não sustenta a cremalheira — com o contato abaixo do nível do eixo, ela só cai. Por isso:
  - uma lingueta na parede de trás da base (cortes a 45°, imprime sem suporte) tem um ressalto de 0,5;
  - a cremalheira de trás tem uma nervura de 0,6 (flanco de baixo a 45°, de cima a 30°) que passa por cima do ressalto perto de 75° (clique);
  - a lingueta segura ~6 N contra os ~2,9 N do baralho;
  - aberta, o centro de gravidade das portas fica por fora e elas encostam no batente.
- **Batente na dobradiça:** a barra de baixo (base, contínua, 45° por baixo) tem o topo no lugar da porta girada até 78°.
- **Dobradiça:** 7 nós (base nos pares). Pino de filamento 1,75: furo de 1,9 na base (aperta) e 2,2 na porta (solto), em gota, com a frente fechada (1 mm).
- **Fechamento:**
  - na emenda das placas da esquerda há 2 hastes com farpas (snap) que entram no receptáculo das placas da direita;
  - 1 ímã 4×2 por placa (z = 74): 4 ímãs, 2 pares (frente E↔D e trás E↔D);
  - as placas E e D são diferentes (2 STLs, 2 de cada) — confira a polaridade dos ímãs antes de colar.
- **Placas:** encostam no teto e na lateral da porta e ficam presas por 2 pinos impressos colados (super bonder) cada,
  pela parede da porta. Eram parafusos M2: trocados a pedido em 2026-11-26.
  - **Pino:** haste Ø2,5 × 5,5 e cabeça Ø4,8 × 0,8 (`PIN` em `gerar_d.py`).
  - **Furos:** Ø2,7 passante na parede e na placa. O passante mantém iguais as placas da frente e de trás.
  - **Rebaixo de Ø5,0 × 0,8 na parede:** a cabeça fica rente e tampa o furo.
  - **Profundidade:** a haste entra 4 mm na placa e para 1 mm antes da face que dá para o berço.
  - **Colagem:** depois de testar a caixa montada. Coladas, as placas não saem mais.
- **Acabamento:**
  - painel rebaixado na frente da base (adesivo) e friso no teto das portas;
  - entalhe para a unha na emenda;
  - pés de silicone e texto no fundo.

## Estado (2026-11-25)

- **Feito:**
  - checagens 2D todas OK: dentes sem sobreposição, folga mínima de 0,14;
  - build 3D sem erro: 514 comandos, 13 corpos;
  - verificação 3D:
    - zero interferência de 0° a 77,5° (a 75° só a trava, que é o clique previsto);
    - engrenamento ±0,4 encosta;
    - engate a 1,5° encosta;
    - fim da espera encosta.
- **Feito (2026-11-25, no outro computador):**
  - **Build:** no SolidCraft 0.40.1 daqui o build quebrava no `HingeDoorL2` (booleano do SMLib). A fatia da dobradiça do
    outro lado encostava topo com topo no nó vizinho, e o arco dela quase coincidia com o do entalhe. Agora ela para 0,02 antes
    do nó vizinho e o arco fica 0,02 por fora (sobrepor também falha: faces laterais coplanares). A peça não muda na prática.
  - **Batente:** com o build refeito, o 3D bate com o 2D, sem mexer em `base_lug()`:
    - livre a 77,5°;
    - 0,02 mm³ a 78°;
    - 7,9 mm³ a 78,5° (0,112 mm² × 70,4 mm de dobradiça).
  - **Trava na varredura:** a 75° e 77,5° a varredura exclui só o par cremalheira de trás × base. O clique é checado à parte.
  - **`verificar_d.py`:** 29 checagens (com as 4 dos pinos das placas), 28 ok + 1 informativa (o sentido de abertura está certo).
  - **STLs** (`exportar_stl_d.py`): 9 arquivos em `stl/D-asas/`, já na mesa. As faces na mesa foram conferidas pela área:

    | Arquivo | Imprimir | Posição | Medidas (mm) |
    |---|---|---|---|
    | `D_base` | 1 | em pé (gota do pino para cima) | 89,2 × 85,6 × 58,5 |
    | `D_berco` | 1 | em pé | 69,6 × 75,0 × 52,5 |
    | `D_porta_esquerda` | 1 | de cabeça para baixo (teto na mesa) | 41,9 × 85,6 × 48,6 |
    | `D_porta_direita` | 1 | de cabeça para baixo | 41,9 × 85,6 × 48,6 |
    | `D_placa_esquerda_x2` | 2 | deitada (frente e trás são iguais) | 39,1 × 75,4 × 5,0 |
    | `D_placa_direita_x2` | 2 | deitada | 34,9 × 75,4 × 5,0 |
    | `D_cremalheira_frente` | 1 | rasgo para baixo | 17,2 × 55,7 × 5,0 |
    | `D_cremalheira_tras` | 1 | rasgo para baixo, nervura da trava para cima | 17,2 × 55,7 × 5,6 |
    | `D_divisoria` | 1 | deitada | 63,6 × 92,0 × 1,6 |

    Os pinos da dobradiça não têm STL: são de filamento 1,75 cortado (~70 mm).
  - **Renders** (`render_d.py`): `images/D_fechada`, `D_aberta`, `D_mecanismo_fechada` e `D_mecanismo_aberta`.
    O mecanismo sai cortado na folga entre o berço e as placas de trás: no corte no meio, a parede do berço tapava a cremalheira.
  - **README:** seção da versão D (impressão, compras, montagem, calibração, verificação) e menção na introdução.
    - Ferragens conferidas no modelo: **4** ímãs 4×2 (o "8 ímãs" daqui estava errado), 2 pinos de filamento 1,75 × 69
      (os 8 parafusos M2 viraram pinos impressos colados, ver Placas).
  - **Ordem de montagem corrigida.** A antiga ("abrir as portas a 78° e descer o berço com as cremalheiras") não funciona:
    - com a porta parada no batente, a cremalheira descendo de cima bate nos dentes 7 e 8 do setor (2D: de 0,25 a 13 mm antes do lugar);
    - engrenar rolando pediria abrir até ~103°, e o batente fica em 78°;
    - o rasgo da cauda de andorinha é aberto só em cima, então a cremalheira entra no trilho por baixo.
  - **Ordem que funciona:** cremalheiras no berço por baixo → placas deslizando de lado (Y) sobre as cremalheiras, já
    engatadas na emenda → conjunto na base → portas por cima, fechadas (2D: descida de 30 mm sem tocar) → pinos da
    dobradiça → pinos das placas secos → teste → colar os pinos das placas. Cola só nos ímãs e nos pinos das placas.
  - **GIFs** (`animar_d.py` + `blender_d.py`, Blender 5.3 em segundo plano): `images/D_montagem.gif` (passo a passo, com
    selo de cola/sem cola) e `images/D_funcionando.gif` (3/4 + corte atrás do berço). As peças saem do `.sc` em STL e as
    poses vêm da mesma cinemática (`travel`, `lift`, giro das portas).
- **Pendente:**
  - Imprimir e testar: primeiro placas + cremalheiras (engrenamento, `bl`), depois o engate da emenda e a trava.
  - Montagem: testar na peça impressa se as placas deslizam de lado sobre a cremalheira com as duas engatadas na emenda
    (o modelo diz que sim, os perfis são prismáticos em Y).
  - Quando fechar o projeto: o `.sc` e um `.step` no git, como nas outras versões.
