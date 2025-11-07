# GitHub Stats Configuration Guide

Este documento explica cómo configurar las estadísticas automáticas de GitHub que incluyen repositorios privados.

## ⚙️ Setup Requerido

### 1. Crear un GitHub Personal Access Token (PAT)

1. Ve a https://github.com/settings/tokens/new
2. Dale un nombre descriptivo: `GitHub Stats Action`
3. Selecciona los permisos:
   - ✅ `repo` (acceso a repositorios públicos y privados)
   - ✅ `read:user` (leer información del usuario)
   - ✅ `read:repo_hook` (leer webhooks)

4. Copia el token generado

### 2. Añadir el Token como Secreto de GitHub

1. Ve a tu repositorio: https://github.com/A4GOD-AMHG/A4GOD-AMHG
2. Settings → Secrets and variables → Actions
3. Haz clic en "New repository secret"
4. Nombre: `GITHUB_PAT`
5. Valor: Pega el token que copiaste
6. Haz clic en "Add secret"

### 3. Ejecutar el Workflow Manualmente

1. Ve a la pestaña "Actions" en tu repositorio
2. Selecciona "Update GitHub Stats"
3. Haz clic en "Run workflow"
4. El workflow ejecutará y generará tus estadísticas

## 🔄 Ejecución Automática

El workflow está configurado para ejecutarse:
- **Diariamente** a las 00:00 UTC (medianoche)
- **Manualmente** cuando lo desees desde la pestaña Actions

## 📊 Qué Incluye

El script genera estadísticas de:
- ✅ Total de repositorios (públicos + privados)
- ✅ Total de commits (incluyendo repositorios privados)
- ✅ Lenguajes más usados
- ✅ Total de estrellas (stars)
- ✅ Total de forks
- ✅ Seguidores
- ✅ Seguidos

## 🛠️ Ejecutar Localmente

Si quieres generar las estadísticas localmente:

```bash
export GH_TOKEN=tu_token_aqui
python scripts/generate_stats.py
```

## ⚠️ Seguridad

- **Nunca** compartas tu token público
- Los secretos de GitHub están encriptados
- El token solo se usa dentro de GitHub Actions
- Puedes revocar el token en cualquier momento desde https://github.com/settings/tokens

## ❌ Solución de Problemas

Si el workflow falla:

1. Verifica que el token tenga los permisos correctos
2. Revisa los logs en Actions → Update GitHub Stats
3. Asegúrate de que el nombre del secreto es `GITHUB_PAT`
4. Prueba ejecutándolo manualmente primero

## 📝 Notas

- GitHub Stats tarda unos minutos en completarse (depende del número de repos)
- El workflow respeta los límites de API de GitHub
- Las estadísticas se actualizan solo si hay cambios

¡Listo! Ahora tendrás estadísticas precisas incluyendo tus repositorios privados. 🎉
