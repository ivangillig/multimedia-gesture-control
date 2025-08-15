# Contributing to Control Multimedia con Manos

¡Gracias por tu interés en contribuir! 🎉

## 🚀 Cómo Contribuir

### 🐛 Reportar Bugs

1. Verifica que el bug no haya sido reportado anteriormente
2. Abre un issue con la etiqueta "bug"
3. Incluye:
   - Versión de Python y OS
   - Pasos para reproducir el bug
   - Comportamiento esperado vs actual
   - Screenshots/videos si es relevante

### 💡 Sugerir Mejoras

1. Abre un issue con la etiqueta "enhancement"
2. Describe claramente la funcionalidad propuesta
3. Explica por qué sería útil
4. Incluye mockups o ejemplos si es posible

### 🔧 Pull Requests

1. Fork el repositorio
2. Crea una branch para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. Realiza tus cambios siguiendo las guías de estilo
4. Escribe o actualiza tests si es necesario
5. Actualiza la documentación si es relevante
6. Asegúrate de que los tests pasan
7. Commit con mensajes descriptivos
8. Push a tu fork: `git push origin feature/nueva-funcionalidad`
9. Abre un Pull Request

## 📝 Guías de Estilo

### Python Code Style
- Seguir PEP 8
- Usar type hints cuando sea posible
- Comentarios claros en español
- Docstrings para funciones complejas

### Git Commits
Formato: `tipo(scope): descripción`

Ejemplos:
- `feat(gestures): agregar reconocimiento de gesto peace`
- `fix(volume): corregir mapeo de distancia a volumen`
- `docs(readme): actualizar instrucciones de instalación`

## 🧪 Tests

```bash
# Ejecutar tests (cuando estén disponibles)
python -m pytest tests/

# Verificar lint
flake8 *.py
```

## 📋 Checklist para PRs

- [ ] El código sigue las guías de estilo
- [ ] Los tests pasan (si existen)
- [ ] La documentación está actualizada
- [ ] Los commits tienen mensajes descriptivos
- [ ] Se probó en Windows
- [ ] No rompe funcionalidad existente

## 🤝 Código de Conducta

- Se respetuoso y constructivo
- Acepta críticas constructivas
- Enfócate en lo mejor para el proyecto
- Ayuda a otros contribuidores

## 💬 ¿Dudas?

¡No dudes en abrir un issue o discussion para cualquier pregunta!
