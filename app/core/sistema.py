# app/core/sistema.py
from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.database.connection import conectar

from app.database.repositories.clientes_repository import ClientesRepository
from app.database.repositories.fornecedores_repository import FornecedoresRepository
from app.database.repositories.funcionarios_repository import FuncionariosRepository
from app.database.repositories.fidelidade_repository import FidelidadeRepository
from app.database.repositories.produtos_repository import ProdutosRepository
from app.database.repositories.usuarios_repository import UsuariosRepository

from app.database.repositories.formas_pagamento_repository import FormasPagamentoRepository
from app.database.repositories.vendas_repository import VendasRepository
from app.database.repositories.fechamentos_repository import FechamentosRepository
from app.database.repositories.carrinhos_repository import CarrinhosRepository
from app.database.repositories.agendamentos_repository import AgendamentosRepository
from app.database.repositories.delivery_repository import DeliveryRepository


class SistemaService:
    """
    Núcleo central do sistema Geladoce (MySQL).
    """

    def __init__(self):
        self.clientes_repo = ClientesRepository()
        self.fornecedores_repo = FornecedoresRepository()
        self.funcionarios_repo = FuncionariosRepository()
        self.usuarios_repo = UsuariosRepository()
        self.fidelidade_repo = FidelidadeRepository()
        self.produtos_repo = ProdutosRepository()

        self.formas_repo = FormasPagamentoRepository()
        self.vendas_repo = VendasRepository()
        self.fechamentos_repo = FechamentosRepository()
        self.carrinhos_repo = CarrinhosRepository()
        self.agendamentos_repo = AgendamentosRepository()

        self.delivery_repo = DeliveryRepository()

        self._clientes_estado: Dict[int, Dict[str, Any]] = {}

    # ======================================================
    # HELPERS
    # ======================================================
    def _to_decimal(self, valor: Any) -> Decimal:
        if isinstance(valor, Decimal):
            return valor
        txt = str(valor).strip().replace("R$", "").replace(" ", "")
        if not txt:
            return Decimal("0")
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")
        try:
            return Decimal(txt)
        except Exception:
            return Decimal("0")

    def _parse_datetime(self, valor: Any) -> datetime:
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

    def _parse_date(self, valor: Any) -> Optional[date]:
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        txt = str(valor).strip()
        formatos = ["%Y-%m-%d", "%d/%m/%Y"]
        for fmt in formatos:
            try:
                return datetime.strptime(txt, fmt).date()
            except ValueError:
                pass
        return None

    def _hora_para_minutos(self, valor: Any) -> Optional[int]:
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

    def _salvar_estado_cliente(self, cliente_id: int, **campos) -> None:
        if not cliente_id:
            return
        estado = self._clientes_estado.setdefault(int(cliente_id), {})
        estado.update(campos)

    def _merge_estado_cliente(self, cliente: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not cliente:
            return None
        base = dict(cliente)
        cid = base.get("id")
        if cid in self._clientes_estado:
            estado = dict(self._clientes_estado[cid])
            estado.pop("pontos_atuais", None)
            estado.pop("total_acumulado", None)
            base.update(estado)
        return base

    def _atualizar_ultima_compra_db(self, cliente_id: int, data_ref: datetime) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute(
                "UPDATE clientes SET ultima_compra=%s WHERE id=%s",
                (data_ref, int(cliente_id)),
            )
            conn.commit()
        except Exception:
            self._salvar_estado_cliente(cliente_id, ultima_compra=data_ref)
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    # ======================================================
    # USUÁRIOS
    # ======================================================
    def garantir_admin_padrao(self) -> None:
        self.usuarios_repo.garantir_admin_padrao()

    def autenticar(self, login_ou_cpf: str, senha: str) -> Optional[Dict[str, Any]]:
        return self.usuarios_repo.autenticar(login_ou_cpf, senha)

    def criar_usuario(self, nome: str, cpf: str, senha: str, tipo_acesso: str) -> Dict[str, Any]:
        return self.usuarios_repo.criar_usuario(nome, cpf, senha, tipo_acesso)

    def alterar_senha(self, login_ou_cpf: str, nova_senha: str) -> None:
        self.usuarios_repo.alterar_senha(login_ou_cpf, nova_senha)

    # ======================================================
    # CLIENTES
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
        clientes = self.clientes_repo.listar_clientes(termo=termo, tipo_cliente=tipo_cliente)
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
    # FORNECEDORES
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
        estoque_inicial=None,
        tipo_item=None,
        eh_insumo=None,
        fornecedor_id=None,
        ativo=True,
    ):
        return self.produtos_repo.salvar_produto(
            nome=nome,
            categoria=categoria,
            preco=preco,
            produto_id=produto_id,
            estoque_inicial=estoque_inicial,
            tipo_item=tipo_item,
            eh_insumo=eh_insumo,
            fornecedor_id=fornecedor_id,
            ativo=ativo,
        )

    def salvar_insumo(
        self,
        nome,
        quantidade_inicial=0,
        fornecedor_id=None,
        produto_id=None,
        ativo=False,
    ):
        return self.produtos_repo.salvar_insumo(
            nome=nome,
            quantidade_inicial=quantidade_inicial,
            fornecedor_id=fornecedor_id,
            produto_id=produto_id,
            ativo=ativo,
        )

    def obter_produto(self, produto_id):
        return self.produtos_repo.obter_produto(int(produto_id))

    def obter_item_estoque(self, produto_id):
        return self.produtos_repo.obter_item_estoque(int(produto_id))

    def excluir_produto(self, produto_id):
        return self.produtos_repo.excluir_produto(int(produto_id))

    def listar_catalogo(self, termo="", categoria="Todos"):
        return self.produtos_repo.listar_catalogo(
            termo=termo,
            categoria=categoria,
            incluir_inativos=False,
            incluir_insumos=False,
        )

    def listar_produtos(self, termo="", categoria="Todos", incluir_inativos=False):
        return self.produtos_repo.listar_produtos_admin(
            termo=termo,
            categoria=categoria,
            incluir_inativos=incluir_inativos,
        )

    def ajustar_estoque(self, produto_id, delta):
        return self.produtos_repo.ajustar_estoque(int(produto_id), int(delta))

    def definir_estoque(self, produto_id, quantidade):
        return self.produtos_repo.definir_estoque(int(produto_id), int(quantidade))

    def listar_estoque(self, termo=""):
        return self.produtos_repo.listar_estoque(termo=termo)

    # ======================================================
    # FUNCIONÁRIOS / ENTREGADORES
    # ======================================================
    def salvar_funcionario(self, nome, telefone="", cargo="", funcionario_id=None, cpf="", tipo_acesso="Colaborador"):
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
    # MOTORISTAS
    # ======================================================
    def salvar_motorista(self, nome: str, cpf: str, telefone: str, motorista_id=None):
        if hasattr(self.funcionarios_repo, "salvar_motorista"):
            return self.funcionarios_repo.salvar_motorista(
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                motorista_id=int(motorista_id) if motorista_id else None
            )
        return self.funcionarios_repo.salvar_funcionario(
            nome=nome,
            cpf=cpf,
            telefone=telefone,
            cargo="Motorista",
            tipo_acesso="Colaborador",
            funcionario_id=int(motorista_id) if motorista_id else None,
        )

    def listar_motoristas(self, termo=""):
        if hasattr(self.funcionarios_repo, "listar_motoristas"):
            return self.funcionarios_repo.listar_motoristas(termo=termo)
        return self.funcionarios_repo.listar_funcionarios(termo=termo, cargo="Motorista")

    def obter_motorista(self, motorista_id):
        if hasattr(self.funcionarios_repo, "obter_motorista"):
            return self.funcionarios_repo.obter_motorista(int(motorista_id))
        return self.funcionarios_repo.obter_funcionario(int(motorista_id))

    def excluir_motorista(self, motorista_id):
        if hasattr(self.funcionarios_repo, "excluir_motorista"):
            return self.funcionarios_repo.excluir_motorista(int(motorista_id))
        return self.funcionarios_repo.excluir_funcionario(int(motorista_id))

    # ======================================================
    # CARRINHOS
    # ======================================================
    def salvar_carrinho(self, nome, capacidade, status="Disponível", id_externo=None, carrinho_id=None):
        return self.carrinhos_repo.salvar_carrinho(
            nome=nome,
            capacidade=capacidade,
            status=status,
            id_externo=id_externo,
            carrinho_id=carrinho_id,
        )

    def listar_carrinhos(self, termo="", status=None):
        return self.carrinhos_repo.listar_carrinhos(termo=termo, status=status)

    def obter_carrinho(self, carrinho_id):
        return self.carrinhos_repo.obter_carrinho(int(carrinho_id))

    def excluir_carrinho(self, carrinho_id):
        return self.carrinhos_repo.excluir_carrinho(int(carrinho_id))

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
        inicio=None,
        fim=None,
        motorista_id=None,
        obs=None,
        **kwargs,
    ):
        data_ref = self._parse_date(data)
        if not data_ref:
            raise ValueError("Data do agendamento inválida.")

        hora_ini = str(hora_inicio or inicio or "").strip()
        hora_fin = str(hora_fim or fim or "").strip()
        ini_min = self._hora_para_minutos(hora_ini)
        fim_min = self._hora_para_minutos(hora_fin)
        if ini_min is None or fim_min is None:
            raise ValueError("Horários inválidos.")
        if fim_min <= ini_min:
            raise ValueError("Hora final deve ser maior que a inicial.")

        if motorista_id is None and funcionario_id not in (None, "", "None"):
            motorista_id = funcionario_id

        if carrinho_id in (None, "", "None"):
            raise ValueError("Selecione um carrinho.")

        return self.agendamentos_repo.salvar_agendamento(
            data=data_ref,
            inicio=hora_ini,
            fim=hora_fin,
            inicio_min=ini_min,
            fim_min=fim_min,
            carrinho_id=int(carrinho_id),
            motorista_id=int(motorista_id),
            local=str(local or "").strip(),
            status=status,
            obs=str(observacao or obs or "").strip(),
            agendamento_id=agendamento_id,
        )

    def listar_agendamentos(self, data=None, data_inicial=None, data_final=None, incluir_cancelados=False):
        data_ref = self._parse_date(data) if data else None
        d_ini = self._parse_date(data_inicial) if data_inicial else None
        d_fim = self._parse_date(data_final) if data_final else None
        return self.agendamentos_repo.listar_agendamentos(
            data=data_ref,
            data_inicial=d_ini,
            data_final=d_fim,
            incluir_cancelados=bool(incluir_cancelados),
        )

    def obter_agendamento(self, agendamento_id):
        return self.agendamentos_repo.obter_agendamento(int(agendamento_id))

    def excluir_agendamento(self, agendamento_id):
        return self.agendamentos_repo.excluir_agendamento(int(agendamento_id))

    def remover_agendamento(self, agendamento_id):
        return self.excluir_agendamento(agendamento_id)

    # ======================================================
    # FIDELIDADE
    # ======================================================
    def calcular_pontos_rn05(self, tipo_cliente, valor_total):
        return int(self.fidelidade_repo.calcular_pontos_rn05(tipo_cliente, valor_total))

    def movimentar_fidelidade(self, cliente_id, acao, pontos, motivo="", venda_id=None, usuario_id=None):
        return self.fidelidade_repo.movimentar_fidelidade(
            cliente_id=int(cliente_id),
            acao=str(acao),
            pontos=int(pontos),
            motivo=str(motivo),
            venda_id=int(venda_id) if venda_id is not None else None,
            usuario_id=int(usuario_id) if usuario_id is not None else None,
        )

    def obter_extrato_fidelidade(self, cliente_id):
        return self.fidelidade_repo.obter_extrato_fidelidade(int(cliente_id))

    # ======================================================
    # FORMAS DE PAGAMENTO
    # ======================================================
    def listar_formas_pagamento(self) -> List[Dict[str, Any]]:
        return self.formas_repo.listar_formas()

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
        usuario_id=None,
    ):
        tipo = str(tipo).strip().upper()
        if tipo not in ("BALCAO", "REVENDA", "DELIVERY"):
            raise ValueError("Tipo de venda inválido.")
        if not itens:
            raise ValueError("A venda precisa ter ao menos 1 item.")

        if tipo == "REVENDA" and (revendedor_id is None) and (cliente_id is not None):
            revendedor_id = cliente_id
            cliente_id = None

        desconto_dec = self._to_decimal(desconto)
        taxa_entrega_dec = self._to_decimal(taxa_entrega)
        data_ref = self._parse_datetime(data_venda) if data_venda else datetime.now()

        venda = self.vendas_repo.registrar_venda(
            tipo=tipo,
            itens=itens,
            forma_pagamento=forma_pagamento,
            cliente_id=int(cliente_id) if cliente_id else None,
            revendedor_id=int(revendedor_id) if revendedor_id else None,
            desconto=desconto_dec,
            taxa_entrega=taxa_entrega_dec,
            observacao=observacao,
            data_venda=data_ref,
            status="FINALIZADA",
        )

        cliente_para_pontos = venda.get("revendedor_id") if tipo == "REVENDA" else venda.get("cliente_id")
        if cliente_para_pontos:
            cliente = self.obter_cliente(cliente_para_pontos)
            if cliente:
                self._atualizar_ultima_compra_db(cliente_para_pontos, data_ref)
                total_produtos = self._to_decimal(venda.get("subtotal", 0)) - self._to_decimal(venda.get("desconto", 0))
                if total_produtos < 0:
                    total_produtos = Decimal("0")
                pontos = self.calcular_pontos_rn05(cliente.get("tipo_cliente", "Varejo"), total_produtos)
                if pontos > 0:
                    self.movimentar_fidelidade(
                        cliente_id=cliente_para_pontos,
                        acao="ADICIONAR",
                        pontos=pontos,
                        motivo=f"Crédito automático RN05 - venda {tipo}",
                        venda_id=venda["id"],
                        usuario_id=usuario_id,
                    )

        return venda

    def listar_vendas(self, tipo=None, data_inicial=None, data_final=None):
        dt_ini = self._parse_datetime(data_inicial) if data_inicial else None
        dt_fim = self._parse_datetime(data_final) if data_final else None
        tipo_norm = str(tipo).strip().upper() if tipo else None
        return self.vendas_repo.listar_vendas(tipo=tipo_norm, data_inicial=dt_ini, data_final=dt_fim, incluir_itens=True)

    # ======================================================
    # DELIVERY
    # ======================================================
    def _status_delivery_gera_venda(self, status: str) -> bool:
        return str(status or "").strip() in {"Em preparo", "Em rota", "Entregue"}

    def salvar_pedido_delivery(self, pedido: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(pedido, dict):
            raise ValueError("Pedido inválido.")

        data_ref = self._parse_date(pedido.get("data"))
        if not data_ref:
            raise ValueError("Data do delivery inválida (use AAAA-MM-DD).")

        prev = str(pedido.get("prev") or "").strip() or None

        cliente = pedido.get("cliente") or {}
        endereco = pedido.get("endereco") or {}

        cliente_nome = str(cliente.get("nome") or "").strip()
        cliente_tel = str(cliente.get("telefone") or "").strip()

        itens_in = pedido.get("itens") or []
        itens = []
        for it in itens_in:
            pid = it.get("produto_id", it.get("id"))
            qtd = it.get("qtd")
            itens.append({"produto_id": int(pid), "qtd": int(qtd)})

        taxa = pedido.get("taxa", 0)
        forma = pedido.get("pagamento") or pedido.get("forma_pagamento") or "Pix"
        status = pedido.get("status") or "Pendente"
        obs = pedido.get("obs") or pedido.get("observacao") or ""

        entregador_id = pedido.get("entregador_id")
        pedido_id = pedido.get("id")

        salvo = self.delivery_repo.salvar_pedido(
            pedido_id=int(pedido_id) if pedido_id else None,
            data=data_ref,
            prev_saida=prev,
            cliente_id=None,
            cliente_nome=cliente_nome,
            cliente_telefone=cliente_tel,
            end_rua=endereco.get("rua", ""),
            end_num=endereco.get("numero", None),
            end_bairro=endereco.get("bairro", ""),
            end_cidade=endereco.get("cidade", "Belém"),
            end_comp=endereco.get("comp", None),
            entregador_id=int(entregador_id) if entregador_id not in (None, "", "None") else None,
            forma_pagamento=forma,
            status=status,
            taxa_entrega=taxa,
            obs=obs,
            itens=itens,
        )

        if self._status_delivery_gera_venda(salvo.get("status")) and not salvo.get("venda_id"):
            venda = self.registrar_venda(
                tipo="DELIVERY",
                cliente_id=None,
                itens=[{"produto_id": i["produto_id"], "qtd": i["qtd"]} for i in itens],
                forma_pagamento=salvo.get("forma_pagamento"),
                desconto=0,
                taxa_entrega=salvo.get("taxa_entrega", 0),
                observacao=salvo.get("obs") or "",
                data_venda=str(data_ref),
            )
            self.delivery_repo.vincular_venda(int(salvo["id"]), int(venda["id"]))
            salvo = self.delivery_repo.obter_pedido(int(salvo["id"])) or salvo

        return self._normalizar_delivery_para_ui(salvo)

    def _normalizar_delivery_para_ui(self, row: Dict[str, Any]) -> Dict[str, Any]:
        itens_ui = []
        for it in (row.get("itens") or []):
            itens_ui.append({
                "id": int(it.get("produto_id")),
                "nome": it.get("produto_nome") or "",
                "preco": float(self._to_decimal(it.get("unitario", 0))),
                "qtd": int(it.get("qtd") or 0),
            })

        return {
            "id": int(row.get("id")),
            "data": row.get("data"),
            "prev": row.get("prev_saida") or "",
            "cliente": {"nome": row.get("cliente_nome") or "", "telefone": row.get("cliente_telefone") or ""},
            "endereco": {
                "rua": row.get("end_rua") or "",
                "numero": row.get("end_num") or "",
                "bairro": row.get("end_bairro") or "",
                "cidade": row.get("end_cidade") or "Belém",
                "comp": row.get("end_comp") or "",
            },
            "itens": itens_ui,
            "taxa": float(self._to_decimal(row.get("taxa_entrega", 0))),
            "total": float(self._to_decimal(row.get("total", 0))),
            "pagamento": row.get("forma_pagamento") or "Pix",
            "status": row.get("status") or "Pendente",
            "entregador_id": row.get("entregador_id"),
            "entregador_nome": row.get("entregador_nome") or "",
            "obs": row.get("obs") or "",
            "venda_registrada": bool(row.get("venda_id")),
            "venda_id": row.get("venda_id"),
        }

    def listar_delivery_dia(self, data_ref) -> List[Dict[str, Any]]:
        dia = self._parse_date(data_ref) if data_ref else date.today()
        if not dia:
            dia = date.today()
        rows = self.delivery_repo.listar_por_data(dia)

        saida = []
        for r in rows:
            saida.append({
                "id": int(r["id"]),
                "data": r.get("data"),
                "prev": r.get("prev_saida") or "",
                "cliente": {"nome": r.get("cliente_nome") or "", "telefone": r.get("cliente_telefone") or ""},
                "total": float(self._to_decimal(r.get("total", 0))),
                "status": r.get("status") or "Pendente",
                "pagamento": r.get("forma_pagamento") or "Pix",
                "taxa": float(self._to_decimal(r.get("taxa_entrega", 0))),
                "entregador_id": r.get("entregador_id"),
                "entregador_nome": r.get("entregador_nome") or "",
                "venda_registrada": bool(r.get("venda_id")),
                "venda_id": r.get("venda_id"),
            })
        return saida

    def obter_delivery(self, pedido_id: int) -> Optional[Dict[str, Any]]:
        row = self.delivery_repo.obter_pedido(int(pedido_id))
        return self._normalizar_delivery_para_ui(row) if row else None

    def excluir_delivery(self, pedido_id: int) -> None:
        self.delivery_repo.excluir_pedido(int(pedido_id))

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
        responsavel_id=None,
    ):
        data_ref = self._parse_date(data_fechamento)
        if not data_ref:
            raise ValueError("Data do fechamento inválida.")

        return self.fechamentos_repo.salvar_fechamento(
            data=data_ref,
            caixa_inicial=self._to_decimal(caixa_inicial),
            sangria=self._to_decimal(sangria),
            contado_caixa=self._to_decimal(contado_caixa),
            observacao=str(observacao).strip(),
            responsavel_id=int(responsavel_id) if responsavel_id else None,
        )

    def listar_fechamentos(self, data_inicial=None, data_final=None):
        d_ini = self._parse_date(data_inicial) if data_inicial else None
        d_fim = self._parse_date(data_final) if data_final else None
        return self.fechamentos_repo.listar_fechamentos(data_inicial=d_ini, data_final=d_fim)

    def obter_fechamento_por_data(self, data_ref):
        dia = self._parse_date(data_ref)
        if not dia:
            return None
        return self.fechamentos_repo.obter_por_data(dia)

    def resumo_fechamento(self, data_ref=None):
        base = self._parse_datetime(data_ref) if data_ref else datetime.now()
        dia = base.date()
        resumo = self.fechamentos_repo.resumo_por_data(dia)
        if resumo:
            return resumo
        return self.vendas_repo.resumo_por_dia(dia)

    # ======================================================
    # RELATÓRIOS
    # ======================================================
    def dados_relatorio(self, mes, ano, tipo="Todos", categoria="Todos"):
        mes = int(mes)
        ano = int(ano)

        dt_ini = datetime(ano, mes, 1)
        if mes == 12:
            dt_fim = datetime(ano + 1, 1, 1) - timedelta(seconds=1)
        else:
            dt_fim = datetime(ano, mes + 1, 1) - timedelta(seconds=1)

        vendas = self.vendas_repo.listar_vendas(
            tipo=None,
            data_inicial=dt_ini,
            data_final=dt_fim,
            incluir_itens=True,
        )

        vendas_filtradas = []
        faturamento = Decimal("0")
        qtd_vendas = 0
        serie_por_dia: Dict[int, Decimal] = {}
        produtos_vendidos: Dict[str, int] = {}
        taxas_entrega = Decimal("0")

        for v in vendas:
            if tipo != "Todos":
                tipo_map = {"Balcão": "BALCAO", "Revenda": "REVENDA", "Serviços": "DELIVERY"}
                tipo_real = tipo_map.get(tipo, None)
                if tipo_real and v["tipo"] != tipo_real:
                    continue

            valor_considerado = Decimal("0")
            itens_considerados = []

            for item in v.get("itens", []):
                if categoria != "Todos" and item.get("categoria") != categoria:
                    continue

                valor_considerado += self._to_decimal(item.get("total", 0))
                itens_considerados.append(item)

                nome_prod = item.get("produto_nome") or item.get("nome") or ""
                produtos_vendidos[nome_prod] = produtos_vendidos.get(nome_prod, 0) + int(item.get("qtd", 0))

            if categoria != "Todos" and not itens_considerados:
                continue

            if categoria == "Todos":
                valor_considerado = self._to_decimal(v.get("total", 0))
                taxas_entrega += self._to_decimal(v.get("taxa_entrega", 0))

            vendas_filtradas.append(v)
            faturamento += valor_considerado
            qtd_vendas += 1

            dia = v["data"].day if isinstance(v["data"], datetime) else self._parse_datetime(v["data"]).day
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