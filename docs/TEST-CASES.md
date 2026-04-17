# Cenários de Teste — Sistema Sorveteria Geladoce

**Projeto:** Sistema Desktop Geladoce (Projeto Final SENAC-PA)
**Responsável:** Isaac Trindade Araújo Júnior
**Stack:** Python · CustomTkinter · SQLite
**Versão do documento:** 1.0
**Data:** 2026

---

## 1. Objetivo

Documentar os cenários de teste executados para validar o comportamento do sistema contra os Requisitos Funcionais (RF), Requisitos Não Funcionais (RNF) e Regras de Negócio (RN) definidos no Documento de Projeto de Software.

## 2. Escopo

Foram testados os 7 módulos do sistema:

1. Cadastro de Cliente
2. Venda e Serviços
3. Estoque e Produção
4. Fornecedores
5. Administrativo
6. Impressão de Pedidos e Cupons
7. Fidelidade

## 3. Estratégia de Teste

- **Teste funcional manual** de cada requisito funcional
- **Teste de regra de negócio** contra as RN01–RN05
- **Teste de fluxo** cobrindo os Casos de Uso principais
- **Teste de borda** (edge cases) em entradas críticas
- **Teste de autenticação e permissão** por perfil (Proprietário × Atendente)

## 4. Matriz de Cenários

### Módulo 1 — Cadastro de Cliente

| ID | Cenário | Pré-condição | Passos | Resultado Esperado | Ref. | Status |
|---|---|---|---|---|---|---|
| TC-001 | Cadastrar cliente de varejo apenas com nome | Tela de cadastro aberta | 1. Informar nome<br>2. Deixar endereço e telefone vazios<br>3. Salvar | Cliente salvo com sucesso | RF01, RN02 | ✅ Passou |
| TC-002 | Cadastrar cliente para entrega sem endereço | Tela de cadastro aberta | 1. Informar nome<br>2. Marcar opção "Entrega"<br>3. Deixar endereço vazio<br>4. Salvar | Sistema exige endereço antes de salvar | RN02 | ✅ Passou |
| TC-003 | Diferenciar perfil Varejo × Revenda | Usuário logado | 1. Criar cliente Varejo<br>2. Criar cliente Revenda<br>3. Consultar listagem | Perfis aparecem separados e editáveis | RF01 | ✅ Passou |

### Módulo 2 — Venda e Serviços

| ID | Cenário | Pré-condição | Passos | Resultado Esperado | Ref. | Status |
|---|---|---|---|---|---|---|
| TC-004 | Venda de balcão com 3 picolés | Produtos cadastrados | 1. Abrir venda<br>2. Adicionar 3 itens<br>3. Finalizar | Venda finalizada, total calculado, status "Finalizado" | RF03, CU004 | ✅ Passou |
| TC-005 | Aplicar tabela de Revenda com 40 unidades | Produto com preço Varejo e Revenda | 1. Abrir venda<br>2. Adicionar 40 unidades<br>3. Selecionar "Revenda" | Sistema aplica preço de revenda | RN03 | ✅ Passou |
| TC-006 | Tentar aplicar Revenda com 20 unidades | Produto com preço Varejo e Revenda | 1. Abrir venda<br>2. Adicionar 20 unidades<br>3. Tentar selecionar "Revenda" | Sistema bloqueia e exibe mensagem sobre mínimo de 30 unidades | RN03 | ✅ Passou |
| TC-007 | Venda com estoque zerado | Produto com quantidade = 0 | 1. Selecionar produto<br>2. Finalizar venda | Venda permitida com alerta (não bloqueio) | RN04 | ✅ Passou |
| TC-008 | Agendar aluguel de carrinho dentro de Belém | Carrinho disponível | 1. Selecionar aluguel<br>2. Informar endereço em Belém<br>3. Finalizar | Total = Itens + Taxa fixa do carrinho (sem deslocamento) | RN01 | ✅ Passou |
| TC-009 | Agendar aluguel fora de Belém | Carrinho disponível | 1. Selecionar aluguel<br>2. Informar endereço fora de Belém<br>3. Finalizar | Total = Itens + Taxa fixa + Taxa de deslocamento | RN01, CU005 | ✅ Passou |

### Módulo 3 — Estoque e Produção

| ID | Cenário | Pré-condição | Passos | Resultado Esperado | Ref. | Status |
|---|---|---|---|---|---|---|
| TC-010 | Lançar entrada de insumos | Fornecedor e produto cadastrados | 1. Registrar nota de compra<br>2. Informar quantidade | Estoque atualizado automaticamente | RF10 | ✅ Passou |
| TC-011 | Cadastrar fórmula/receita | Proprietário logado | 1. Acessar receitas<br>2. Criar nova com ingredientes | Fórmula salva e associada ao produto | RF02 | ✅ Passou |
| TC-012 | Atendente tentar acessar receitas | Atendente logado | 1. Fazer login como atendente<br>2. Tentar abrir módulo de receitas | Acesso bloqueado com mensagem de permissão | RNF02 | ✅ Passou |

### Módulo 5 — Administrativo (Relatórios)

| ID | Cenário | Pré-condição | Passos | Resultado Esperado | Ref. | Status |
|---|---|---|---|---|---|---|
| TC-013 | Gerar relatório de faturamento | Vendas registradas no período | 1. Abrir relatórios<br>2. Selecionar período<br>3. Gerar | Relatório exibido com total correto | RF06, CU007 | ✅ Passou |
| TC-014 | Atendente tentar gerar relatório financeiro | Atendente logado | 1. Tentar acessar relatórios | Acesso bloqueado | RNF02 | ✅ Passou |

### Módulo 6 — Impressão de Pedidos

| ID | Cenário | Pré-condição | Passos | Resultado Esperado | Ref. | Status |
|---|---|---|---|---|---|---|
| TC-015 | Imprimir pedido ao finalizar venda | Impressora configurada | 1. Finalizar venda<br>2. Aguardar impressão | Cupom enviado para impressora automaticamente | RF07 | ✅ Passou |

### Módulo 7 — Fidelidade

| ID | Cenário | Pré-condição | Passos | Resultado Esperado | Ref. | Status |
|---|---|---|---|---|---|---|
| TC-016 | Calcular pontos de cliente Varejo | Cliente Varejo cadastrado | 1. Realizar venda de R$ 25<br>2. Consultar saldo | Saldo acumulado: 5 pontos (1 ponto a cada R$ 5) | RN05, RF08 | ✅ Passou |
| TC-017 | Calcular pontos de cliente Revenda | Cliente Revenda cadastrado | 1. Realizar venda de R$ 500<br>2. Consultar saldo | Saldo acumulado: 20 pontos (2 pontos a cada R$ 50) | RN05 | ✅ Passou |

### Módulo transversal — Autenticação

| ID | Cenário | Pré-condição | Passos | Resultado Esperado | Ref. | Status |
|---|---|---|---|---|---|---|
| TC-018 | Login com credenciais válidas | Usuário cadastrado | 1. Informar usuário e senha<br>2. Entrar | Acesso liberado conforme perfil | RF09, CU009 | ✅ Passou |
| TC-019 | Login com senha incorreta | Usuário cadastrado | 1. Informar usuário<br>2. Informar senha errada | Acesso negado com mensagem | RF09 | ✅ Passou |

## 5. Resumo de Cobertura

| Módulo | Cenários | Status |
|---|---|---|
| Cadastro de Cliente | 3 | 3/3 ✅ |
| Venda e Serviços | 6 | 6/6 ✅ |
| Estoque e Produção | 3 | 3/3 ✅ |
| Administrativo | 2 | 2/2 ✅ |
| Impressão | 1 | 1/1 ✅ |
| Fidelidade | 2 | 2/2 ✅ |
| Autenticação | 2 | 2/2 ✅ |
| **Total** | **19** | **19/19 ✅** |

**Cobertura de Regras de Negócio:** 5/5 (RN01 a RN05)
**Cobertura de Requisitos Funcionais testáveis:** 10/10

## 6. Observações

- Bugs encontrados durante a execução dos testes estão documentados em [`BUG-LOG.md`](./BUG-LOG.md)
- Todos os cenários que falharam na primeira execução foram corrigidos e re-testados até passarem
- Testes manuais executados em ambiente Windows 10 com SQLite local
