# Dashboard Orçamentário — Marketing (Dorel Juvenile Brasil)

Vitrine estática dos dados de Forecast x Actual de Marketing (2024–2026), com filtros múltiplos.
Snapshot — não conecta na base viva. Pra atualizar, troque o CSV e faça novo deploy.

## O que tem aqui

- `app.py` — o app.
- `requirements.txt` — dependências.
- `data/base.csv` — snapshot dos dados (exportado da aba "Base Consolidada" do Excel).

## Deploy — passo a passo (primeira vez)

### 1. Criar o repositório no GitHub

1. Acesse github.com, clique em **New repository**.
2. Nome sugerido: `dashboard-mkt-dorel` (pode ser privado ou público — Streamlit Cloud funciona com os dois, privado exige conectar sua conta).
3. Não marque nenhuma opção extra (sem README, sem .gitignore) — repositório vazio mesmo.
4. Clique em **Create repository**.

### 2. Subir os arquivos

Na página do repositório recém-criado, tem um botão **"uploading an existing file"** (ou "Add file" → "Upload files").

1. Arraste os 3 itens desta pasta: `app.py`, `requirements.txt`, e a pasta `data` (com o `base.csv` dentro).
2. Escreva qualquer mensagem de commit (ex. "primeira versão").
3. Clique em **Commit changes**.

### 3. Conectar no Streamlit Cloud

1. Acesse share.streamlit.io (você já criou a conta).
2. Clique em **New app** (ou "Create app").
3. Escolha **"Deploy a public app from GitHub"** (ou o equivalente).
4. Autorize o Streamlit a acessar sua conta GitHub, se pedir.
5. Selecione o repositório `dashboard-mkt-dorel`, branch `main`, arquivo principal `app.py`.
6. Clique em **Deploy**.

Leva 1–3 minutos pra subir. Depois disso, você recebe uma URL fixa tipo:
`https://dashboard-mkt-dorel.streamlit.app`

Esse é o link que você manda pra ela. Ela abre no navegador (celular ou desktop), filtra e mexe livremente.

## Como atualizar os dados depois (se precisar)

1. No Excel, exporte a aba "Base Consolidada" como CSV (mesmo processo de antes).
2. No GitHub, vá até `data/base.csv`, clique em editar (ícone de lápis) ou delete e suba o novo.
3. O Streamlit Cloud redetecta a mudança e atualiza o app sozinho em ~1 minuto — sem precisar reconfigurar nada.

## Se algo der errado

- Tela de erro no deploy geralmente é falta de algum arquivo (confira se `data/base.csv` foi mesmo enviado, incluindo a pasta).
- Se o app "dormir" por inatividade (Streamlit Cloud grátis hiberna apps sem uso), é só abrir o link de novo e esperar ~30 segundos — ele acorda sozinho.
