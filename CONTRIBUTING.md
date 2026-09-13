# Guía de Contribución

## Código de Conducta

- Sé respetuoso con los demás
- Proporciona feedback constructivo
- Sé inclusivo y bienvenedor

## Cómo Contribuir

### 1. Fork y Clonar

```bash
git clone https://github.com/tu-usuario/Solaris-Monitoring.git
cd Solaris-Monitoring
git remote add upstream <repo-original>
```

### 2. Crear Rama

```bash
git checkout -b feature/descripcion-corta main

# Ejemplos de nombres:
# feature/add-authentication
# bugfix/fix-anomaly-detection
# docs/update-esp32-guide
```

### 3. Hacer Cambios

- Escribir código siguiendo PEP 8
- Usar type hints para todo
- Agregar docstrings cuando sea necesario
- Crear tests para nuevas funcionalidades

### 4. Testing

```bash
# Ejecutar tests
pytest

# Verificar cobertura
pytest --cov=src

# Validar código
ruff check .
mypy src tests
```

### 5. Commit

```bash
git add .
git commit -m "Descripción clara del cambio"
```

## Estándares de Código

- Seguir PEP 8
- Type hints en todo
- >90% test coverage
- Linting sin errores

## Testing

```bash
pytest --cov=src
```

Cobertura mínima: 90%

## Documentación

Actualizar documentación en `docs/` cuando sea necesario.

¡Gracias por contribuir!
