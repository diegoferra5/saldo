# 📋 BBVA PDF Parser - Contexto de Producción

## 🎯 ¿Qué Hace el Parser?

El parser procesa estados de cuenta BBVA en PDF y extrae:

1. **Summary Financiero** del bloque "Comportamiento":
   - Saldo inicial/final
   - Total de depósitos/cargos
   - Cantidad de transacciones

2. **Transacciones Individuales** del bloque "Detalle de Movimientos":
   - Fecha operación/liquidación
   - Descripción del comercio
   - Monto
   - Saldos (cuando están disponibles)

3. **Clasificación Automática** (CARGO/ABONO/UNKNOWN):
   - Usa saldo de transacción cuando está disponible (alta confianza)
   - Usa keywords cuando no hay saldo (baja confianza)
   - Marca UNKNOWN cuando no puede decidir con confianza

4. **Validación Matemática**:
   - Compara totales parseados vs summary del banco
   - Alerta si hay discrepancias

---

## 📊 Schema de Transacción Final

```python
{
    # Identificación
    'id': UUID,
    'user_id': UUID,
    'statement_id': UUID,
    
    # Datos de la transacción
    'date': '11/NOV',                        # Formato original del PDF
    'date_liquidacion': '11/NOV',
    'transaction_date': date(2025, 11, 11),  # Fecha completa parseada
    'description': 'LACT YOGUFRUT',
    
    # Montos
    'amount_abs': 80.00,              # Siempre positivo
    'amount': -80.00,                 # Negativo=gasto, Positivo=ingreso, None=unknown
    
    # Clasificación
    'movement_type': 'CARGO',         # 'CARGO' | 'ABONO' | 'UNKNOWN'
    'needs_review': False,            # True si requiere revisión manual
    'category': 'Food & Dining',      # Categoría automática (opcional)
    
    # Saldos del PDF (opcionales)
    'saldo_operacion': 10948.46,
    'saldo_liquidacion': 10948.46,
    
    # Metadata futura
    'beneficiary': None,              # A implementar
    'reference': None,                # A implementar
    'clabe': None,                    # A implementar
    'is_recurring': False,            # A implementar
    
    # Timestamps
    'created_at': datetime,
    'updated_at': datetime
}
```

---

## 📈 Performance Actual

| Statement | Transacciones | Auto-clasificadas | UNKNOWN | Accuracy |
|-----------|---------------|-------------------|---------|----------|
| **Nov 2025** (moderno) | 34 | 29 (85%) | 5 (15%) | **85.3%** ✅ |
| **Ago 2023** (viejo) | 78 | 35 (45%) | 43 (55%) | **44.9%** ⚠️ |

**Observación**: BBVA mejoró la calidad de sus PDFs en 2024-2025, incluyendo más saldos en transacciones. Statements modernos tienen mucho mejor accuracy.

---

## 🚨 Limitaciones Conocidas

1. **"PAGO CUENTA DE TERCERO" sin saldo es ambiguo**
   - Puede ser enviado (cargo) o recibido (abono)
   - Sin información adicional, es imposible clasificar
   - Solución: Marca UNKNOWN → usuario clasifica

2. **Statements pre-2024 tienen menos información**
   - BBVA incluía menos campos de saldo
   - Más transacciones requieren revisión manual
   - No es bug del parser, es limitación de la fuente

3. **Líneas de detalle actualmente ignoradas**
   - Ejemplo: "BNET 1544197178 Bb" bajo "PAGO CUENTA DE TERCERO"
   - Contienen contexto útil (beneficiario, referencia)
   - Parser actual las salta (empiezan con espacio)

---

## 🛣️ Features Futuras a Implementar

### **Priority 1: Reducir UNKNOWN** (Weeks 5-6)

**1.1 Parser de Líneas de Detalle**
- Capturar líneas indentadas bajo cada transacción
- Extraer contexto: "Transf a NOMBRE" indica si es enviado/recibido
- **Impacto**: Reduce UNKNOWN de 43 → ~15 para statements viejos
- **Esfuerzo**: 4-6 horas

**1.2 Extracción de Beneficiario**
- Parsear nombre de persona/empresa de las líneas de detalle
- Agregar campos: `beneficiary`, `reference`, `clabe`
- **Impacto**: 
  - UX: "Pagaste $3,000 a Diego Ferra Lopez"
  - Analytics: "Top 5 personas a las que pagas"
  - Categorización: "Renta a Juan Pérez"
- **Esfuerzo**: 6-8 horas

**1.3 Bulk Classification UI**
- Seleccionar múltiples UNKNOWN y clasificar en bloque
- **Impacto**: Reduce onboarding de 10min → 2min
- **Esfuerzo**: 8-10 horas (frontend)

---

### **Priority 2: Intelligence** (Weeks 7-10)

**2.1 ML Personalizado por Usuario**
- Aprende de clasificaciones manuales del usuario
- Entrena modelo con mínimo 20 transacciones
- **Impacto**: Accuracy 95%+ después de 1-2 meses de uso
- **Tech**: sklearn LogisticRegression, features: description, amount, date
- **Esfuerzo**: 20-30 horas

**2.2 Detección de Transacciones Recurrentes**
- Identifica: renta mensual, suscripciones, nómina
- Algoritmo: Agrupa por descripción similar + intervalos regulares
- **Impacto**: 
  - Alertas de pagos próximos
  - Budgets más inteligentes
  - Detección de aumentos inesperados
- **Esfuerzo**: 15-20 horas

---

### **Priority 3: Multi-Bank** (Months 3-6)

**3.1 Support Santander & Banorte**
- Cada banco tiene layout de PDF diferente
- Arquitectura: `BankParserFactory` con parsers específicos
- **Esfuerzo por banco**: 10-15 horas

**3.2 Categorización Automática Avanzada**
- Expandir keywords para más categorías
- Mapear comercios conocidos (Netflix → Entertainment)
- **Categorías**: Food, Transport, Entertainment, Services, Health, Education, etc.
- **Esfuerzo**: 8-12 horas

---

### **Priority 4: Advanced** (Months 6-12)

**4.1 OCR Fallback para PDFs Escaneados**
- Detectar PDFs tipo "imagen" sin texto
- Usar Tesseract OCR para extraer texto
- **Impacto**: Soporta statements escaneados/fotografiados
- **Esfuerzo**: 20-25 horas

**4.2 Multi-Statement Analytics**
- Comparar mes vs mes (tendencias)
- Detectar cambios significativos en gastos
- Proyecciones de ahorro
- **Esfuerzo**: 30-40 horas

---

## 💼 Consideraciones de Negocio

### ✅ Fortalezas
- **UX superior**: Auto-clasifica 70-85% de transacciones modernas
- **Transparente**: Usuario entiende por qué algunos son UNKNOWN
- **Validación matemática**: Detecta errores automáticamente
- **Escalable**: Path claro hacia ML personalizado

### ⚠️ Riesgos
- **Onboarding friction**: Usuarios con statements viejos tienen más trabajo manual
- **Support tickets**: "¿Por qué no detecta esta transacción?"
- **Competencia API**: Belvo/Fintoc tienen conexión directa (pero solo Brasil/Chile)

### 💰 Monetización
**Freemium Model**:
- **Free**: 3 statements/mes, auto-classification básica
- **Premium ($4.99/mes)**: 
  - Ilimitados statements
  - ML personalizado (95%+ accuracy)
  - Export avanzado
  - Análisis multi-mes

**Premium justification**: ML que aprende de TUS clasificaciones

---

## ✅ Status: LISTO PARA MVP

**Ship Checklist**:
- [x] Core functionality completa
- [x] Accuracy 70-85% para statements modernos
- [x] Manejo robusto de edge cases (UNKNOWN)
- [x] Path claro hacia mejoras (features futuras)
- [x] Validación matemática funcionando

**Pendiente para producción:**
- [ ] Unit tests
- [ ] Integration tests con FastAPI
- [ ] Logging production-ready
- [ ] Telemetry (track % UNKNOWN por statement)

---

## 🚀 Próximo Paso

Integración con FastAPI:
1. Crear endpoint `POST /api/statements/parse`
2. Schema de base de datos (statements + transactions)
3. UI para manual review de UNKNOWN
4. Tutorial de onboarding

**Recomendación**: Ship MVP ahora, iterar con feedback de usuarios reales en Weeks 5-6.