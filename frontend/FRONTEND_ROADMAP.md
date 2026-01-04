# 🗺️ FRONTEND ROADMAP - Saldo App

## 📋 STACK GENERAL

```
Framework:     Next.js 14 (App Router)
Language:      TypeScript 5+
Styling:       Tailwind CSS 3
UI:            Shadcn/ui
State:         Zustand (auth, user preferences)
Data Fetch:    TanStack Query v5
HTTP:          Axios
Forms:         React Hook Form + Zod
Charts:        Recharts
Uploads:       react-dropzone
Notifications: sonner (toast)
Icons:         lucide-react
```

---

## 🔐 AUTHENTICATION FLOW

### **Stack de Auth**
- **State Management**: Zustand store persistido en localStorage
- **Validation**: Zod schemas (min 8 chars password, email format)
- **HTTP**: Axios con interceptors
- **Forms**: React Hook Form
- **UI**: Shadcn/ui (Input, Button, Card, Label)

### **Flujo de Autenticación**

```
┌─────────────┐
│   /login    │ → POST /api/auth/login → JWT token
└─────────────┘          ↓
                   Zustand Store
                   (token + user)
                         ↓
                   localStorage
                         ↓
                   Axios Interceptor
                   (todas las requests)
                         ↓
                   Protected Routes
                   (/dashboard/*)
```

**Logout Flow:**
```
User clicks logout → Clear Zustand → Clear localStorage → Redirect /login
```

**Token Refresh:**
- Backend token dura 7 días
- Frontend valida en cada request
- Si 401 → logout automático + redirect

---

## 📄 PÁGINA POR PÁGINA - STACK BREAKDOWN

### **1. /login**
**Propósito:** Autenticación de usuarios existentes

**Stack:**
```typescript
Components:   Shadcn Card, Input, Button, Label
Form:         React Hook Form + Zod
Validation:   - Email válido
              - Password min 8 chars
State:        Local form state (react-hook-form)
API Call:     POST /api/auth/login
Success:      → Zustand.setAuth() → redirect /dashboard
Error:        → Toast notification (sonner)
```

**Features:**
- Email/password fields
- "Forgot password?" link (future)
- "Don't have an account? Sign up" link
- Loading state en botón
- Error handling (credenciales inválidas)

---

### **2. /signup**
**Propósito:** Registro de nuevos usuarios

**Stack:**
```typescript
Components:   Shadcn Card, Input, Button, Label
Form:         React Hook Form + Zod
Validation:   - Email válido + único
              - Password min 8 chars
              - Confirm password (match)
              - Full name (opcional pero recomendado)
State:        Local form state
API Call:     POST /api/auth/register
Success:      → Auto-login (token en response) → /dashboard
Error:        → Toast (email ya existe)
```

**Features:**
- Full name field
- Email field
- Password + Confirm Password
- "Already have an account? Login" link
- Password strength indicator (opcional)
- Loading state

---

### **3. /dashboard**
**Propósito:** Overview financiero + estadísticas

**Stack:**
```typescript
Layout:       Protected layout con sidebar
Data Fetch:   TanStack Query
  - useQuery(['stats']) → GET /api/transactions/stats
  - useQuery(['accounts']) → GET /api/accounts
  - useQuery(['recent-transactions']) → GET /api/transactions?limit=10
Charts:       Recharts (BarChart para ingresos/gastos)
Components:   - StatCard (ingresos, gastos, balance)
              - RecentTransactions (tabla)
              - AccountSummary (cards por cuenta)
Refresh:      Auto-refetch cada 60s
```

**Features:**
- KPIs: Total ingresos, gastos, balance
- Gráfica de cash flow (últimos 6 meses)
- Últimas 10 transacciones
- Resumen por cuenta (BBVA débito, crédito, etc.)

---

### **4. /accounts**
**Propósito:** Gestión de cuentas bancarias

**Stack:**
```typescript
Data Fetch:   TanStack Query
  - useQuery(['accounts']) → GET /api/accounts
  - useMutation → POST /api/accounts (crear)
  - useMutation → PATCH /api/accounts/{id} (actualizar)
  - useMutation → DELETE /api/accounts/{id} (soft delete)
Components:   - AccountCard (display_name, bank, type, balance)
              - AddAccountDialog (Shadcn Dialog + Form)
              - EditAccountDialog
Filters:      - bank_name (dropdown)
              - account_type (tabs: all, debit, credit)
              - is_active (toggle)
State:        Query state (no Zustand necesario)
```

**Features:**
- Grid de cuentas (cards)
- Crear nueva cuenta (bank selector + type)
- Editar display_name
- Activar/desactivar cuenta
- Ver transacciones por cuenta (link a /transactions?account_id=X)

---

### **5. /statements**
**Propósito:** Upload y gestión de estados de cuenta PDF

**Stack:**
```typescript
Upload:       react-dropzone
  - Accept: .pdf only
  - Max size: 10MB
  - Preview filename antes de upload
Data Fetch:   TanStack Query
  - useQuery(['statements']) → GET /api/statements
  - useMutation → POST /api/statements/upload (multipart/form-data)
  - useMutation → POST /api/statements/{id}/process (parse PDF)
  - useMutation → DELETE /api/statements/{id}
Progress:     Axios onUploadProgress → Progress bar
Components:   - DropzoneArea (drag & drop)
              - StatementList (tabla con estado: pending/processing/success/failed)
              - UploadDialog (seleccionar bank + account + month)
Filters:      - bank_name
              - account_type
              - statement_month (date picker)
```

**Features:**
- Drag & drop PDF
- Select bank + account + month antes de upload
- Progress bar durante upload
- Botón "Process" para parsear PDF
- Ver health check (balance validation)
- Lista de statements con estados
- Delete statement

---

### **6. /transactions**
**Propósito:** Lista detallada y editable de transacciones

**Stack:**
```typescript
Data Fetch:   TanStack Query
  - useQuery(['transactions', filters]) → GET /api/transactions
  - useMutation → PATCH /api/transactions/{id}
Table:        Shadcn Table (sortable)
Filters:      - account_id (multi-select)
              - date_from / date_to (date range picker)
              - movement_type (CARGO/ABONO/UNKNOWN)
              - needs_review (checkbox)
              - search (description contains)
Pagination:   Client-side (TanStack Table)
Components:   - FilterBar (sticky top)
              - TransactionTable
              - EditTransactionDialog (cambiar category, movement_type)
              - BulkActions (future: seleccionar múltiples)
Export:       CSV download (future)
```

**Features:**
- Tabla con columnas: date, description, amount, movement_type, category, account
- Filtros avanzados (sticky)
- Click row → modal de edición
- Marcar/desmarcar "needs_review"
- Color coding: ABONO (green), CARGO (red), UNKNOWN (gray)
- Sort por fecha, monto, tipo

---

### **7. /settings**
**Propósito:** Configuración de usuario y preferencias

**Stack:**
```typescript
Data Fetch:   TanStack Query
  - useQuery(['user']) → GET /api/auth/me
  - useMutation → PATCH /api/users/me (future endpoint)
Components:   - ProfileSection (full_name, email)
              - PreferencesSection (theme, currency, date format)
              - SecuritySection (change password - future)
State:        Zustand para theme preference
```

**Features:**
- Editar full_name
- Ver email (readonly)
- Dark mode toggle (Zustand + localStorage)
- Logout button

---

## 🎨 LAYOUTS Y COMPONENTES COMPARTIDOS

### **Layout Estructura**

```
/app
├── (auth)
│   ├── layout.tsx          → Centered card, no sidebar
│   ├── /login/page.tsx
│   └── /signup/page.tsx
├── (dashboard)
│   ├── layout.tsx          → Sidebar + topbar (protected)
│   ├── /dashboard/page.tsx
│   ├── /accounts/page.tsx
│   ├── /statements/page.tsx
│   ├── /transactions/page.tsx
│   └── /settings/page.tsx
└── layout.tsx              → Root (Providers: TanStack, Theme)
```

### **Componentes Globales**

```typescript
/components
├── /ui                     → Shadcn components (Button, Input, etc.)
├── /layout
│   ├── Sidebar.tsx         → Nav links + logo
│   ├── Topbar.tsx          → User menu + notifications
│   └── ProtectedRoute.tsx  → Middleware wrapper
├── /features
│   ├── /auth
│   │   ├── LoginForm.tsx
│   │   └── SignupForm.tsx
│   ├── /transactions
│   │   ├── TransactionTable.tsx
│   │   ├── TransactionFilters.tsx
│   │   └── EditTransactionDialog.tsx
│   ├── /accounts
│   │   ├── AccountCard.tsx
│   │   └── AddAccountDialog.tsx
│   └── /statements
│       ├── DropzoneArea.tsx
│       └── StatementList.tsx
└── /shared
    ├── LoadingSpinner.tsx
    ├── ErrorBoundary.tsx
    └── EmptyState.tsx
```

---

## 🔧 SERVICIOS Y UTILIDADES

### **/lib**

```typescript
/lib
├── api.ts                  → Axios instance + interceptors
├── queries/
│   ├── auth.ts             → useLogin, useSignup, useMe
│   ├── accounts.ts         → useAccounts, useCreateAccount, etc.
│   ├── statements.ts       → useStatements, useUploadStatement
│   └── transactions.ts     → useTransactions, useUpdateTransaction
├── stores/
│   ├── authStore.ts        → Zustand (token, user, login, logout)
│   └── themeStore.ts       → Zustand (theme preference)
├── validations/
│   ├── auth.ts             → Zod schemas (loginSchema, signupSchema)
│   ├── account.ts          → accountSchema
│   └── transaction.ts      → transactionUpdateSchema
└── utils/
    ├── formatters.ts       → formatCurrency, formatDate
    └── constants.ts        → BANK_NAMES, ACCOUNT_TYPES, etc.
```

---

## 📦 DEPENDENCIAS COMPLETAS

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",

    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.28.0",
    "axios": "^1.6.8",

    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.4",
    "zod": "^3.22.4",

    "tailwindcss": "^3.4.1",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-tabs": "^1.0.4",

    "recharts": "^2.12.0",
    "react-dropzone": "^14.2.3",
    "sonner": "^1.4.3",
    "lucide-react": "^0.363.0",
    "date-fns": "^3.6.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "eslint": "^8",
    "eslint-config-next": "14.2.0",
    "postcss": "^8",
    "autoprefixer": "^10"
  }
}
```

---

## 🚀 ORDEN DE IMPLEMENTACIÓN

### **Sprint 1: Foundation (Auth) - COMENZAMOS AQUÍ**
1. ✅ Setup Next.js project
2. ✅ Install dependencies
3. ✅ Configure Tailwind + Shadcn
4. ✅ Setup axios client
5. ✅ Create Zustand auth store
6. ✅ Build /login page
7. ✅ Build /signup page
8. ✅ Implement protected route middleware
9. ✅ Test auth flow end-to-end

### **Sprint 2: Core Features**
10. Dashboard page (stats + recent transactions)
11. Accounts page (CRUD)
12. Basic transaction list

### **Sprint 3: Advanced Features**
13. Statement upload + parsing
14. Transaction filters + editing
15. Charts y analytics

### **Sprint 4: Polish**
16. Settings page
17. Error handling global
18. Loading states
19. Responsive design
20. Dark mode

---

## 🎯 DECISIONES TÉCNICAS CLAVE

### **¿Por qué Zustand y no Context API?**
- Menos boilerplate
- Mejor performance (sin re-renders innecesarios)
- Persistencia built-in (middleware)
- Devtools

### **¿Por qué TanStack Query?**
- Caching automático (reduce llamadas al backend)
- Stale-while-revalidate pattern
- Polling para updates en tiempo real
- Invalidación inteligente después de mutations
- Loading/error states automáticos

### **¿Por qué Shadcn y no MUI/Chakra?**
- No es librería (copy-paste components)
- Tailwind-native (consistencia)
- Accesibilidad built-in (Radix UI)
- Customizable 100%
- Zero bundle size (solo importas lo que usas)

### **¿Por qué Axios y no fetch?**
- Interceptors (perfecto para auth)
- Upload progress (statements PDF)
- Automatic JSON parsing
- Better error handling
- Request/response transforms

---

## 📝 PRÓXIMOS PASOS INMEDIATOS

1. Crear proyecto Next.js
2. Instalar dependencias
3. Configurar Shadcn/ui
4. Crear estructura de carpetas
5. **Implementar auth flow completo** ← EMPEZAMOS AQUÍ

¿Listo para comenzar con el setup? 🚀
