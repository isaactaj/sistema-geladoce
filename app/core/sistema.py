from datetime import datetime, date
from decimal import Decimal

from app.database.repositories.clientes_repository import ClientesRepository
from app.database.repositories.fornecedores_repository import FornecedoresRepository
from app.database.repositories.funcionarios_repository import FuncionariosRepository


class SistemaService:
    """
    Núcleo central do sistema.
    Todas as páginas devem ler e gravar dados aqui.

    Neste momento:
    - Clientes já estão ligados ao MySQL via ClientesRepository
    - Fornecedores já estão ligados ao MySQL via FornecedoresRepository
    - Funcionários já estão ligados ao MySQL via FuncionariosRepository
    - Demais módulos continuam em memória
    """

    def __init__(self):
        # Repositories reais (MySQL)
        self.clientes_repo = ClientesRepository()
        self.fornecedores_repo = FornecedoresRepository()
        self.funcionarios_repo = FuncionariosRepository()

        # Sequências locais (mantidas para módulos ainda em memória)
        self._seq = {
            "cliente": 1,       # mantido por compatibilidade
            "produto": 1,
            "venda": 1,
            "mov_fidelidade": 1,
            "agendamento": 1,
            "delivery": 1,
            "fechamento": 1,
            "funcionario": 1,   # mantido por compatibilidade
            "carrinho": 1,
            "fornecedor": 1,    # mantido por compatibilidade
        }

        # Cache transitório de campos extras de cliente que ainda não
        # estão sendo persistidos por repository específico
        self._clientes_estado = {}

        self._produtos = []
        self._estoque = {}           # produto_id -> quantidade
        self._vendas = []            # balcão, revenda, delivery
        self._mov_fidelidade = []
        self._agendamentos = []
        self._deliveries = []
        self._fechamentos = []

        self._carrinhos = []

    # ======================================================
    # HELPERS
    # ======================================================
    def _next_id(self, chave):
        valor = self._seq[chave]
        self._seq[chave] += 1
        return valor

    def _to_decimal(self, valor):
        if isinstance(valor, Decimal):
            return valor

        txt = str(valor).strip().replace("R$", "").replace(" ", "")
        if not txt:
            return Decimal("0")

        # "1.250,50" -> "1250.50"
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")

        try:
            return Decimal(txt)
        except Exception:
            return Decimal("0")

    def _parse_datetime(self, valor):
        if isinstance(valor, datetime):
            return valor

        if isinstance(valor, date):
            return datetime(valor.year, valor.month, valor.day)

        txt = str(valor).strip()
        formatos = [
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(txt, fmt)
            except ValueError:
                pass

        return datetime.now()

    def _parse_date(self, valor):
        if isinstance(valor, datetime):
            return valor.date()

        if isinstance(valor, date):
            return valor

        txt = str(valor).strip()
        formatos = [
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(txt, fmt).date()
            except ValueError:
                pass

        return None

    def _hora_para_minutos(self, valor):
        try:
            txt = str(valor).strip()
            h, m = txt.split(":")
            h = int(h)
            m = int(m)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except Exception:
            pass
        return None

    def _somente_digitos(self, valor):
        return "".join(ch for ch in str(valor) if ch.isdigit())

    def _normalizar_categoria(self, categoria):
        mapa = {
            "massa": "Sorvete",
            "sorvete": "Sorvete",
            "picolé": "Picolé",
            "picole": "Picolé",
            "açaí": "Açaí",
            "acai": "Açaí",
            "outros": "Outros",
            "outro": "Outros",
        }
        return mapa.get(str(categoria).strip().lower(), "Outros")

    def _normalizar_tipo_item(self, tipo_item=None, eh_insumo=None):
        if eh_insumo is True:
            return "Insumo"

        txt = str(tipo_item).strip().lower() if tipo_item is not None else ""
        if txt in ("insumo", "insumos", "matéria-prima", "materia-prima", "materia prima"):
            return "Insumo"

        return "Produto"

    def _normalizar_status_carrinho(self, status):
        txt = str(status).strip()
        validos = {"Disponível", "Em rota", "Manutenção"}
        return txt if txt in validos else "Disponível"

    def _normalizar_status_agendamento(self, status):
        txt = str(status).strip()
        validos = {"Agendado", "Confirmado", "Cancelado"}
        return txt if txt in validos else "Agendado"

    def _normalizar_tipo_acesso(self, tipo_acesso):
        txt = str(tipo_acesso).strip().lower()
        if txt == "administrador":
            return "Administrador"
        return "Colaborador"

    def _merge_estado_cliente(self, cliente):
        """
        Mescla os dados reais vindos do banco com o cache transitório
        de fidelidade/última compra enquanto essa parte ainda não foi
        totalmente migrada para persistência em banco.
        """
        if not cliente:
            return None

        base = dict(cliente)
        cid = base.get("id")
        if cid in self._clientes_estado:
            base.update(self._clientes_estado[cid])

        return base

    def _salvar_estado_cliente(self, cliente_id, **campos):
        """
        Salva no cache transitório apenas os campos extras que ainda
        não têm persistência própria no banco.
        """
        if not cliente_id:
            return

        estado = self._clientes_estado.setdefault(int(cliente_id), {})
        estado.update(campos)

    # ======================================================
    # CLIENTES (AGORA VIA MYSQL REPOSITORY)
    # ======================================================
    def salvar_cliente(self, nome, cpf_cnpj, telefone, email="", tipo_cliente="Varejo", cliente_id=None):
        cliente = self.clientes_repo.salvar_cliente(
            nome=nome,
            cpf_cnpj=cpf_cnpj,
            telefone=telefone,
            email=email,
            tipo_cliente=tipo_cliente,
            cliente_id=cliente_id,
        )
        return self._merge_estado_cliente(cliente)

    def listar_clientes(self, termo="", tipo_cliente=None):
        clientes = self.clientes_repo.listar_clientes(
            termo=termo,
            tipo_cliente=tipo_cliente,
        )
        return [self._merge_estado_cliente(c) for c in clientes]

    def listar_revendedores(self):
        clientes = self.clientes_repo.listar_revendedores()
        return [self._merge_estado_cliente(c) for c in clientes]

    def obter_cliente(self, cliente_id):
        cliente = self.clientes_repo.obter_cliente(cliente_id)
        return self._merge_estado_cliente(cliente)

    def excluir_cliente(self, cliente_id):
        self._clientes_estado.pop(int(cliente_id), None)
        return self.clientes_repo.excluir_cliente(cliente_id)

    # ======================================================
    # FORNECEDORES (AGORA VIA MYSQL REPOSITORY)
    # ======================================================
    def salvar_fornecedor(self, razao, cnpj, telefone, observacoes="", fornecedor_id=None):
        return self.fornecedores_repo.salvar_fornecedor(
            razao=razao,
            cnpj=cnpj,
            telefone=telefone,
            observacoes=observacoes,
            fornecedor_id=fornecedor_id,
        )

    def listar_fornecedores(self, termo=""):
        return self.fornecedores_repo.listar_fornecedores(termo=termo)

    def obter_fornecedor(self, fornecedor_id):
        return self.fornecedores_repo.obter_fornecedor(fornecedor_id)

    def excluir_fornecedor(self, fornecedor_id):
        return self.fornecedores_repo.excluir_fornecedor(fornecedor_id)

    # ======================================================
    # PRODUTOS + ESTOQUE
    # ======================================================
    def salvar_produto(
        self,
        nome,
        categoria,
        preco,
        produto_id=None,
        estoque_inicial=0,
        tipo_item=None,
        eh_insumo=None,
    ):
        categoria_norm = self._normalizar_categoria(categoria)
        preco_dec = self._to_decimal(preco)

        if produto_id:
            produto = self.obter_produto(produto_id)
            if not produto:
                raise ValueError("Produto não encontrado.")

            produto["nome"] = nome.strip()
            produto["categoria"] = categoria_norm
            produto["preco"] = preco_dec

            if tipo_item is not None or eh_insumo is not None:
                tipo_item_norm = self._normalizar_tipo_item(tipo_item, eh_insumo)
                produto["tipo_item"] = tipo_item_norm
                produto["eh_insumo"] = tipo_item_norm == "Insumo"

            return produto

        tipo_item_norm = self._normalizar_tipo_item(tipo_item, eh_insumo)

        novo = {
            "id": self._next_id("produto"),
            "nome": name.strip(),
            "categoria": categoria_norm,
            "preco": preco_dec,
            "ativo": True,
            "tipo_item": tipo_item_norm,
            "eh_insumo": tipo_item_norm == "Insumo",
        }
        self._produtos.append(novo)
        self._estoque[novo["id"]] = int(estoque_inicial)
        return novo

    def obter_produto(self, produto_id):
        for p in self._produtos:
            if p["id"] == produto_id:
                return p
        return None

    def excluir_produto(self, produto_id):
        self._produtos = [p for p in self._produtos if p["id"] != produto_id]
        self._estoque.pop(produto_id, None)

    def listar_catalogo(self, termo="", categoria="Todos"):
        termo = str(termo).strip().lower()
        categoria_filtro = str(categoria).strip()
        if categoria_filtro != "Todos":
            categoria_filtro = self._normalizar_categoria(categoria_filtro)

        resultado = []

        for p in self._produtos:
            if not p["ativo"]:
                continue

            if categoria_filtro != "Todos" and p["categoria"] != categoria_filtro:
                continue

            texto = f'{p["nome"]} {p["categoria"]} {p.get("tipo_item", "Produto")}'.lower()
            if termo and termo not in texto:
                continue

            resultado.append({
                "id": p["id"],
                "nome": p["nome"],
                "categoria": p["categoria"],
                "preco": p["preco"],
                "estoque": self._estoque.get(p["id"], 0),
                "tipo_item": p.get("tipo_item", "Produto"),
                "eh_insumo": p.get("eh_insumo", False),
                "ativo": p["ativo"],
            })

        return resultado

    def ajustar_estoque(self, produto_id, delta):
        atual = self._estoque.get(produto_id, 0)
        novo = atual + int(delta)

        if novo < 0:
            raise ValueError("Estoque insuficiente.")

        self._estoque[produto_id] = novo
        return novo

    def definir_estoque(self, produto_id, quantidade):
        qtd = int(quantidade)
        if qtd < 0:
            raise ValueError("Quantidade inválida.")
        self._estoque[produto_id] = qtd
        return qtd

    def listar_estoque(self, termo=""):
        termo = str(termo).strip().lower()
        itens = []

        for p in self._produtos:
            qtd = self._estoque.get(p["id"], 0)

            if qtd <= 0:
                status = "Crítico"
            elif qtd <= 10:
                status = "Normal"
            else:
                status = "Cheio"

            texto = f'{p["nome"]} {p.get("tipo_item", "Produto")}'.lower()
            if termo and termo not in texto:
                continue

            itens.append({
                "id": p["id"],
                "produto_id": p["id"],
                "nome": p["nome"],
                "qtd": qtd,
                "status": status,
                "categoria": p["categoria"],
                "preco": p["preco"],
                "tipo_item": p.get("tipo_item", "Produto"),
                "eh_insumo": p.get("eh_insumo", False),
            })

        return itens

    # ======================================================
    # FUNCIONÁRIOS / ENTREGADORES (AGORA VIA MYSQL REPOSITORY)
    # ======================================================
    def salvar_funcionario(
        self,
        nome,
        telefone="",
        cargo="",
        funcionario_id=None,
        cpf="",
        tipo_acesso="Colaborador",
    ):
        return self.funcionarios_repo.salvar_funcionario(
            nome=nome,
            telefone=telefone,
            cargo=cargo,
            funcionario_id=funcionario_id,
            cpf=cpf,
            tipo_acesso=tipo_acesso,
        )

    def listar_funcionarios(self, termo="", cargo=None, tipo_acesso=None):
        return self.funcionarios_repo.listar_funcionarios(
            termo=termo,
            cargo=cargo,
            tipo_acesso=tipo_acesso,
        )

    def listar_entregadores(self, termo=""):
        return self.funcionarios_repo.listar_entregadores(termo=termo)

    def obter_funcionario(self, funcionario_id):
        return self.funcionarios_repo.obter_funcionario(funcionario_id)

    def excluir_funcionario(self, funcionario_id):
        return self.funcionarios_repo.excluir_funcionario(funcionario_id)

    # ======================================================
    # CARRINHOS
    # ======================================================
    def salvar_carrinho(self, nome, capacidade, status="Disponível", id_externo="", carrinho_id=None):
        status_norm = self._normalizar_status_carrinho(status)

        if carrinho_id:
            carrinho = self.obter_carrinho(carrinho_id)
            if not carrinho:
                raise ValueError("Carrinho não encontrado.")

            carrinho["nome"] = nome.strip()
            carrinho["capacidade"] = int(capacidade)
            carrinho["status"] = status_norm
            if str(id_externo).strip():
                carrinho["id_externo"] = str(id_externo).strip()
            return carrinho

        novo_id = self._next_id("carrinho")
        novo = {
            "id": novo_id,
            "id_externo": str(id_externo).strip() or f"CAR-{novo_id:02d}",
            "nome": nome.strip(),
            "capacidade": int(capacidade),
            "status": status_norm,
            "ativo": True,
            "cadastro": datetime.now(),
        }
        self._carrinhos.append(novo)
        return novo

    def listar_carrinhos(self, termo="", status=None):
        termo = str(termo).strip().lower()
        status_filtro = str(status).strip() if status else None
        resultado = []

        for c in self._carrinhos:
            if not c.get("ativo", True):
                continue

            if status_filtro and status_filtro != "Todos" and c["status"] != status_filtro:
                continue

            texto = f'{c["nome"]} {c["id_externo"]}'.lower()
            if termo and termo not in texto:
                continue

            resultado.append(c)

        return resultado

    def obter_carrinho(self, carrinho_id):
        for c in self._carrinhos:
            if c["id"] == carrinho_id:
                return c
        return None

    def excluir_carrinho(self, carrinho_id):
        self._carrinhos = [c for c in self._carrinhos if c["id"] != carrinho_id]

    # ======================================================
    # AGENDAMENTOS
    # ======================================================
    def salvar_agendamento(
        self,
        data,
        hora_inicio=None,
        hora_fim=None,
        carrinho_id=None,
        funcionario_id=None,
        local="",
        status="Agendado",
        observacao="",
        agendamento_id=None,
        # aliases opcionais para compatibilidade
        inicio=None,
        fim=None,
        motorista_id=None,
        obs=None,
    ):
        data_ref = self._parse_date(data)
        if not data_ref:
            raise ValueError("Data do agendamento inválida.")

        hora_ini = str(hora_inicio or inicio or "").strip()
        hora_fim = str(hora_fim or fim or "").strip()
        inicio_min = self._hora_para_minutos(hora_ini)
        fim_min = self._hora_para_minutos(hora_fim)

        if inicio_min is None or fim_min is None:
            raise ValueError("Horários inválidos.")

        if fim_min <= inicio_min:
            raise ValueError("Hora final deve ser maior que a inicial.")

        carrinho_id = int(carrinho_id)
        funcionario_id = int(funcionario_id or motorista_id)

        carrinho = self.obter_carrinho(carrinho_id)
        if not carrinho:
            raise ValueError("Carrinho não encontrado.")

        funcionario = self.obter_funcionario(funcionario_id)
        if not funcionario:
            raise ValueError("Funcionário não encontrado.")

        status_norm = self._normalizar_status_agendamento(status)
        observacao_final = str(observacao or obs or "").strip()

        if agendamento_id:
            agendamento = self.obter_agendamento(agendamento_id)
            if not agendamento:
                raise ValueError("Agendamento não encontrado.")

            agendamento["data"] = data_ref
            agendamento["inicio"] = hora_ini
            agendamento["fim"] = hora_fim
            agendamento["inicio_min"] = inicio_min
            agendamento["fim_min"] = fim_min
            agendamento["carrinho_id"] = carrinho_id
            agendamento["motorista_id"] = funcionario_id
            agendamento["local"] = str(local).strip()
            agendamento["status"] = status_norm
            agendamento["obs"] = observacao_final
            return agendamento

        novo = {
            "id": self._next_id("agendamento"),
            "data": data_ref,
            "inicio": hora_ini,
            "fim": hora_fim,
            "inicio_min": inicio_min,
            "fim_min": fim_min,
            "carrinho_id": carrinho_id,
            "motorista_id": funcionario_id,
            "local": str(local).strip(),
            "status": status_norm,
            "obs": observacao_final,
            "cadastro": datetime.now(),
        }
        self._agendamentos.append(novo)
        return novo

    def listar_agendamentos(self, data=None):
        data_filtro = self._parse_date(data) if data else None
        resultado = []

        for a in self._agendamentos:
            if data_filtro and a["data"] != data_filtro:
                continue

            carrinho = self.obter_carrinho(a["carrinho_id"])
            funcionario = self.obter_funcionario(a["motorista_id"])

            resultado.append({
                "id": a["id"],
                "data": a["data"],
                "inicio": a["inicio"],
                "fim": a["fim"],
                "inicio_min": a["inicio_min"],
                "fim_min": a["fim_min"],
                "carrinho_id": a["carrinho_id"],
                "carrinho_nome": carrinho["nome"] if carrinho else "",
                "carrinho_id_externo": carrinho["id_externo"] if carrinho else "",
                "motorista_id": a["motorista_id"],
                "motorista_nome": funcionario["nome"] if funcionario else "",
                "local": a["local"],
                "status": a["status"],
                "obs": a["obs"],
            })

        resultado.sort(key=lambda x: (x["data"], x["inicio_min"]))
        return resultado

    def obter_agendamento(self, agendamento_id):
        for a in self._agendamentos:
            if a["id"] == agendamento_id:
                return a
        return None

    def excluir_agendamento(self, agendamento_id):
        self._agendamentos = [a for a in self._agendamentos if a["id"] != agendamento_id]

    def remover_agendamento(self, agendamento_id):
        self.excluir_agendamento(agendamento_id)

    # ======================================================
    # FIDELIDADE - RN05
    # ======================================================
    def calcular_pontos_rn05(self, tipo_cliente, valor_total):
        valor = self._to_decimal(valor_total)
        tipo = str(tipo_cliente).strip().lower()

        if valor <= 0:
            return 0

        if tipo == "varejo":
            return int(valor // Decimal("5"))

        if tipo == "revendedor":
            return int(valor // Decimal("50")) * 2

        return 0

    def movimentar_fidelidade(self, cliente_id, acao, pontos, motivo="", venda_id=None):
        cliente = self.obter_cliente(cliente_id)
        if not cliente:
            raise ValueError("Cliente não encontrado.")

        pontos = int(pontos)
        acao = acao.upper()

        atual = int(cliente.get("pontos_atuais", 0))
        total = int(cliente.get("total_acumulado", 0))

        if acao == "ADICIONAR":
            atual += pontos
            total += pontos

        elif acao == "REMOVER":
            atual = max(0, atual - pontos)

        elif acao == "RESGATAR":
            if pontos > atual:
                raise ValueError("Pontos insuficientes para resgate.")
            atual -= pontos

        elif acao == "BONUS":
            atual += pontos
            total += pontos

        elif acao == "ZERAR":
            atual = 0

        else:
            raise ValueError("Ação de fidelidade inválida.")

        # Mantém os pontos disponíveis durante a sessão do app
        # sem alterar indevidamente o status do cliente.
        self._salvar_estado_cliente(
            cliente_id,
            pontos_atuais=atual,
            total_acumulado=total,
        )

        mov = {
            "id": self._next_id("mov_fidelidade"),
            "cliente_id": cliente_id,
            "acao": acao,
            "pontos": pontos,
            "motivo": motivo.strip() or "Sem motivo",
            "venda_id": venda_id,
            "data": datetime.now(),
        }
        self._mov_fidelidade.append(mov)
        return mov

    def obter_extrato_fidelidade(self, cliente_id):
        return [m for m in self._mov_fidelidade if m["cliente_id"] == cliente_id]

    # ======================================================
    # VENDAS
    # ======================================================
    def registrar_venda(
        self,
        tipo,
        itens,
        forma_pagamento,
        cliente_id=None,
        revendedor_id=None,
        desconto=0,
        taxa_entrega=0,
        observacao="",
        data_venda=None,
    ):
        """
        itens esperado:
        [
            {"produto_id": 1, "qtd": 2},
            {"produto_id": 4, "qtd": 1}
        ]
        """

        tipo = str(tipo).strip().upper()
        if tipo not in ("BALCAO", "REVENDA", "DELIVERY"):
            raise ValueError("Tipo de venda inválido.")

        if not itens:
            raise ValueError("A venda precisa ter ao menos 1 item.")

        desconto = self._to_decimal(desconto)
        taxa_entrega = self._to_decimal(taxa_entrega)
        data_ref = self._parse_datetime(data_venda) if data_venda else datetime.now()

        itens_normalizados = []
        subtotal = Decimal("0")

        # 1) validar produtos e estoque
        for item in itens:
            produto_id = int(item["produto_id"])
            qtd = int(item["qtd"])

            if qtd <= 0:
                raise ValueError("Quantidade inválida.")

            produto = self.obter_produto(produto_id)
            if not produto:
                raise ValueError(f"Produto {produto_id} não encontrado.")

            estoque_atual = self._estoque.get(produto_id, 0)
            if estoque_atual < qtd:
                raise ValueError(f"Estoque insuficiente para {produto['nome']}.")

            unitario = self._to_decimal(produto["preco"])
            total_item = unitario * qtd

            itens_normalizados.append({
                "produto_id": produto_id,
                "produto_nome": produto["nome"],
                "categoria": produto["categoria"],
                "qtd": qtd,
                "unitario": unitario,
                "total": total_item,
            })
            subtotal += total_item

        if desconto < 0:
            desconto = Decimal("0")
        if desconto > subtotal:
            desconto = subtotal

        if taxa_entrega < 0:
            taxa_entrega = Decimal("0")

        total_produtos = subtotal - desconto
        total = total_produtos + taxa_entrega

        # 2) baixar estoque
        for item in itens_normalizados:
            self.ajustar_estoque(item["produto_id"], -item["qtd"])

        venda = {
            "id": self._next_id("venda"),
            "tipo": tipo,
            "data": data_ref,
            "cliente_id": cliente_id,
            "revendedor_id": revendedor_id,
            "forma_pagamento": forma_pagamento,
            "observacao": observacao.strip(),
            "subtotal": subtotal,
            "desconto": desconto,
            "taxa_entrega": taxa_entrega,
            "total": total,
            "itens": itens_normalizados,
        }
        self._vendas.append(venda)

        # 3) aplicar fidelidade automática
        cliente_para_pontos = None
        if tipo == "REVENDA":
            cliente_para_pontos = revendedor_id
        else:
            cliente_para_pontos = cliente_id

        if cliente_para_pontos:
            cliente = self.obter_cliente(cliente_para_pontos)
            if cliente:
                # registra última compra no cache transitório
                self._salvar_estado_cliente(cliente_para_pontos, ultima_compra=data_ref)

                # Fidelidade usa o valor dos produtos (sem taxa de entrega)
                pontos = self.calcular_pontos_rn05(cliente["tipo_cliente"], total_produtos)
                if pontos > 0:
                    self.movimentar_fidelidade(
                        cliente_id=cliente_para_pontos,
                        acao="ADICIONAR",
                        pontos=pontos,
                        motivo=f"Crédito automático RN05 - venda {tipo}",
                        venda_id=venda["id"],
                    )

        return venda

    def listar_vendas(self, tipo=None, data_inicial=None, data_final=None):
        resultado = []

        dt_ini = self._parse_datetime(data_inicial) if data_inicial else None
        dt_fim = self._parse_datetime(data_final) if data_final else None

        for v in self._vendas:
            if tipo and v["tipo"] != str(tipo).strip().upper():
                continue

            if dt_ini and v["data"] < dt_ini:
                continue
            if dt_fim and v["data"] > dt_fim:
                continue

            resultado.append(v)

        return resultado

    # ======================================================
    # FECHAMENTO
    # ======================================================
    def salvar_fechamento(
        self,
        data_fechamento,
        vendas_brutas,
        descontos,
        cancelamentos,
        dinheiro,
        pix,
        cartao,
        sangria=0,
        caixa_inicial=0,
        contado_caixa=0,
        observacao="",
    ):
        """
        Salva ou atualiza o fechamento do dia.

        Regras atuais:
        - Não utiliza suprimento
        - Caixa previsto = caixa inicial + dinheiro - sangria
        """
        data_ref = self._parse_date(data_fechamento)
        if not data_ref:
            raise ValueError("Data do fechamento inválida.")

        vendas_brutas_dec = self._to_decimal(vendas_brutas)
        descontos_dec = self._to_decimal(descontos)
        cancelamentos_dec = self._to_decimal(cancelamentos)

        dinheiro_dec = self._to_decimal(dinheiro)
        pix_dec = self._to_decimal(pix)
        cartao_dec = self._to_decimal(cartao)

        sangria_dec = self._to_decimal(sangria)
        caixa_inicial_dec = self._to_decimal(caixa_inicial)
        contado_caixa_dec = self._to_decimal(contado_caixa)

        total_liquido = vendas_brutas_dec - descontos_dec - cancelamentos_dec
        if total_liquido < 0:
            total_liquido = Decimal("0")

        total_recebido = dinheiro_dec + pix_dec + cartao_dec
        previsto_em_caixa = caixa_inicial_dec + dinheiro_dec - sangria_dec
        diferenca = contado_caixa_dec - previsto_em_caixa

        fechamento_existente = self.obter_fechamento_por_data(data_ref)

        if fechamento_existente:
            fechamento_existente["vendas_brutas"] = vendas_brutas_dec
            fechamento_existente["descontos"] = descontos_dec
            fechamento_existente["cancelamentos"] = cancelamentos_dec
            fechamento_existente["total_liquido"] = total_liquido
            fechamento_existente["dinheiro"] = dinheiro_dec
            fechamento_existente["pix"] = pix_dec
            fechamento_existente["cartao"] = cartao_dec
            fechamento_existente["total_recebido"] = total_recebido
            fechamento_existente["sangria"] = sangria_dec
            fechamento_existente["caixa_inicial"] = caixa_inicial_dec
            fechamento_existente["contado_caixa"] = contado_caixa_dec
            fechamento_existente["previsto_em_caixa"] = previsto_em_caixa
            fechamento_existente["diferenca"] = diferenca
            fechamento_existente["observacao"] = str(observacao).strip()
            fechamento_existente["atualizado_em"] = datetime.now()
            return fechamento_existente

        novo = {
            "id": self._next_id("fechamento"),
            "data": data_ref,
            "vendas_brutas": vendas_brutas_dec,
            "descontos": descontos_dec,
            "cancelamentos": cancelamentos_dec,
            "total_liquido": total_liquido,
            "dinheiro": dinheiro_dec,
            "pix": pix_dec,
            "cartao": cartao_dec,
            "total_recebido": total_recebido,
            "sangria": sangria_dec,
            "caixa_inicial": caixa_inicial_dec,
            "contado_caixa": contado_caixa_dec,
            "previsto_em_caixa": previsto_em_caixa,
            "diferenca": diferenca,
            "observacao": str(observacao).strip(),
            "criado_em": datetime.now(),
            "atualizado_em": None,
        }
        self._fechamentos.append(novo)
        return novo

    def listar_fechamentos(self, data_inicial=None, data_final=None):
        dt_ini = self._parse_date(data_inicial) if data_inicial else None
        dt_fim = self._parse_date(data_final) if data_final else None

        resultado = []
        for f in self._fechamentos:
            if dt_ini and f["data"] < dt_ini:
                continue
            if dt_fim and f["data"] > dt_fim:
                continue
            resultado.append(f)

        resultado.sort(key=lambda x: x["data"], reverse=True)
        return resultado

    def listar_fechamento(self, data_inicial=None, data_final=None):
        """
        Alias para compatibilidade com páginas que chamem no singular.
        """
        return self.listar_fechamentos(data_inicial=data_inicial, data_final=data_final)

    def obter_fechamento_por_data(self, data_ref):
        dia = self._parse_date(data_ref)
        if not dia:
            return None

        for f in self._fechamentos:
            if f["data"] == dia:
                return f
        return None

    def resumo_fechamento(self, data_ref=None):
        base = self._parse_datetime(data_ref) if data_ref else datetime.now()
        dia = base.date()

        vendas_dia = [v for v in self._vendas if v["data"].date() == dia]

        vendas_brutas = sum((v["subtotal"] for v in vendas_dia), Decimal("0"))
        descontos = sum((v["desconto"] for v in vendas_dia), Decimal("0"))
        taxas_entrega = sum((v.get("taxa_entrega", Decimal("0")) for v in vendas_dia), Decimal("0"))
        cancelamentos = Decimal("0")
        liquido = sum((v["total"] for v in vendas_dia), Decimal("0"))

        dinheiro = sum((v["total"] for v in vendas_dia if v["forma_pagamento"] == "Dinheiro"), Decimal("0"))
        pix = sum((v["total"] for v in vendas_dia if v["forma_pagamento"] == "Pix"), Decimal("0"))
        cartao = sum((v["total"] for v in vendas_dia if v["forma_pagamento"] == "Cartão"), Decimal("0"))
        prazo = sum((v["total"] for v in vendas_dia if v["forma_pagamento"] == "Prazo"), Decimal("0"))

        return {
            "data": dia,
            "vendas_brutas": vendas_brutas,
            "descontos": descontos,
            "taxas_entrega": taxas_entrega,
            "cancelamentos": cancelamentos,
            "total_liquido": liquido,
            "dinheiro": dinheiro,
            "pix": pix,
            "cartao": cartao,
            "prazo": prazo,
            "qtd_vendas": len(vendas_dia),
        }

    # ======================================================
    # RELATÓRIOS
    # ======================================================
    def dados_relatorio(self, mes, ano, tipo="Todos", categoria="Todos"):
        mes = int(mes)
        ano = int(ano)

        vendas_filtradas = []
        faturamento = Decimal("0")
        qtd_vendas = 0
        serie_por_dia = {}
        produtos_vendidos = {}
        taxas_entrega = Decimal("0")

        for v in self._vendas:
            if v["data"].month != mes or v["data"].year != ano:
                continue

            if tipo != "Todos":
                tipo_map = {
                    "Balcão": "BALCAO",
                    "Revenda": "REVENDA",
                    "Serviços": "DELIVERY",
                }
                tipo_real = tipo_map.get(tipo, None)
                if tipo_real and v["tipo"] != tipo_real:
                    continue

            valor_considerado = Decimal("0")
            itens_considerados = []

            for item in v["itens"]:
                if categoria != "Todos" and item["categoria"] != categoria:
                    continue

                valor_considerado += item["total"]
                itens_considerados.append(item)

                produtos_vendidos[item["produto_nome"]] = produtos_vendidos.get(item["produto_nome"], 0) + item["qtd"]

            if categoria != "Todos" and not itens_considerados:
                continue

            if categoria == "Todos":
                valor_considerado = v["total"]
                taxas_entrega += v.get("taxa_entrega", Decimal("0"))

            vendas_filtradas.append(v)
            faturamento += valor_considerado
            qtd_vendas += 1

            dia = v["data"].day
            serie_por_dia[dia] = serie_por_dia.get(dia, Decimal("0")) + valor_considerado

        ticket_medio = Decimal("0")
        if qtd_vendas > 0:
            ticket_medio = faturamento / qtd_vendas

        top_produtos = sorted(produtos_vendidos.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "faturamento": faturamento,
            "qtd_vendas": qtd_vendas,
            "ticket_medio": ticket_medio,
            "serie_por_dia": serie_por_dia,
            "top_produtos": top_produtos,
            "vendas": vendas_filtradas,
            "taxas_entrega": taxas_entrega,
        }