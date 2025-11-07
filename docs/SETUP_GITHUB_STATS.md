
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
