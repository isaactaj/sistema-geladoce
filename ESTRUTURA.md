# ESTRUTURA.md — Organização do repositório (Geladoce)

Este arquivo explica **como o repositório está dividido**, para qualquer pessoa do time conseguir:
- achar rapidamente onde mexer
- criar novas telas sem bagunçar o projeto
- entender o fluxo do sistema (sidebar → navegação → páginas)

> Regra de ouro: **cada arquivo tem um “papel”**. Se você não sabe onde colocar algo, leia a seção “Onde colocar o quê”.
> Para instalar todas os imports use pip install -r requirements.txt
---

## 1) Estrutura de pastas

geladocesistema/
├─ main.py
├─ README.md
├─ ESTRUTURA.md
├─ requirements.txt
├─ .gitignore
│
├─ app/
│ ├─ config/
│ │ └─ theme.py
│ │
│ ├─ core/
│ │ └─ navigation.py
│ │
│ ├─ ui/
│ │ └─ sidebar.py
│ │
│ └─ pages/
│ ├─ placeholder.py
│
├─ scripts/
│
└─ assets/


---

## 2) O que cada parte faz

### `main.py`
É o **ponto de entrada** do sistema.
Ele cria a janela principal (`CTk`), configura tema, carrega a sidebar e chama a navegação.

**Não coloque regra de negócio aqui.**
Aqui deve ficar só:
- setup inicial
- layout base
- inicialização do app

---

### `app/config/theme.py`
Arquivo central do **tema** (cores, fontes e helpers de formatação).

Tudo que for cor, fonte e estilo deve vir daqui.
Exemplos:
- `COR_FUNDO`, `COR_PAINEL`, `FONTE`
- helpers como `fmt_dinheiro()` e `cor_delta()`

> Regra: ninguém cria cor “solta” no meio do código. Se precisar, coloca no `theme.py`.

---

### `app/ui/sidebar.py`
Aqui fica a **interface do menu lateral**:
- `MenuLateral`
- `SecaoExpansivel` (accordion)
- lógica de “marcar ativo” o item do menu

A sidebar **não cria páginas**. Ela só chama a função `navegar(chave)` quando o usuário clica.

> Sidebar = UI de navegação (botões e layout)

---

### `app/core/navigation.py`
A navegação é o “cérebro” que decide **qual tela aparece** na área principal.

Ela recebe uma `key` (ex.: `"relatorios"`, `"clientes"`) e:
- destrói a página atual
- cria a nova página correspondente

> Navigation = troca de telas (roteamento simples)

---

### `app/pages/placeholder.py`
Tela “em construção”, usada quando a rota ainda não existe.

Ou seja: se você clicar em algo que ainda não tem página pronta, aparece o placeholder.

> Placeholder = evita erro e mostra para o usuário que a tela ainda não foi feita.

---

### `app/pages/relatorios/page.py`
A tela de relatórios em si:
- filtros
- KPI cards
- gráficos
- botões de exportação
- lógica de atualização do dashboard

> Page = a tela + interface + comportamento da tela

---

### `app/pages/relatorios/export.py`
Tudo que for relacionado a **exportar** (PDF/Excel) fica aqui.
Isso mantém `page.py` mais limpo e mais fácil de manter.

Exemplos:
- funções `exportar_pdf(...)`
- funções `exportar_excel(...)`
- helpers de conversão de gráfico para imagem

> Export = gerar arquivos (PDF/Excel)

---

### `scripts/run_login_demo.py`
Scripts extras que NÃO fazem parte do app principal.

Por exemplo:
- simulação do login
- testes rápidos
- protótipos

> Regra: scripts não devem rodar automaticamente junto com o app.

---

### `assets/`
Arquivos estáticos:
- imagens
- ícones
- etc.

---

## 3) Fluxo do sistema (como tudo se conecta)

1. O usuário clica na **sidebar** (ex.: Relatórios)
2. A sidebar chama: `navegar("relatorios")`
3. O `main.py` repassa para o `Navigation`:
   - `self.area.show("relatorios")`
4. O `Navigation` cria a página correta:
   - `PaginaAdminRelatorios(...)`

---

## 4) Onde colocar o quê (regras práticas)

✅ **Cores / fontes / formatação visual**
- `app/config/theme.py`

✅ **Botão, menu lateral, componentes de navegação**
- `app/ui/sidebar.py`

✅ **Troca de telas / mapa de rotas**
- `app/core/navigation.py`

✅ **Tela nova**
- criar em `app/pages/nome_da_tela/page.py`

✅ **Funções auxiliares de uma tela (exportar, cálculos etc.)**
- criar `app/pages/nome_da_tela/alguma_coisa.py`
  - exemplo: `export.py`, `utils.py`

✅ **Teste rápido / protótipo**
- `scripts/`

✅ **Imagens e ícones**
- `assets/`

---

## 5) Padrão de chaves (muito importante)

As telas são chamadas por chaves (strings), exemplo:
- `"inicio"`
- `"relatorios"`
- `"clientes"`

**Regras para chaves:**
- sempre minúsculo
- sem espaço
- sem acento (evitar `"serviços"` → use `"servicos"`)
- usar `_` para separar palavras

Exemplo bom: `vendas_balcao`  
Exemplo ruim: `Vendas Balcão`

---

## 6) Como criar uma tela nova (passo a passo)

1) Criar pasta:

  nomedatela ( o nome deve ser correspondente a pagina/tela que vc esta fazendo exemplo: relatorios corresponde a pagina relatorios dentro da seção adiministrativo )

2) Criar arquivos:

    __init__.py (sempre dentro de cada pasta de uma tela nova crie um arquivo __init__.py pois é ele quem "chama" o codigo)

    page.py (sempre coloque page como nome do arquivo para que a chamada dele seja mais simplificada para o codigo)

    
3) Criar a classe da tela:
- `class PaginaClientes(ctk.CTkFrame): ...`

4) Registrar no `Navigation` (routes):
- `"clientes": PaginaClientes`

5) Criar botão na sidebar com a mesma chave:
- `("Clientes", "clientes")`

Pronto: agora clicar em Clientes abre a nova página.

---

## 7) Convenções (para não virar bagunça)

- Uma classe principal por arquivo (quando der)
- Nome de classes: `PaginaAlgo`, `MenuLateral`, `Navigation`
- Importar tema sempre assim:
  - `from app.config import theme`
- Evitar “código gigante” em um único arquivo
- Se uma tela crescer muito, dividir em:
  - `page.py` (UI principal)
  - `export.py` (exportações)
  - `utils.py` (cálculos)
  - `widgets.py` (componentes da tela)

---

## 8) Dúvidas comuns

**“Por que existe navigation.py se já tem sidebar.py?”**  
Porque a sidebar só mostra botões e dispara eventos.
Quem realmente troca as páginas é a navegação.

**“O placeholder serve pra quê?”**  
Para não quebrar o sistema quando a tela ainda não foi implementada.

---

## 9) Checklist para antes de dar commit

- A tela nova está na pasta correta?
- A chave usada na sidebar é a mesma registrada no Navigation?
- As cores/fonte estão usando `theme.py`?
- Nada de acento nas chaves?
- Não colocou exportação dentro do `main.py`?
- Estou codando na branch feat?
- Estou dando commit na branch develop? 

---

FIM.
