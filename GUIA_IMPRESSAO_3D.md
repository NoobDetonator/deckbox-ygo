# Guia de impressão 3D (FDM, ABS): folgas, orientação e checklist

As regras que este repositório usa para desenhar peças que saem certas na primeira impressão.
- **Base dos números:** bico de 0,4 mm, camada de 0,2 mm, ABS.
- **De onde vêm:** guias de fabricantes e de laboratórios (fontes no fim) e o que já foi testado aqui. A dobradiça impressa da versão B saiu perfeita na sua impressora com 0,4 mm de folga radial e 0,5 mm axial (um pouco solta).
- **Cuidado ao comparar números de fontes diferentes:** algumas dão a folga **por lado** (radial), outras o **total** (no diâmetro). Aqui é sempre **por lado**, salvo quando estiver escrito "no diâmetro".

> Regra de ouro: **imprima as peças de teste antes das peças grandes.** A folga certa depende da sua impressora, do filamento e do fatiador. Um teste de 10 g evita jogar fora uma base de 50 g. A versão D tem um conjunto pronto (`stl/D-asas/D_teste_*.stl`).

---

## 1. Folgas

| Encaixe | Folga (por lado) | Exemplo neste projeto |
|---|---|---|
| **Deslizante** (gaveta, trilho, berço na base) | 0,25 – 0,3 | berço na base: 0,3. Cauda de andorinha da D: 0,25 nos flancos e 0,3 no fundo, que é ponte e cede |
| **Print-in-place** (peça que já sai montada) | pino no furo 0,3 – 0,4; entre nós 0,35 – 0,5 | dobradiça da D: pino 0,35, nós 0,4, nó contra a aba do outro lado 0,4 |
| **Engrenagem** | 0,1 por flanco em cada peça (≈ 0,4 no total) | setor e cremalheira da D: `bl` = 0,1 |
| **Snap-fit** (faces que não devem encostar) | 0,25 (≈ 0,5 no total) | engate da emenda da D |
| **Snap-fit** (quanto a haste cede para passar) | 0,2 – 0,3, com deformação < 1 % | haste da D: cede 0,28 (0,5 %) |
| **Pino colado num furo** | 0,1 – 0,15 | pino de 2,5 em furo de 2,8 |
| **Peça impressa num rebaixo** (aba, tampa) | 0,15 – 0,2 | aba da dobradiça da D: 0,15 |
| **Ímã num furo** | +0,2 no diâmetro, +0,1 a 0,15 na profundidade | ímã 4 × 2 em furo de 4,2 × 2,1 (A, B, C) |
| **Pressão** (press-fit) | 0 – 0,05 | só com teste: em ABS o furo sai 0,1 a 0,2 menor |
| **Vão dentro da mesma peça** (para não soldar) | ≥ 0,5 no plano da mesa; ≥ 2 camadas (0,4) na vertical | vão em volta das hastes do engate: 0,6 |

Print-in-place pede mais folga que peça montada à mão: se soldar, não dá para separar. Arredondamentos e chanfros perto do vão diminuem a folga, então meça o vão real, não o do esboço.

## 2. Furos

- **Furo vertical** (eixo em Z) sai **0,1 a 0,2 mm menor** em ABS. Some isso ao diâmetro, ou desenhe justo e passe uma broca.
- **Furo horizontal** (eixo deitado): o teto é ponte e cai. Desenhe em **gota** (*teardrop*), com a ponta para cima na posição de impressão. O teto sai a 45° e o furo fica redondo onde importa.
- **Furo menor que 2 mm** sai ruim. Prefira pino impresso de 2,5 ou mais, ou filamento de 1,75 como eixo.

## 3. Orientação: decida antes de desenhar

A peça é feita em camadas, e **a ligação entre camadas é o ponto fraco**: na vertical (Z), a peça aguenta uns 50–70 % do que aguenta deitada.

- **Engrenagem, cremalheira, haste de snap e lingueta: sempre deitadas.** O perfil fica no plano da mesa e a flexão corre ao longo das camadas.
- **Pino que trabalha em cisalhamento:** deitado, se der. Em pé, só se for curto e colado.
- **Balanço** (saliência) até **45°** sai sem suporte. Mais que isso, troque a face por um chanfro de 45°. Saliências horizontais de até ~1 mm saem.
- **Ponte** (teto horizontal apoiado nas duas pontas): até ~10 mm sai limpa em ABS; acima de 15 mm, evite.
- **A face na mesa é a mais exata e a mais bonita**, mas é onde aparece o pé de elefante (seção 4).
- **Vazios fechados em cima** (furo de ímã deitado, rasgo coberto): o teto é ponte. Se a pele por cima ficar com menos de 1 mm, abra o rasgo até a borda (é o que a D faz com os ímãs das placas).

## 4. Pé de elefante (primeira camada larga)

A primeira camada é esmagada na mesa e sai 0,1 a 0,3 mm mais larga. Em peça que encaixa, isso trava.
1. **No fatiador:** ligue a compensação de pé de elefante, de 0,1 a 0,2 mm (PrusaSlicer e OrcaSlicer: "Elephant foot compensation"; Cura: "Initial Layer Horizontal Expansion" negativo).
2. **No desenho:**
   - chanfro de 0,4 a 1 mm nas bordas que vão na mesa: a base da D tem 0,8 e o teto das portas, 1,0;
   - nas peças que encaixam pela face da mesa, um **alívio**: a borda fica 0,2 mm para dentro nos primeiros 0,3 mm. É o que fazem os dentes, o engate e o rasgo da cauda de andorinha da D, que ainda tem a boca chanfrada.

## 5. Espessuras

- **Parede:** pense em voltas de perímetro (largura de extrusão ≈ 0,45). 1,6 mm são 3 ou 4 voltas; 2,0 mm são 4 ou 5. Mínimo de 0,8 mm (2 voltas).
- **Relevo e baixo-relevo:** pelo menos 2 camadas (0,4 mm). Texto com pelo menos 3,5 mm de altura e traço de 0,5 mm.
- **Peças de 5 mm** (placas e cremalheiras): com 6 perímetros os dentes e as hastes já saem maciços. O miolo pode ter 40 % de preenchimento; 100 % só gasta plástico.

## 6. ABS: contração e empenamento

- **Contração:** 0,5 a 0,7 % depois de frio. Para conferir, imprima uma barra de 100 mm e meça. Nas medidas que encostam em carta, ímã ou outra peça, este projeto compensa com o parâmetro `shrink` (0,006).
- **Empenamento:**
  - câmara fechada (aqueça uns 10 min antes);
  - ventoinha de 0 a 20 % (30 a 40 % só nas pontes);
  - mesa a 100–110 °C e cola ou PEI;
  - **brim de 5 a 8 mm** nas peças grandes;
  - cantos arredondados (R4) em vez de quinas vivas na base;
  - filamento seco.
- **Colar:**
  - super bonder (cianoacrilato) com ativador para peças pequenas e pinos;
  - ABS também cola com acetona, que solda as peças, sem folga para colocar;
  - pouco super bonder: o vapor deixa o ABS esbranquiçado ("blooming").

## 7. Checklist antes de imprimir uma peça grande

- [ ] Imprimi as peças de teste e elas encaixaram (ou ajustei os parâmetros e gerei de novo).
- [ ] A orientação de cada arquivo confere com a tabela do README (os STLs já saem na posição certa: não gire no fatiador).
- [ ] Sem suporte: nada passa de 45° sem chanfro.
- [ ] Compensação de pé de elefante ligada no fatiador.
- [ ] Brim nas peças grandes (base, portas, berço).
- [ ] Mesa limpa e nivelada; primeira camada conferida no começo da impressão.
- [ ] Câmara quente, ventoinha baixa, filamento seco.
- [ ] Perímetros e preenchimento como no README (6 perímetros; 15 % gyroid nas caixas, 40 % nas placas e cremalheiras).

## 8. Como isso entrou na caixa D

| Peça | Posição na mesa | Por quê | Cuidados no desenho |
|---|---|---|---|
| Base | em pé | paredes verticais, sem ponte | chanfro de 0,8 na mesa; rebaixos e canal da dobradiça abertos para cima; orelhas do batente com 45° por baixo; lingueta da trava com cortes a 45° de 0,9 (0,64 na perpendicular: não solda) |
| Portas | de cabeça para baixo (teto na mesa) | o teto sai liso e as paredes sobem sem suporte | chanfro de 1,0 no teto; friso de 1,0 de largura (mais estreito o pé de elefante fecharia); furos dos pinos das placas em gota, com a ponta para cima na impressão |
| Placas-setor | deitadas | dentes e hastes do engate trabalham no plano das camadas | alívio de 0,2 × 0,3 nas duas faces; ímã num rasgo aberto até a borda (sem pele fina); vão de 0,6 em volta das hastes, fundo redondo na raiz |
| Cremalheiras | deitadas, rasgo para baixo | o rasgo da cauda de andorinha alarga para cima: as paredes se apoiam na camada de baixo e o teto é uma ponte de 7 mm | boca do rasgo chanfrada 0,4 e alívio de 0,2 × 0,3 na face da mesa |
| Berço | em pé | paredes de 1,6 sem ponte | trilho com o fundo a 45°; chanfro de entrada de 0,6 embaixo |
| Dobradiças | deitadas, face colada na mesa | print-in-place como a da B (já testada): os nós encostam na mesa e o furo dos nós que giram é em gota | folgas da seção 1; a face colada sai lisa da mesa |
| Pinos das placas | em pé, sobre a cabeça | peça minúscula; a cabeça sai lisa e fica para fora | imprima junto com outras peças (deixa a camada esfriar); colados, o cisalhamento fica baixo (~2,5 MPa) |

---

## Fontes

- Folgas por tipo de encaixe: [QIDI — interlocking parts](https://qidi3d.com/en-br/blogs/news/how-to-3d-print-interlocking-parts-and-assemblies), [Sovol — tolerances & clearances](https://www.sovol3d.com/blogs/news/fdm-3d-printing-tolerances-clearances-how-to-design-parts-that-fit), [Snapmaker — tolerances](https://www.snapmaker.com/blog/3d-printing-tolerances), [CCI Digital Fabrication Lab](https://wiki.cci.arts.ac.uk/books/digital-fabrication-lab/page/design-the-clearance-and-tolerance)
- Print-in-place e dobradiças: [JLC3DP — por que as peças soldam](https://jlc3dp.com/blog/print-in-place-hinge), [Snapmaker — hinges](https://www.snapmaker.com/blog/3d-printed-hinges/), [Sovol — print-in-place](https://www.sovol3d.com/blogs/news/print-in-place-3d-printing-how-to-design-hinges-joints-and-moving-parts-that-actually-work)
- Engrenagens: [Sovol — gears that actually work](https://www.sovol3d.com/blogs/news/3d-printing-gears-that-actually-work-backlash-orientation-and-material-tips)
- Snap-fit: [Hubs/Protolabs — snap-fit joints](https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing), [Fictiv — snap-fit components](https://www.fictiv.com/articles/how-to-design-snap-fit-components)
- Regras gerais de FDM (balanço, ponte, parede, furo): [Hubs — designing for FDM](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
- Pé de elefante: [Prusa — elephant foot compensation](https://help.prusa3d.com/article/elephant-foot-compensation_114487), [QIDI — elephant foot](https://qidi3d.com/blogs/news/fix-3d-print-elephant-foot)
- Furos e gotas: [All3DP — holes](https://all3dp.com/2/3d-printing-holes-screw-guide/), [HydraRaptor — horizontal holes](https://hydraraptor.blogspot.com/2020/07/horiholes_36.html)
- ABS: [Prusa — ABS](https://help.prusa3d.com/article/abs_2058), [Sovol — large ABS parts without warping](https://www.sovol3d.com/blogs/news/how-to-print-large-abs-parts-without-warping-settings-enclosure-and-chamber-tips)
