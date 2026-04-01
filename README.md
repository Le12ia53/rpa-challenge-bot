## Visão Geral

Este projeto implementa um bot de automação capaz de resolver os três níveis do RPA Challenge:

* Easy — autenticação simples via API
* Hard — autenticação com mTLS e challenge dinâmico
* Extreme — fluxo assíncrono multi-step com WebSocket, Proof-of-Work e criptografia

O objetivo é demonstrar:

* Capacidade de engenharia reversa de aplicações web
* Automação resiliente em ambientes com múltiplas camadas de segurança
* Integração com protocolos REST e WebSocket
* Aplicação de conceitos de segurança (mTLS, criptografia, proof-of-work)

---

## Arquitetura da Solução

```bash
rpa-challenge-bot/
│
├── challenges/
│   ├── easy.py
│   ├── hard.py
│   └── extreme.py
│
├── utils/
│   ├── timer.py
│   └── tls.py
│
├── config.py
├── main.py
├── requirements.txt
└── README.md
```

---

## Tecnologias Utilizadas

* Python 3.10+
* Playwright (automação de browser)
* Requests (cliente HTTP)
* websocket-client (comunicação WebSocket)
* OpenSSL / Cryptography (mTLS e criptografia)
* Hashlib (Proof-of-Work com SHA256)

---

## Como Executar

### 1. Subir o ambiente do desafio

```bash
docker pull doc9cloud/rpa-challenge:latest

docker run -d -p 3000:3000 -p 3001:3001 \
  --name rpa-challenge \
  doc9cloud/rpa-challenge:latest
```

Acesso:
https://localhost:3000

---

### 2. Extrair certificado (nível Hard)

```bash
docker cp rpa-challenge:/app/certs/client.pfx ./certs/client.pfx
docker cp rpa-challenge:/app/certs/ca.crt ./certs/ca.crt
```

Senha do certificado:
test123

---

### 3. Criar ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

---

### 4. Instalar dependências

```bash
pip install -r requirements.txt
pip install websocket-client
```

---

### 5. Executar os desafios

```bash
python main.py --level easy
python main.py --level hard
python main.py --level extreme
```

---

## Credenciais Utilizadas

| Nível   | Usuário  | Senha           |
| ------- | -------- | --------------- |
| Easy    | admin    | rpa@2026!       |
| Hard    | operator | cert#Secure2026 |
| Extreme | root     | h4ck3r@Pr00f!   |

---

## Estratégia por Nível

### Easy

* Extração de formulário HTML
* Identificação do endpoint de autenticação
* Envio de payload JSON
* Captura do token de resposta

---

### Hard

* Extração do challenge dinâmico (hash SHA256)
* Geração de payload com timestamp e nonce
* Autenticação via mTLS utilizando certificado cliente
* Validação em endpoint seguro

---

### Extreme

Fluxo completo:

1. Inicialização da sessão
2. Conexão com WebSocket
3. Resolução de Proof-of-Work
4. Verificação de token intermediário
5. Decriptação de payload (AES-256-CBC)
6. Geração de OTP
7. Finalização da autenticação

---

## Resultados

| Nível   | Status | Tempo Médio |
| ------- | ------ | ----------- |
| Easy    | OK     | ~30 ms      |
| Hard    | OK     | ~7 s        |
| Extreme | OK     | ~8–18 s     |

---

## Diferenciais Técnicos

* Engenharia reversa de fluxo assíncrono
* Implementação de autenticação mTLS
* Resolução de Proof-of-Work com otimização
* Interceptação de requisições HTTP e WebSocket
* Orquestração híbrida entre browser e API
* Tratamento de certificados autoassinados

---

## Observabilidade

O sistema registra:

* Requisições HTTP
* Respostas da aplicação
* Frames de WebSocket
* Tokens intermediários
* Payloads criptografados

---

## Possíveis Melhorias

* Paralelização do Proof-of-Work
* Implementação completa sem dependência de browser
* Decriptação manual do payload criptografado
* Estratégias de retry com backoff exponencial
* Monitoramento com ferramentas de observabilidade

---

## Autor

Vanderleia Matos
Especialista em AI, automação e engenharia de sistemas

---

## Licença

Uso educacional e técnico
