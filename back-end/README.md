# FIFA League App — Backend (FastAPI)

API em **FastAPI** (assíncrona) que se conecta ao **PostgreSQL do Supabase**,
pronta para rodar com **Docker**. O schema do banco está em
[`database/Database-Schema.sql`](database/Database-Schema.sql).

## Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy 2.0** (async) + **asyncpg**
- **Pydantic v2** / **pydantic-settings** (configuração via `.env`)
- **Supabase Auth** (Admin API via secret key, no back-end)
- **Docker** / **docker-compose**

## Arquitetura em camadas

A API é separada em camadas com responsabilidades bem definidas, e o fluxo de
uma requisição é sempre no mesmo sentido:

```
HTTP → Rota (endpoint) → Serviço (regras) → Repositório (dados) → Banco
```

- **Rota** (`api/v1/endpoints`): só lida com HTTP — recebe o request, chama o
  serviço e devolve a resposta. Não contém regra de negócio.
- **Serviço** (`services`): regras de negócio e validações (ex.: impedir email
  duplicado). Lança **erros de domínio** (`core/exceptions.py`), sem conhecer HTTP.
- **Repositório** (`repositories`): acesso a dados — só fala com o banco e lida
  apenas com modelos ORM.
- **Conexão** (`core/database.py`): engine/sessão assíncrona (infraestrutura).

Os **erros de domínio** são convertidos em respostas HTTP por *exception
handlers* registrados no `main.py` (ex.: `NotFoundError` → 404,
`ConflictError` → 409), mantendo as rotas finas.

## Estrutura do projeto

```
.
├── app/
│   ├── main.py                 # App factory: CORS, routers, lifespan, error handlers
│   ├── core/
│   │   ├── config.py           # Settings (lidas do .env)
│   │   ├── database.py         # Engine async, sessão e dependência get_db
│   │   ├── supabase.py         # Client Admin (secret key) para Auth
│   │   └── exceptions.py       # Erros de domínio (NotFound, Conflict, Auth, ...)
│   ├── models/                 # Modelos ORM (SQLAlchemy)
│   │   ├── base.py
│   │   └── user.py             # Mapeado à tabela "User" do Supabase
│   ├── schemas/                # Schemas Pydantic (entrada/saída)
│   │   ├── auth.py             # RegisterRequest (email, password, name)
│   │   └── user.py
│   ├── repositories/           # Camada de dados (acesso ao banco)
│   │   └── user.py
│   ├── services/               # Camada de negócio (regras/validações)
│   │   └── auth.py             # Cadastro: Auth + vínculo no User pré-cadastrado
│   └── api/
│       ├── deps.py             # Injeção de dependências (sessão, repo, serviço)
│       └── v1/
│           ├── router.py       # Agrega os routers da v1
│           └── endpoints/
│               ├── auth.py     # POST /auth/register, /login, /refresh, /logout
│               └── health.py   # /health, /health/db
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

> O cadastro exige um **User pré-cadastrado** na tabela (email autorizado,
> `authUserId` vazio). O endpoint `/api/v1/auth/register` cria o Auth e vincula
> o `authUserId`. Modelo, repositório e schema `UserRead` permanecem para
> persistir/retornar o perfil. Para as demais tabelas (`Player`, `Team`,
> `Match`, ...), basta replicar o mesmo padrão em cada camada.

## Configuração

1. Copie o `.env.example` para `.env` e preencha as variáveis:

```bash
cp .env.example .env
```

2. Pegue a connection string no Supabase em **Project Settings → Database** e
   troque o prefixo para `postgresql+asyncpg://`.

- **Conexão direta** (porta 5432):
  ```
  DATABASE_URL=postgresql+asyncpg://postgres:SENHA@db.SEU_REF.supabase.co:5432/postgres
  ```
- **Pooler transacional** (porta 6543, recomendado para muitas conexões).
  Requer `DB_STATEMENT_CACHE_SIZE=0` (já é o padrão):
  ```
  DATABASE_URL=postgresql+asyncpg://postgres.SEU_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:6543/postgres
  ```

3. Em **Project Settings → API Keys**, preencha:
   - `SUPABASE_URL` — Project URL
   - `SUPABASE_SECRET_KEY` — secret key `sb_secret_...` (**só no back-end**)

4. Em **Authentication → Providers → Email**, deixe **Confirm email** habilitado
   para o cadastro exigir confirmação antes do login.

## Como rodar

### Com Docker (recomendado)

```bash
docker compose up --build
```

### Localmente (sem Docker)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`.

## Endpoints úteis

- `GET /` — informações da API
- `GET /docs` — Swagger UI (documentação interativa)
- `GET /api/v1/health` — liveness
- `GET /api/v1/health/db` — testa a conexão com o Supabase
- `POST /api/v1/auth/register` — ativa Auth para User pré-cadastrado; body: `email`, `password`, `name`
- `POST /api/v1/auth/login` — login; body: `email`, `password`; resposta: `accessToken`, `refreshToken`, `isAdmin`, `name`, `coachName`
- `POST /api/v1/auth/refresh` — renova tokens; body: `refreshToken`; resposta: `accessToken`, `refreshToken`
- `POST /api/v1/auth/logout` — encerra sessão; header: `Authorization: Bearer <accessToken>`

### Cadastro (`POST /api/v1/auth/register`)

Pré-requisito: o email já deve existir na tabela **`User`** com `authUserId`
nulo (você cadastra o convidado antes no banco).

1. Confere se o email existe e se `authUserId` está vazio.
2. Cria o usuário no **Supabase Auth** (`email_confirm=false`).
3. Dispara o email de confirmação.
4. Atualiza o **`User`** com o `authUserId` (e o `name` enviado).
5. Retorna `201` com os dados do User (sem senha e sem tokens).

Email não autorizado → `404`. Email já com conta ativa → `409`.
Até confirmar o email, o login permanece bloqueado pelo Auth. A senha fica
somente no Auth, nunca na tabela `User`.

### Login (`POST /api/v1/auth/login`)

1. Autentica email/senha no **Supabase Auth**.
2. Busca o registro correspondente na tabela **`User`** pelo `authUserId`.
3. Em sucesso, retorna `{ "accessToken": "...", "refreshToken": "...", "isAdmin": false, "name": "...", "coachName": "..." }`.

Nas rotas protegidas, o front envia `Authorization: Bearer <accessToken>`. A
dependência `CurrentUserDep` valida o JWT no Supabase Auth e confere se o
`authUserId` existe na tabela `User`.

Se as credenciais forem inválidas (ou o email ainda não estiver confirmado),
responde `401`. Se o Auth autenticar mas não houver linha na `User`, responde
`404`.

### Refresh (`POST /api/v1/auth/refresh`)

1. Recebe o `refreshToken` do login (ou do refresh anterior).
2. Troca no Supabase Auth por um **novo** par `accessToken` + `refreshToken`.
3. Confere se o usuário ainda existe na tabela `User`.

O refresh token é de **uso único**: guarde sempre o novo `refreshToken` retornado.
Refresh token inválido/expirado → `401`. Usuário ausente na `User` → `401`.

### Logout (`POST /api/v1/auth/logout`)

1. Front envia `Authorization: Bearer <accessToken>`.
2. A API revoga a sessão atual no Supabase Auth (`scope=local`).
3. Responde `204`. O front apaga `accessToken` e `refreshToken` do storage.

Obs.: o access token JWT pode continuar aceito até o `exp`; por isso limpar no
front é obrigatório. Sem o refresh token, a sessão não renova mais.

## Notas sobre o Supabase

- **SSL** é obrigatório e já vem habilitado (`DB_USE_SSL=true`).
- No **pooler transacional** (PgBouncer, porta 6543), *prepared statements* não
  são suportados; por isso `DB_STATEMENT_CACHE_SIZE=0`.
- Os nomes de tabela/coluna no banco usam PascalCase/camelCase (ex.: `"User"`,
  `"authUserId"`). Os modelos ORM já fazem esse mapeamento para snake_case.
- O schema é gerenciado pelo SQL em `database/` (aplicado no Supabase), então a
  API **não** cria tabelas no startup.
- A **secret key** (`sb_secret_...`) bypassa RLS e tem poder total no Auth —
  nunca a coloque no front-end nem em repositório público.
