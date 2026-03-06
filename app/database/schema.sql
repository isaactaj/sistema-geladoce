-- app/database/schema.sql
-- ============================================================
-- SCHEMA GELADOCE (FULL - RECRIAR BANCO)
-- Charset padrão: utf8mb4
-- Engine padrão: InnoDB (FKs)
-- ============================================================

-- (Opcional) garante charset/colation em sessão
-- SET NAMES utf8mb4;

-- =========================
-- 1) CLIENTES
-- =========================
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    cpf_cnpj VARCHAR(20) NOT NULL,
    telefone VARCHAR(30) NOT NULL,
    email VARCHAR(150) NULL,
    tipo_cliente ENUM('Varejo', 'Revendedor') NOT NULL DEFAULT 'Varejo',
    status ENUM('Ativo', 'Inativo') NOT NULL DEFAULT 'Ativo',
    pontos_atuais INT NOT NULL DEFAULT 0,
    total_acumulado INT NOT NULL DEFAULT 0,
    ultima_compra DATETIME NULL,
    cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_clientes_cpf_cnpj (cpf_cnpj),
    KEY idx_clientes_nome (nome),
    KEY idx_clientes_status (status),
    KEY idx_clientes_telefone (telefone),
    KEY idx_clientes_email (email),
    KEY idx_clientes_tipo_cliente (tipo_cliente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 2) FORNECEDORES
-- =========================
CREATE TABLE IF NOT EXISTS fornecedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    razao VARCHAR(180) NOT NULL,
    cnpj VARCHAR(14) NOT NULL,
    telefone VARCHAR(30) NOT NULL,
    observacoes TEXT NULL,
    cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_fornecedores_cnpj (cnpj),
    KEY idx_fornecedores_razao (razao),
    KEY idx_fornecedores_telefone (telefone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 3) FUNCIONÁRIOS
-- =========================
CREATE TABLE IF NOT EXISTS funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    telefone VARCHAR(30) NOT NULL,
    cargo VARCHAR(100) DEFAULT '',
    tipo_acesso ENUM('Colaborador', 'Administrador') NOT NULL DEFAULT 'Colaborador',
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_funcionarios_cpf (cpf),
    KEY idx_funcionarios_nome (nome),
    KEY idx_funcionarios_ativo (ativo),
    KEY idx_funcionarios_tipo_acesso (tipo_acesso),
    KEY idx_funcionarios_cargo (cargo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 4) USUÁRIOS (LOGIN)
--  - FK por CPF conforme requisito
-- =========================
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    login VARCHAR(60) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    tipo_acesso ENUM('Colaborador', 'Administrador') NOT NULL DEFAULT 'Colaborador',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_usuarios_login (login),
    UNIQUE KEY uk_usuarios_cpf (cpf),
    KEY idx_usuarios_tipo_acesso (tipo_acesso),

    CONSTRAINT fk_usuarios_funcionario_cpf
        FOREIGN KEY (cpf) REFERENCES funcionarios(cpf)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 5) CARRINHOS
-- =========================
CREATE TABLE IF NOT EXISTS carrinhos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_externo VARCHAR(30) NOT NULL,
    nome VARCHAR(120) NOT NULL,
    capacidade INT NOT NULL DEFAULT 0,
    status ENUM('Disponível', 'Em rota', 'Manutenção') NOT NULL DEFAULT 'Disponível',
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_carrinhos_id_externo (id_externo),
    KEY idx_carrinhos_nome (nome),
    KEY idx_carrinhos_status (status),
    KEY idx_carrinhos_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 6) PRODUTOS
-- =========================
CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    categoria ENUM('Sorvete', 'Picolé', 'Açaí', 'Outros') NOT NULL DEFAULT 'Outros',
    preco DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    ativo TINYINT(1) NOT NULL DEFAULT 1,

    tipo_item ENUM('Produto', 'Insumo') NOT NULL DEFAULT 'Produto',
    eh_insumo TINYINT(1) NOT NULL DEFAULT 0,

    fornecedor_id INT NULL,

    KEY idx_produtos_nome (nome),
    KEY idx_produtos_categoria (categoria),
    KEY idx_produtos_ativo (ativo),
    KEY idx_produtos_tipo_item (tipo_item),
    KEY idx_produtos_fornecedor_id (fornecedor_id),

    CONSTRAINT fk_produtos_fornecedor
        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 7) ESTOQUE
-- =========================
CREATE TABLE IF NOT EXISTS estoque (
    produto_id INT PRIMARY KEY,
    quantidade INT NOT NULL DEFAULT 0,

    CONSTRAINT fk_estoque_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 8) FORMAS DE PAGAMENTO
-- =========================
CREATE TABLE IF NOT EXISTS formas_pagamento (
    codigo VARCHAR(30) PRIMARY KEY,
    descricao VARCHAR(80) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO formas_pagamento (codigo, descricao) VALUES
('Dinheiro', 'Pagamento em dinheiro'),
('Pix', 'Pagamento via PIX'),
('Cartão', 'Pagamento via cartão (com acento)'),
('Cartao', 'Pagamento via cartão (sem acento)'),
('Prazo', 'Pagamento a prazo')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);


-- =========================
-- 9) FECHAMENTOS
-- =========================
CREATE TABLE IF NOT EXISTS fechamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data DATE NOT NULL,

    caixa_inicial DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    sangria DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    contado_caixa DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    observacao TEXT NULL,
    responsavel_id INT NULL,

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_fechamentos_data (data),
    KEY idx_fechamentos_data (data),
    KEY idx_fechamentos_responsavel (responsavel_id),

    CONSTRAINT fk_fechamentos_responsavel
        FOREIGN KEY (responsavel_id) REFERENCES funcionarios(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 10) VENDAS
-- =========================
CREATE TABLE IF NOT EXISTS vendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('BALCAO', 'REVENDA', 'DELIVERY') NOT NULL,
    status ENUM('ABERTA', 'FINALIZADA', 'CANCELADA') NOT NULL DEFAULT 'FINALIZADA',
    data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    cliente_id INT NULL,
    revendedor_id INT NULL,

    fechamento_id INT NULL,

    forma_pagamento VARCHAR(30) NOT NULL,
    observacao TEXT NULL,

    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    desconto DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    taxa_entrega DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    KEY idx_vendas_data (data),
    KEY idx_vendas_tipo (tipo),
    KEY idx_vendas_status (status),
    KEY idx_vendas_cliente_id (cliente_id),
    KEY idx_vendas_revendedor_id (revendedor_id),
    KEY idx_vendas_fechamento_id (fechamento_id),
    KEY idx_vendas_forma_pagamento (forma_pagamento),

    CONSTRAINT fk_venda_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_venda_revendedor
        FOREIGN KEY (revendedor_id) REFERENCES clientes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_venda_fechamento
        FOREIGN KEY (fechamento_id) REFERENCES fechamentos(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_venda_forma_pagamento
        FOREIGN KEY (forma_pagamento) REFERENCES formas_pagamento(codigo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 11) ITENS DA VENDA
-- =========================
CREATE TABLE IF NOT EXISTS vendas_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venda_id INT NOT NULL,
    produto_id INT NOT NULL,

    qtd INT NOT NULL,
    unitario DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    KEY idx_vendas_itens_venda_id (venda_id),
    KEY idx_vendas_itens_produto_id (produto_id),

    CONSTRAINT fk_vendas_itens_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_vendas_itens_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 12) MOVIMENTAÇÕES DE FIDELIDADE
-- =========================
CREATE TABLE IF NOT EXISTS mov_fidelidade (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    acao ENUM('ADICIONAR', 'REMOVER', 'RESGATAR', 'BONUS', 'ZERAR') NOT NULL,
    pontos INT NOT NULL DEFAULT 0,
    motivo VARCHAR(255) NOT NULL,
    venda_id INT NULL,
    usuario_id INT NULL,
    data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_mov_fidelidade_cliente_id (cliente_id),
    KEY idx_mov_fidelidade_venda_id (venda_id),
    KEY idx_mov_fidelidade_usuario_id (usuario_id),
    KEY idx_mov_fidelidade_data (data),

    CONSTRAINT fk_mov_fidelidade_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_mov_fidelidade_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_mov_fidelidade_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 13) AGENDAMENTOS (com quantidade + opcionais)
-- =========================
CREATE TABLE IF NOT EXISTS agendamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data DATE NOT NULL,
    inicio VARCHAR(5) NOT NULL,
    fim VARCHAR(5) NOT NULL,
    inicio_min INT NOT NULL,
    fim_min INT NOT NULL,

    quantidade_carrinhos INT NOT NULL DEFAULT 1,
    carrinho_preferido_id INT NULL,
    motorista_id INT NULL,

    local VARCHAR(180) NOT NULL,
    status ENUM('Agendado', 'Confirmado', 'Cancelado') NOT NULL DEFAULT 'Agendado',
    obs TEXT NULL,
    cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_agendamentos_data (data),
    KEY idx_agendamentos_status (status),
    KEY idx_agendamentos_carrinho_pref (carrinho_preferido_id),
    KEY idx_agendamentos_motorista (motorista_id),

    CONSTRAINT fk_agendamento_carrinho_pref
        FOREIGN KEY (carrinho_preferido_id) REFERENCES carrinhos(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_agendamento_motorista
        FOREIGN KEY (motorista_id) REFERENCES funcionarios(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 14) DELIVERY (persistência real)
-- =========================
CREATE TABLE IF NOT EXISTS delivery_pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,

    data DATE NOT NULL,
    prev_saida VARCHAR(5) NOT NULL DEFAULT '00:30',

    cliente_nome VARCHAR(150) NOT NULL,
    cliente_telefone VARCHAR(30) NOT NULL,
    cliente_id INT NULL,

    end_rua VARCHAR(180) NOT NULL,
    end_num VARCHAR(30) NULL,
    end_bairro VARCHAR(120) NOT NULL,
    end_cidade VARCHAR(120) NOT NULL DEFAULT 'Belém',
    end_comp VARCHAR(180) NULL,

    entregador_id INT NULL,

    pagamento VARCHAR(30) NOT NULL,
    status ENUM('Pendente','Em preparo','Em rota','Entregue','Cancelado') NOT NULL DEFAULT 'Pendente',

    taxa_entrega DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    venda_id INT NULL,
    obs TEXT NULL,

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    KEY idx_delivery_data (data),
    KEY idx_delivery_status (status),
    KEY idx_delivery_entregador (entregador_id),
    KEY idx_delivery_venda (venda_id),
    KEY idx_delivery_cliente_tel (cliente_telefone),

    CONSTRAINT fk_delivery_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_entregador
        FOREIGN KEY (entregador_id) REFERENCES funcionarios(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_pagamento
        FOREIGN KEY (pagamento) REFERENCES formas_pagamento(codigo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS delivery_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    produto_id INT NOT NULL,

    qtd INT NOT NULL,
    unitario DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    KEY idx_delivery_itens_pedido (pedido_id),
    KEY idx_delivery_itens_produto (produto_id),

    CONSTRAINT fk_delivery_itens_pedido
        FOREIGN KEY (pedido_id) REFERENCES delivery_pedidos(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_itens_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 15) DELIVERY: PEDIDOS
-- =========================
CREATE TABLE IF NOT EXISTS delivery_pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,

    data DATE NOT NULL,
    prev_saida VARCHAR(5) NULL,

    -- opcional: se você quiser vincular ao cliente cadastrado
    cliente_id INT NULL,

    -- snapshot (sempre salva, mesmo sem cliente_id)
    cliente_nome VARCHAR(150) NOT NULL,
    cliente_telefone VARCHAR(30) NOT NULL,

    -- endereço (snapshot)
    end_rua VARCHAR(180) NOT NULL,
    end_num VARCHAR(20) NULL,
    end_bairro VARCHAR(120) NOT NULL,
    end_cidade VARCHAR(120) NOT NULL DEFAULT 'Belém',
    end_comp VARCHAR(180) NULL,

    entregador_id INT NULL,

    forma_pagamento VARCHAR(30) NOT NULL,
    status ENUM('Pendente', 'Em preparo', 'Em rota', 'Entregue', 'Cancelado') NOT NULL DEFAULT 'Pendente',

    taxa_entrega DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    obs TEXT NULL,

    -- quando o status gera venda, vinculamos aqui
    venda_id INT NULL,

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    KEY idx_delivery_data (data),
    KEY idx_delivery_status (status),
    KEY idx_delivery_entregador (entregador_id),
    KEY idx_delivery_cliente (cliente_id),
    KEY idx_delivery_venda (venda_id),

    CONSTRAINT fk_delivery_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_entregador
        FOREIGN KEY (entregador_id) REFERENCES funcionarios(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_forma_pag
        FOREIGN KEY (forma_pagamento) REFERENCES formas_pagamento(codigo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================
-- 16) DELIVERY: ITENS
-- =========================
CREATE TABLE IF NOT EXISTS delivery_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    produto_id INT NOT NULL,

    qtd INT NOT NULL,
    unitario DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    KEY idx_delivery_itens_pedido (pedido_id),
    KEY idx_delivery_itens_produto (produto_id),

    CONSTRAINT fk_delivery_itens_pedido
        FOREIGN KEY (pedido_id) REFERENCES delivery_pedidos(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_delivery_itens_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 1) VIEW: RESUMO DE FECHAMENTO
-- =========================
CREATE OR REPLACE VIEW vw_fechamentos_resumo AS
SELECT
    f.id AS fechamento_id,
    f.data AS data_fechamento,

    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' THEN v.subtotal ELSE 0 END), 0) AS vendas_brutas,
    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' THEN v.desconto ELSE 0 END), 0) AS descontos,
    COALESCE(SUM(CASE WHEN v.status = 'CANCELADA' THEN v.total ELSE 0 END), 0) AS cancelamentos,
    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' THEN v.total ELSE 0 END), 0) AS total_liquido,

    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' AND v.forma_pagamento = 'Dinheiro' THEN v.total ELSE 0 END), 0) AS dinheiro,
    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' AND v.forma_pagamento = 'Pix' THEN v.total ELSE 0 END), 0) AS pix,
    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' AND v.forma_pagamento IN ('Cartão','Cartao') THEN v.total ELSE 0 END), 0) AS cartao,
    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' AND v.forma_pagamento = 'Prazo' THEN v.total ELSE 0 END), 0) AS prazo,

    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' THEN v.total ELSE 0 END), 0) AS total_recebido,

    (f.caixa_inicial
        + COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' AND v.forma_pagamento = 'Dinheiro' THEN v.total ELSE 0 END), 0)
        - f.sangria
    ) AS previsto_em_caixa,

    (f.contado_caixa
        - (f.caixa_inicial
            + COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' AND v.forma_pagamento = 'Dinheiro' THEN v.total ELSE 0 END), 0)
            - f.sangria
          )
    ) AS diferenca,

    COALESCE(SUM(CASE WHEN v.status <> 'CANCELADA' THEN 1 ELSE 0 END), 0) AS qtd_vendas

FROM fechamentos f
LEFT JOIN vendas v
    ON (
        v.fechamento_id = f.id
        OR (v.fechamento_id IS NULL AND DATE(v.data) = f.data)
    )
GROUP BY f.id, f.data, f.caixa_inicial, f.sangria, f.contado_caixa;