
# storage_gsheets.py — utilidades de persistencia con Google Sheets
# Requiere los secrets:
# [gcp_service_account]  -> JSON de la cuenta de servicio
# sheet_url = "https://docs.google.com/spreadsheets/d/...."
#
# Estructura del Google Sheet (dos pestañas):
# - "agenda":  columnas -> numero | nombre | equipo | fecha | tipo
# - "empleados": columnas -> numero | nombre | equipo

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _client():
    info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(info, scopes=SCOPE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(st.secrets["sheet_url"])
    return sh

def _ws(name: str):
    sh = _client()
    try:
        return sh.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        # Si no existe, crear con encabezados
        ws = sh.add_worksheet(title=name, rows=1000, cols=10)
        if name == "agenda":
            ws.update("A1:E1", [["numero","nombre","equipo","fecha","tipo"]])
        elif name == "empleados":
            ws.update("A1:C1", [["numero","nombre","equipo"]])
        return ws

def get_empleados_dict() -> dict:
    ws = _ws("empleados")
    rows = ws.get_all_records()
    d = {}
    for r in rows:
        num = str(r.get("numero", "")).strip()
        if not num: 
            continue
        d[num] = {
            "nombre": str(r.get("nombre","")).strip(),
            "equipo": str(r.get("equipo","")).strip(),
        }
    return d

def get_agenda_df() -> pd.DataFrame:
    ws = _ws("agenda")
    rows = ws.get_all_records()
    if not rows:
        return pd.DataFrame(columns=["numero","nombre","equipo","fecha","tipo"])
    df = pd.DataFrame(rows, columns=["numero","nombre","equipo","fecha","tipo"])
    # Cast tipos
    df["numero"] = df["numero"].astype(str)
    return df

def append_agenda_row(rec: dict):
    ws = _ws("agenda")
    ws.append_row([rec["numero"], rec["nombre"], rec["equipo"], rec["fecha"], rec["tipo"]], value_input_option="USER_ENTERED")

def replace_agenda_df(df: pd.DataFrame):
    ws = _ws("agenda")
    # Limpiar y escribir todo de nuevo (incluye encabezados)
    ws.clear()
    ws.update("A1:E1", [["numero","nombre","equipo","fecha","tipo"]])
    if df is None or df.empty:
        return
    # Asegurar orden y convertir fechas a texto ISO
    df2 = df.copy()
    df2["fecha"] = pd.to_datetime(df2["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    values = df2[["numero","nombre","equipo","fecha","tipo"]].astype(str).fillna("").values.tolist()
    ws.update("A2", values)
