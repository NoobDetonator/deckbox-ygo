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
```

O `.sc` não vai para o git enquanto o projeto muda (23 MB); ele sai do build JSON com o comando acima.
`D_verificacao.json` é uma lista de chamadas `batch` do MCP do SolidCraft (abrir o `.sc` e rodar cada uma).

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
  - 1 ímã 4×2 por placa (z = 74): 4 pares no total;
  - as placas E e D são diferentes (2 STLs, 2 de cada) — confira a polaridade dos ímãs antes de colar.
- **Placas:** presas na parede da porta com 2 parafusos M2 escareados por fora. Encostam no teto e na lateral da porta.
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
- **Pendente:**
  1. **Batente:** no 3D, a 78,5° a porta ainda não encosta na barra de baixo (no 2D encostava 0,12 mm²). Achar o ângulo real (testar 80–85°) e ajustar `base_lug()` para encostar a 78°.
  2. A checagem "portas a 75 graus" deve esperar a trava (renomear ou tirar o 75 da varredura).
  3. Exportar os STLs na posição de impressão:
     - base em pé;
     - portas de cabeça para baixo;
     - placas deitadas;
     - cremalheiras com o rasgo para baixo;
     - berço em pé.
  4. Renders (fechada, aberta, mecanismo) e a seção da versão D no README (tabela de impressão, montagem, ferragens: 8× M2×6 escareado, 8 ímãs 4×2, 2 pinos de filamento 1,75 × ~70).
  5. **Montagem:** com as portas abertas a 78°, encaixar o berço com as cremalheiras (o último dente do setor entre os dentes 9 e 10 da cremalheira).
