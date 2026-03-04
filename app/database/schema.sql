-- app/database/schema.sql

-- ============================================================
-- SCHEMA INICIAL DO GELADOCE (revisado)
-- ============================================================
-- Estrutura base do banco, compatível com o código atual
-- e preparada para crescer com repositórios.
--
-- Melhorias incluídas:
-- - Índices e UNIQUEs definidos dentro das tabelas (mais seguro reexecutar)
-- - clientes: email NULL, atualizado_em com ON UPDATE, unique cpf_cnpj
-- - fornecedores: atualizado_em com ON UPDATE (e índices)
-- - funcionarios: ADICIONADO atualizado_em com ON UPDATE (e índices)
-- - vendas: campo status + índices
-- - índices para relatórios e buscas
-- ============================================================

-- (Opcional) garante charset/colation em sessão
-- SET NAMES utf8mb4;
-- SET collation_connection = 'utf8mb4_unicode_ci';

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
    KEY idx_funcionarios_tipo_acesso (tipo_acesso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


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


CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    categoria ENUM('Sorvete', 'Picolé', 'Açaí', 'Outros') NOT NULL DEFAULT 'Outros',
    preco DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    ativo TINYINT(1) NOT NULL DEFAULT 1,

    -- Mantidos os dois campos (tipo_item + eh_insumo) por compatibilidade com seu código atual.
    tipo_item ENUM('Produto', 'Insumo') NOT NULL DEFAULT 'Produto',
    eh_insumo TINYINT(1) NOT NULL DEFAULT 0,

    KEY idx_produtos_nome (nome),
    KEY idx_produtos_categoria (categoria),
    KEY idx_produtos_ativo (ativo),
    KEY idx_produtos_tipo_item (tipo_item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS estoque (
    produto_id INT PRIMARY KEY,
    quantidade INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_estoque_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS vendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('BALCAO', 'REVENDA', 'DELIVERY') NOT NULL,
    status ENUM('ABERTA', 'FINALIZADA', 'CANCELADA') NOT NULL DEFAULT 'FINALIZADA',
    data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cliente_id INT NULL,
    revendedor_id INT NULL,
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
    KEY idx_vendas_forma_pagamento (forma_pagamento),

    CONSTRAINT fk_venda_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_venda_revendedor
        FOREIGN KEY (revendedor_id) REFERENCES clientes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS venda_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venda_id INT NOT NULL,
    produto_id INT NOT NULL,
    produto_nome VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    qtd INT NOT NULL,
    unitario DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    KEY idx_venda_itens_venda_id (venda_id),
    KEY idx_venda_itens_produto_id (produto_id),
    KEY idx_venda_itens_categoria (categoria),

    CONSTRAINT fk_venda_itens_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_venda_itens_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS mov_fidelidade (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    acao ENUM('ADICIONAR', 'REMOVER', 'RESGATAR', 'BONUS', 'ZERAR') NOT NULL,
    pontos INT NOT NULL DEFAULT 0,
    motivo VARCHAR(255) NOT NULL,
    venda_id INT NULL,
    data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_mov_fidelidade_cliente_id (cliente_id),
    KEY idx_mov_fidelidade_venda_id (venda_id),
    KEY idx_mov_fidelidade_data (data),

    CONSTRAINT fk_mov_fidelidade_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_mov_fidelidade_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS agendamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data DATE NOT NULL,
    inicio VARCHAR(5) NOT NULL,
    fim VARCHAR(5) NOT NULL,
    inicio_min INT NOT NULL,
    fim_min INT NOT NULL,
    carrinho_id INT NOT NULL,
    motorista_id INT NOT NULL,
    local VARCHAR(180) NOT NULL,
    status ENUM('Agendado', 'Confirmado', 'Cancelado') NOT NULL DEFAULT 'Agendado',
    obs TEXT NULL,
    cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_agendamentos_data (data),
    KEY idx_agendamentos_carrinho_id (carrinho_id),
    KEY idx_agendamentos_motorista_id (motorista_id),
    KEY idx_agendamentos_status (status),

    CONSTRAINT fk_agendamento_carrinho
        FOREIGN KEY (carrinho_id) REFERENCES carrinhos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_agendamento_funcionario
        FOREIGN KEY (motorista_id) REFERENCES funcionarios(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS fechamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    vendas_brutas DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    descontos DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    cancelamentos DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_liquido DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    dinheiro DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    pix DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    cartao DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_recebido DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    sangria DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    caixa_inicial DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    contado_caixa DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    previsto_em_caixa DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    diferenca DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    observacao TEXT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    KEY idx_fechamentos_data (data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;