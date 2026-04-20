# Guia de Integração do Frontend com API Educa in Tech

**Data:** 20 de Abril de 2026  
**Versão da API:** 1.0.0

---

## 1. Configuração Base

### 1.1 Base URL (Development)

```
http://localhost:8000/api
```

### 1.2 Documentação Automática (Swagger UI)

```
http://localhost:8000/api/docs/
http://localhost:8000/api/schema/
```

Toda a especificação OpenAPI está disponível em `/api/schema/` para gerar tipos TypeScript automaticamente.

---

## 2. Autenticação JWT

Todos os endpoints (exceto `/api/users/token/`) requerem autenticação JWT.

### 2.1 Fluxo de Autenticação

#### **Login (Obter Tokens)**

```http
POST /api/users/token/
Content-Type: application/json

{
  "username": "professor@educa.tech",
  "password": "sua_senha"
}
```

**Resposta (200 OK):**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### **Usar Access Token**

```javascript
fetch("http://localhost:8000/api/turmas/", {
  method: "GET",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
});
```

#### **Renovar Token (Quando Access Expirar)**

```http
POST /api/users/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Resposta (200 OK):**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2.2 Configuração Recomendada (React/Next.js)

```typescript
// services/api.ts
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor para adicionar token em cada requisição
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para renovar token quando expirar
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/users/token/refresh/`, {
            refresh,
          });
          localStorage.setItem("access_token", data.access);
          // Retry original request
          return api(error.config);
        } catch (e) {
          // Refresh falhou, fazer logout
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  },
);

export default api;
```

---

## 3. Endpoints Principais

### 3.1 Endereços (`/api/unidades/`)

**Listar unidades:**

```http
GET /api/unidades/
Authorization: Bearer {access_token}
```

**Resposta (200 OK):**

```json
[
  {
    "id": 1,
    "nome": "Escola Central",
    "localizacao": "São Paulo, SP",
    "created_at": "2026-03-01T10:00:00Z"
  }
]
```

**Criar unidade (Admin/Coordenador):**

```http
POST /api/unidades/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "nome": "Escola Nova",
  "localizacao": "Rio de Janeiro, RJ"
}
```

---

### 3.2 Disciplinas (`/api/disciplinas/`)

**Listar disciplinas:**

```http
GET /api/disciplinas/
Authorization: Bearer {access_token}
```

**Criar disciplina:**

```http
POST /api/disciplinas/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "nome": "Matemática",
  "codigo": "MAT001",
  "descricao": "Disciplina de Matemática"
}
```

---

### 3.3 Turmas (`/api/turmas/`)

**Listar turmas:**

```http
GET /api/turmas/
Authorization: Bearer {access_token}
```

**Filtrar turmas por disciplina:**

```http
GET /api/turmas/?disciplina_id=1
Authorization: Bearer {access_token}
```

**Obter turma específica:**

```http
GET /api/turmas/1/
Authorization: Bearer {access_token}
```

**Resposta:**

```json
{
  "id": 1,
  "nome": "10-A",
  "ano_letivo": 2026,
  "disciplina": {
    "id": 1,
    "nome": "Matemática"
  },
  "unidade": {
    "id": 1,
    "nome": "Escola Central"
  },
  "professor": {
    "id": 5,
    "username": "prof.santos"
  },
  "total_alunos": 25
}
```

**Criar turma:**

```http
POST /api/turmas/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "nome": "10-B",
  "ano_letivo": 2026,
  "disciplina": 1,
  "unidade": 1,
  "professor": 5
}
```

**Transferir aluno entre turmas:**

```http
POST /api/turmas/1/transfer-student/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "aluno_id": 10,
  "nova_turma_id": 2
}
```

---

### 3.4 Alunos (`/api/alunos/`)

**Listar alunos de uma turma:**

```http
GET /api/alunos/?turma_id=1
Authorization: Bearer {access_token}
```

**Criar aluno:**

```http
POST /api/alunos/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "nome": "João Silva",
  "matricula": "MAT2026001",
  "turma": 1
}
```

---

### 3.5 Avaliações (`/api/avaliacoes/`)

**Listar avaliações:**

```http
GET /api/avaliacoes/?turma_id=1
Authorization: Bearer {access_token}
```

**Criar avaliação:**

```http
POST /api/avaliacoes/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "nome": "Prova 1",
  "tipo": "mensal",
  "turma": 1,
  "peso": 1.0,
  "data_aplicacao": "2026-04-15",
  "data_prazo": "2026-04-20"
}
```

**Tipos permitidos:**

- `mensal`
- `trimestral`
- `formativa`
- `oral`

---

### 3.6 Notas (`/api/notas/`)

**Lançar nota:**

```http
POST /api/notas/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "aluno": 10,
  "avaliacao": 5,
  "valor": 8.5
}
```

---

### 3.7 Dashboard de Turma (`/api/core/dashboard/turma/<id>/`)

**Obter dashboard completo da turma:**

```http
GET /api/core/dashboard/turma/1/?dias=30
Authorization: Bearer {access_token}
```

**Parâmetros opcionais:**

- `dias`: Recorte temporal em dias (default: 30)
- `top_k`: Quantidade de documentos RAG para recuperar (default: 8)

**Resposta (200 OK):**

```json
{
  "turma_id": 1,
  "turma_nome": "10-A",
  "media_geral": 7.2,
  "total_alunos": 25,
  "total_avaliacoes": 5,
  "distribuicao_notas": {
    "excelente": 8,
    "bom": 10,
    "satisfatorio": 5,
    "insuficiente": 2
  },
  "cobertura_lancamento": {
    "total": 125,
    "lancadas": 118,
    "percentual": 94.4
  },
  "media_por_tipo_avaliacao": {
    "mensal": 7.5,
    "trimestral": 7.0
  },
  "serie_recente": [
    {
      "data": "2026-04-15",
      "media": 7.3
    }
  ],
  "comparativo_coorte": {
    "media_coorte": 7.0,
    "diferenca": 0.2
  }
}
```

---

### 3.8 Insights com IA (`/api/integrations/llm-rag/dashboard/turma/<id>/insights/`)

**Obter insights pedagógicos com IA:**

```http
POST /api/integrations/llm-rag/dashboard/turma/1/insights/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "pergunta": "Quais são os pontos fracos da turma em Matemática?",
  "dias": 30,
  "top_k": 8
}
```

**Resposta (200 OK):**

```json
{
  "turma_id": 1,
  "pergunta": "Quais são os pontos fracos da turma em Matemática?",
  "insight": "baseado em análise de dados e gerado pelo LLM local...",
  "fontes": [
    {
      "aluno": "João Silva",
      "media_notas": 5.5
    }
  ],
  "tempo_geracao_ms": 2345
}
```

---

## 4. Tratamento de Erros

Todos os erros seguem um padrão unificado:

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Você não tem permissão para realizar esta ação.",
    "details": {
      "required_roles": ["admin", "coordenador"]
    }
  }
}
```

### Códigos de Erro Comuns

| HTTP | Code                | Descrição                 |
| ---- | ------------------- | ------------------------- |
| 400  | `VALIDATION_ERROR`  | Dados inválidos           |
| 401  | `UNAUTHORIZED`      | Token expirado ou ausente |
| 403  | `PERMISSION_DENIED` | Sem permissão para ação   |
| 404  | `NOT_FOUND`         | Recurso não encontrado    |
| 500  | `INTERNAL_ERROR`    | Erro no servidor          |

---

## 5. Variáveis de Ambiente (Frontend)

Crie um arquivo `.env.local` (ou equivalente):

```env
REACT_APP_API_URL=http://localhost:8000/api
VITE_API_URL=http://localhost:8000/api
```

---

## 6. CORS Habilitado

O backend está configurado para aceitar requisições de:

- `http://localhost:3000` (React dev)
- `http://localhost:5173` (Vite dev)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

Para adicionar mais origens, atualize `CORS_ALLOWED_ORIGINS` no `.env` do backend.

---

## 7. Executar Backend Localmente

### Sem Docker

```bash
cd app/backend

# Instalar dependências
pip install -r ../requirements.txt

# Criar migrações
python manage.py migrate

# Criar superusuário (opcional)
python manage.py createsuperuser

# Rodar servidor
python manage.py runserver 0.0.0.0:8000
```

### Com Docker Compose

```bash
docker-compose up
```

Backend estará em: `http://localhost:8000`

---

## 8. Gerar Tipos TypeScript (OpenAPI)

Use ferramenta como `openapi-generator` ou `swagger-typescript-codegen`:

```bash
npm install -D openapi-generator-cli swagger-typescript-codegen

# Gerar tipos
openapi-generator-cli generate -i http://localhost:8000/api/schema/ -g typescript-axios -o ./src/generated
```

---

## 9. Exemplo Completo (React + Axios)

```typescript
import api from '@/services/api';
import { useState, useEffect } from 'react';

export function TurmasList() {
  const [turmas, setTurmas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTurmas = async () => {
      try {
        const { data } = await api.get('/turmas/');
        setTurmas(data);
      } catch (err) {
        setError(err.response?.data?.error?.message || 'Erro ao carregar turmas');
      } finally {
        setLoading(false);
      }
    };

    fetchTurmas();
  }, []);

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;

  return (
    <ul>
      {turmas.map((turma) => (
        <li key={turma.id}>
          {turma.nome} - {turma.disciplina.nome}
        </li>
      ))}
    </ul>
  );
}
```

---

## 10. Problemas Comuns e Soluções

### "CORS error: No 'Access-Control-Allow-Origin' header"

- ✅ Verificar `CORS_ALLOWED_ORIGINS` no backend
- ✅ Usar `http://localhost:3000` (não use `localhost` sem `http://`)

### "401 Unauthorized"

- ✅ Token expirado → renovar com refresh token
- ✅ Token não enviado no header → verificar interceptor

### "403 Forbidden"

- ✅ Seu usuário não tem role necessária
- ✅ Consulte `RBAC_ACCESS_MATRIX.md` para permissões

---

Este guia é seu referência para conectar o frontend. A API está pronta! 🚀
