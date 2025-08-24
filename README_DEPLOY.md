
# Vacaciones CH-1 (Cloud) — Despliegue en Streamlit Community Cloud

Esta versión guarda todo en **Google Sheets** (multiusuario, nada se pierde) y se
despliega en **Streamlit Community Cloud** gratis.

## 0) Prepara tu Google Sheet
1. Crea una hoja de cálculo en Google Sheets con **dos pestañas**:
   - `empleados`: columnas **numero | nombre | equipo**
   - `agenda`: columnas **numero | nombre | equipo | fecha | tipo**
2. (Opcional) Importa tus empleados desde `employees_template.csv`.
3. Copia la **URL** de la hoja (la necesitarás como `sheet_url`).

## 1) Crea una cuenta de servicio (Google Cloud)
1. Entra a https://console.cloud.google.com/ (elige o crea un proyecto).
2. Habilita **Google Sheets API** y **Google Drive API** (solo lectura/escritura).
3. Crea una **Service Account** y genera una **clave JSON**.
4. **Comparte** tu Google Sheet con el **email** de la service account (permiso Editor).

## 2) Sube a GitHub este repo (estos archivos):
- `app_vacaciones_cloud.py`
- `storage_gsheets.py`
- `requirements.txt`

## 3) Secrets en Streamlit Cloud
En la página del deploy, abre **Manage app → Secrets** y pega algo así:

```toml
[gcp_service_account]
type = "service_account"
project_id = "TU_PROYECTO"
private_key_id = "XXXXXXXXXXXX"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIB...==\n-----END PRIVATE KEY-----\n"
client_email = "xxxx@xxxx.iam.gserviceaccount.com"
client_id = "12345678901234567890"
token_uri = "https://oauth2.googleapis.com/token"

sheet_url = "https://docs.google.com/spreadsheets/d/XXXXXXXXXXXX/edit"
admin_password = "CH1-Admin-2025"
```

> **Importante**: la **private_key** debe conservar los `\n` tal cual.

## 4) Deploy
- En https://share.streamlit.io/ selecciona tu repo y como **file** pon `app_vacaciones_cloud.py`.
- Streamlit instalará `requirements.txt` y lanzará la app.
- Comparte la URL pública que te da Streamlit.

## 5) Notas operativas
- **Admin**: exportar Excel/CSV y eliminar registros (desde la pestaña Calendario).  
- **Reglas activas**: máximo **3 por día** y **no** dos del **mismo equipo** el mismo día.  
- Cada alta/edición **limpia el cache** (TTL 15–30 s) para que todos vean datos frescos.

## 6) Migrar empleados
- Abre la pestaña `empleados` del Google Sheet y pega tus filas (numero, nombre, equipo).  
- Ya con eso, al escribir un número en la app, se autocompletan nombre/equipo.

---

¿Quieres dominio propio (e.g., `vacaciones.tu-empresa.com`) y SSO? Podemos moverlo a Cloudflare Tunnel + Access.
