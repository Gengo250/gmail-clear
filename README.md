# Gmail Cleaner (Projeto Pessoal)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](#requisitos)
[![Google API](https://img.shields.io/badge/Google%20API-Gmail%20API-red.svg)](#google-cloud--gmail-api)
[![OAuth 2.0](https://img.shields.io/badge/Auth-OAuth%202.0-brightgreen.svg)](#autentica%C3%A7%C3%A3o-oauth-20)

Automação **estritamente pessoal** para ajudar a manter a caixa do Gmail organizada, aplicando **regras configuráveis** para mover emails (ex.: LinkedIn, Duolingo, SPAM antigo) para a **Lixeira (TRASH)** usando a **Gmail API**.

> **Nota:** Este projeto foi pensado para uso individual. Não publique `credentials.json` nem `token.json`.

---

## Sumário

- [Motivação](#motiva%C3%A7%C3%A3o)
- [O que o projeto faz](#o-que-o-projeto-faz)
- [Principais recursos](#principais-recursos)
- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Google Cloud + Gmail API](#google-cloud--gmail-api)
- [Instalação](#instala%C3%A7%C3%A3o)
- [Configuração das regras](#configura%C3%A7%C3%A3o-das-regras)
- [Como usar](#como-usar)
- [Segurança](#seguran%C3%A7a)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Licen](#licen%C3%A7a)

---

## Motivação

Caixas de email tendem a acumular:

- notificações repetitivas (LinkedIn, Duolingo, etc.);
- newsletters e mensagens promocionais;
- SPAM que permanece guardado mais tempo do que deveria.

A limpeza manual é chata, propensa a erro e consome tempo.  
Este projeto automatiza essa rotina com **regras transparentes** e execução segura (primeiro você **simula**, depois **aplica**).

---

## O que o projeto faz

1. Autentica o usuário via **OAuth 2.0 (Desktop App)**.
2. Busca mensagens usando a **mesma sintaxe da barra de busca do Gmail** (Gmail Search Query).
3. Aplica ações por regra:
   - `TRASH`: move para a Lixeira (reversível).
4. Fornece uma CLI simples:
   - `auth` → autenticar e gerar `token.json`
   - `plan` → mostrar o que seria afetado (simulação)
   - `run --apply` → executar de verdade

---

## Principais recursos

- ✅ Regras declarativas em **YAML**
- ✅ **Dry-run** (simulação) antes de aplicar
- ✅ CLI amigável (`gmail-cleaner`)
- ✅ Logs legíveis no terminal (Rich)
- ✅ Re-tentativas com backoff para falhas temporárias (Tenacity)
- ✅ Estrutura modular (camadas separadas: auth, api, regras, CLI)

---

## Arquitetura

Estrutura de pastas (padrão `src/`):

```text
gmail-cleaner/
  config/
    rules.yaml
  src/
    gmail_cleaner/
      __init__.py
      __main__.py
      auth.py         # OAuth 2.0 e token.json
      gmail_api.py    # chamadas Gmail API + retry/backoff
      config.py       # leitura/validação do YAML
      cleaner.py      # planejamento e execução das regras
      cli.py          # interface de linha de comando
      log.py          # setup de logs
  credentials.json    # OAuth client (não versionar)
  token.json          # token do usuário (não versionar)
  requirements.txt
  pyproject.toml
  README.md
```

### Responsabilidades (em alto nível)

- **`auth.py`**: cria/atualiza `token.json` usando OAuth 2.0.
- **`gmail_api.py`**: lista mensagens por query e move para TRASH.
- **`cleaner.py`**: “plano → execução” baseado nas regras.
- **`config.py`**: carrega e valida o `rules.yaml` (Pydantic).
- **`cli.py`**: expõe comandos (`auth`, `plan`, `run`).

---

## Requisitos

- Python **3.10+**
- Conta Google (Gmail)
- Acesso ao **Google Cloud Console**
- Dependências (instaladas via `requirements.txt`):
  - `google-api-python-client`
  - `google-auth-oauthlib`
  - `PyYAML`
  - `pydantic`
  - `rich`
  - `tenacity`

---

## Google Cloud + Gmail API

### 1) Criar um projeto e ativar a Gmail API

No Google Cloud Console:

1. **Criar Project**
2. Ir em **APIs e serviços → Biblioteca**
3. Buscar e ativar **Gmail API**

### 2) Configurar Tela de consentimento OAuth

Em **APIs e serviços → Tela de permissão OAuth**:

- **Tipo de usuário:** **Externo (External)**  
  (necessário para contas `@gmail.com`)
- **Status:** `Testing` é suficiente para uso pessoal
- **Usuários de teste (Test users):** adicione seu email (ex.: `seuemail@gmail.com`)

> Se você ver erro `403 org_internal`, quase sempre é porque o app está como **Internal**.

### 3) Criar credencial OAuth Client (Desktop)

Em **APIs e serviços → Credenciais**:

1. **Criar credenciais → ID do cliente OAuth**
2. Tipo: **Aplicativo para computador (Desktop app)**
3. Baixe o arquivo e salve na raiz do projeto como:

```text
credentials.json
```

---

## Instalação

> Recomendado: ambiente virtual (`venv`).

```bash
# dentro da pasta do projeto
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

---

## Configuração das regras

Edite `config/rules.yaml`.

Exemplo:

```yaml
app:
  user_id: "me"
  credentials_path: "./credentials.json"
  token_path: "./token.json"
  dry_run: true
  page_size: 200

rules:
  - name: "LinkedIn antigo -> Lixo"
    query: "from:linkedin.com older_than:14d -is:starred -is:important"
    action: "TRASH"
    max_results: 2000
    include_spam_trash: false

  - name: "Duolingo antigo -> Lixo"
    query: "from:duolingo.com older_than:14d -is:starred -is:important"
    action: "TRASH"
    max_results: 2000
    include_spam_trash: false

  - name: "Spam velho -> Lixo"
    query: "in:spam older_than:7d"
    action: "TRASH"
    max_results: 5000
    include_spam_trash: true
```

### Campos relevantes

- `query`: sintaxe de busca do Gmail (ex.: `from:`, `older_than:`, `in:spam`, etc.)
- `max_results`: limite de segurança por regra
- `dry_run`: quando `true`, não altera nada (somente planeja)
- `include_spam_trash`: inclui SPAM/Lixeira na busca

---

## Como usar

### 1) Autenticar (primeira execução)

```bash
gmail-cleaner auth
```

- O terminal exibirá uma URL para login/consentimento.
- Após autorizar, o projeto cria `token.json`.

### 2) Planejar (simular)

```bash
gmail-cleaner plan
```

Mostra uma tabela com:
- regra
- ação
- quantidade de mensagens que seriam afetadas

### 3) Executar de verdade

```bash
gmail-cleaner run --apply
```

> Dica: rode o `plan` sempre que ajustar regras.

---

## Segurança

- Não versionar:
  - `credentials.json`
  - `token.json`
- Use `TRASH` como padrão (reversível).
- Evite mover emails importantes adicionando filtros no `query`, por exemplo:
  - `-is:important`
  - `-is:starred`

---

## Troubleshooting

### `403 org_internal` / “Acesso bloqueado”
Causa: app configurado como **Internal** (somente organização Workspace).

Solução:
- mudar para **External**
- adicionar seu email em **Test users** (se estiver em `Testing`)

### `No module named gmail_cleaner`
Causa: pacote não instalado no venv (ou `pip install -e .` faltando).

Solução:

```bash
pip install -e .
```

### Mudou permissões e o token “não acompanha”
Se você alterar escopos/configuração OAuth, recrie o token:

```bash
rm -f token.json
gmail-cleaner auth
```

---

## Roadmap

- Operações em lote (batch) para reduzir tempo em caixas muito grandes
- Relatório por execução (JSON/CSV) com auditoria do que foi movido
- Allowlist (domínios protegidos)
- Agendamento via `systemd timer`/`cron`

---

## Licença

Projeto de uso pessoal. Se você decidir tornar público, revise segurança e documentação antes de publicar.
