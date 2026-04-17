# Registro de Bugs — Sistema Sorveteria Geladoce

**Projeto:** Sistema Desktop Geladoce (Projeto Final SENAC-PA)
**Responsável:** Isaac Trindade Araújo Júnior
**Período de QA:** 2026
**Total de bugs registrados:** 9
**Status geral:** 9/9 corrigidos ✅

---

## Legenda de Severidade

- 🔴 **Alta** — impede operação do sistema ou causa prejuízo financeiro
- 🟡 **Média** — afeta fluxo mas tem contorno possível
- 🟢 **Baixa** — cosmético ou de baixo impacto

---

## BUG-001 — Taxa de deslocamento sendo cobrada em endereço dentro de Belém

- **Severidade:** 🔴 Alta
- **Módulo:** Venda e Serviços — Aluguel de Carrinho
- **Referência:** RN01, CU005
- **Status:** ✅ Corrigido

**Descrição**
Ao agendar um aluguel de carrinho com endereço dentro de Belém, o sistema estava somando a taxa de deslocamento no total, quando deveria cobrar apenas Itens + Taxa fixa do carrinho.

**Passos para reproduzir**
1. Abrir módulo de aluguel
2. Selecionar carrinho disponível
3. Informar endereço em Belém (ex: Nazaré, Umarizal)
4. Adicionar 30 picolés
5. Finalizar agendamento

**Resultado obtido:** Total incluía R$ 50 de taxa de deslocamento indevidamente
**Resultado esperado:** Total sem taxa de deslocamento para endereços em Belém

**Correção aplicada**
Adicionada verificação da cidade do endereço antes do cálculo. Se cidade = "Belém", taxa de deslocamento = 0.

---

## BUG-002 — Preço de revenda liberado com menos de 30 unidades

- **Severidade:** 🔴 Alta
- **Módulo:** Venda e Serviços
- **Referência:** RN03
- **Status:** ✅ Corrigido

**Descrição**
A tabela de preço de Revenda podia ser selecionada mesmo quando a venda tinha menos de 30 unidades, violando a regra de atacado.

**Passos para reproduzir**
1. Abrir nova venda
2. Adicionar 10 picolés
3. Selecionar opção "Revenda" no tipo de preço

**Resultado obtido:** Sistema aplicava preço de revenda sem validar quantidade
**Resultado esperado:** Sistema bloquear seleção com mensagem sobre o mínimo de 30 unidades

**Correção aplicada**
Adicionada validação da quantidade total antes de permitir trocar para tabela de revenda. Mensagem de erro clara orienta o atendente.

---

## BUG-003 — Venda bloqueada quando estoque zerado

- **Severidade:** 🔴 Alta
- **Módulo:** Estoque e Produção
- **Referência:** RN04
- **Status:** ✅ Corrigido

**Descrição**
Conforme a regra de negócio, a venda deve ser permitida mesmo com estoque virtual zerado (para não parar a fila quando há divergência entre estoque físico e virtual). O sistema estava bloqueando a venda.

**Passos para reproduzir**
1. Zerar estoque de um produto
2. Tentar vender esse produto no balcão

**Resultado obtido:** Sistema bloqueava a venda com mensagem "estoque insuficiente"
**Resultado esperado:** Venda permitida com apenas um alerta visual para o atendente

**Correção aplicada**
Remoção do bloqueio. Agora exibe alerta visual amarelo mas permite continuar a venda.

---

## BUG-004 — Cálculo de fidelidade usando regra de varejo para cliente de revenda

- **Severidade:** 🟡 Média
- **Módulo:** Fidelidade
- **Referência:** RN05, RF08
- **Status:** ✅ Corrigido

**Descrição**
Clientes cadastrados como Revendedor recebiam pontos na proporção de Varejo (1 ponto / R$ 5), quando deveriam receber 2 pontos a cada R$ 50 gastos.

**Passos para reproduzir**
1. Cadastrar cliente como Revendedor
2. Realizar venda de R$ 500
3. Consultar saldo de pontos

**Resultado obtido:** 100 pontos (regra de varejo aplicada)
**Resultado esperado:** 20 pontos (regra de revenda)

**Correção aplicada**
Função de cálculo de pontos agora lê o perfil do cliente antes de aplicar a fórmula.

---

## BUG-005 — Agendamento aceitando data no passado

- **Severidade:** 🟡 Média
- **Módulo:** Venda e Serviços — Agendamento
- **Referência:** RF04, CU005
- **Status:** ✅ Corrigido

**Descrição**
O campo de data do agendamento de carrinhos não validava se a data informada era futura.

**Passos para reproduzir**
1. Abrir agendamento
2. Selecionar data no passado (ex: um mês atrás)
3. Confirmar

**Resultado obtido:** Sistema aceitava e criava o agendamento
**Resultado esperado:** Mensagem de erro informando que a data deve ser futura

**Correção aplicada**
Adicionada validação no campo de data comparando com a data atual do sistema.

---

## BUG-006 — Atendente com acesso a relatório financeiro

- **Severidade:** 🔴 Alta
- **Módulo:** Administrativo
- **Referência:** RNF02, RF06
- **Status:** ✅ Corrigido

**Descrição**
Quebra de segurança: o perfil Atendente conseguia abrir a tela de relatórios financeiros, que deveria ser exclusiva do Proprietário.

**Passos para reproduzir**
1. Fazer login como Atendente
2. Navegar pelo menu lateral
3. Clicar em "Relatórios"

**Resultado obtido:** Tela abria normalmente com dados de faturamento
**Resultado esperado:** Acesso bloqueado com mensagem de permissão insuficiente

**Correção aplicada**
Adicionado verificador de perfil na rota do módulo Administrativo. Atendente agora recebe tela de permissão negada.

---

## BUG-007 — Campo endereço obrigatório em venda comum

- **Severidade:** 🟡 Média
- **Módulo:** Cadastro de Cliente
- **Referência:** RN02
- **Status:** ✅ Corrigido

**Descrição**
O sistema exigia preenchimento de endereço no cadastro de cliente mesmo para vendas comuns de balcão, contrariando a regra de que endereço só é obrigatório para entregas e fidelidade.

**Passos para reproduzir**
1. Abrir cadastro rápido de cliente durante venda de balcão
2. Informar nome e telefone
3. Salvar sem endereço

**Resultado obtido:** Mensagem de erro "endereço obrigatório"
**Resultado esperado:** Cadastro salvo normalmente

**Correção aplicada**
Regra de validação de endereço passou a ser condicional, ativa apenas quando o cliente é cadastrado via fluxo de entrega ou fidelidade.

---

## BUG-008 — Impressão duplicada de cupom

- **Severidade:** 🟢 Baixa
- **Módulo:** Impressão de Pedidos
- **Referência:** RF07
- **Status:** ✅ Corrigido

**Descrição**
Em vendas finalizadas com duplo clique no botão "Finalizar", o cupom saía duas vezes na impressora.

**Passos para reproduzir**
1. Abrir uma venda
2. Adicionar itens
3. Clicar duas vezes em sequência no botão "Finalizar"

**Resultado obtido:** Cupom impresso em duplicidade
**Resultado esperado:** Apenas um cupom emitido

**Correção aplicada**
Adicionado controle de estado no botão (desabilita após o primeiro clique até a impressão concluir).

---

## BUG-009 — Total da venda com divergência de arredondamento

- **Severidade:** 🟡 Média
- **Módulo:** Venda e Serviços
- **Referência:** RF03, CU004
- **Status:** ✅ Corrigido

**Descrição**
Em vendas com itens de preço com casas decimais (ex: R$ 3,33), o total exibido às vezes divergia em R$ 0,01 da soma manual dos itens, por conta de arredondamento em ponto flutuante.

**Passos para reproduzir**
1. Adicionar 3 itens de R$ 3,33 à venda
2. Conferir total

**Resultado obtido:** R$ 10,00 (arredondamento indevido)
**Resultado esperado:** R$ 9,99

**Correção aplicada**
Substituição de `float` por `Decimal` no cálculo de valores monetários, com quantização a 2 casas decimais.

---

## Resumo Estatístico

| Severidade | Quantidade | % |
|---|---|---|
| 🔴 Alta | 4 | 44% |
| 🟡 Média | 4 | 44% |
| 🟢 Baixa | 1 | 12% |
| **Total** | **9** | **100%** |

| Módulo | Bugs |
|---|---|
| Venda e Serviços | 4 |
| Estoque / Fidelidade | 2 |
| Cadastro / Administrativo | 2 |
| Impressão | 1 |

**Taxa de correção:** 100% (9/9)
