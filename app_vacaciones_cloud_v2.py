
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime as dt
import calendar
from io import BytesIO

from storage_gsheets_v2 import (
    get_empleados_dict,
    get_agenda_df,
    append_agenda_row,
    replace_agenda_df,
)

st.set_page_config(page_title="Vacaciones CH-1 (Cloud)", page_icon="📅", layout="wide")

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
DIAS = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
ADMIN_PASSWORD = st.secrets.get("admin_password", "CH1-Admin-2025")

@st.cache_data(ttl=30)
def load_empleados():
    return get_empleados_dict()

@st.cache_data(ttl=15)
def load_agenda_df():
    df = get_agenda_df()
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["fecha"])
    return df

def clear_cache():
    load_empleados.clear()
    load_agenda_df.clear()

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.header("Vacaciones CH-1 (Cloud)")
    with st.expander("🔑 Administrador", expanded=False):
        if not st.session_state.is_admin:
            admin_pwd = st.text_input("Contraseña admin", type="password", key="admin_pwd")
            if st.button("Entrar como admin", key="btn_admin_login"):
                if admin_pwd == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.success("Sesión de administrador activa")
                else:
                    st.error("Contraseña incorrecta")
        else:
            st.success("Sesión admin activa")
            if st.button("Cerrar sesión admin", key="btn_admin_logout"):
                st.session_state.is_admin = False

tab1, tab2 = st.tabs(["📝 Captura", "📅 Calendario / Exportación"])

with tab1:
    st.subheader("Captura de solicitudes")
    empleados_db = load_empleados()
    agenda_df = load_agenda_df()

    c1, c2 = st.columns(2)
    with c1:
        password = st.text_input("Contraseña (usuario)", type="password", key="pwd_user")
    with c2:
        numero_empleado = st.text_input("Número de empleado", key="num_emp")

    if password and numero_empleado in empleados_db:
        emp = empleados_db[numero_empleado]
        st.success(f"{emp['nombre']} — Equipo: {emp['equipo']}")

        hoy = dt.date.today()
        c3, c4, c5 = st.columns(3)
        with c3:
            anio = st.number_input("Año", min_value=hoy.year, max_value=hoy.year+2, value=hoy.year, step=1, key="anio_cap")
        with c4:
            mes = st.selectbox("Mes", list(range(1,13)), index=hoy.month-1, format_func=lambda m: MESES[m-1], key="mes_cap")
        dias_mes = calendar.monthrange(int(anio), int(mes))[1]
        with c5:
            dia = st.selectbox("Día", list(range(1, dias_mes+1)), index=min(hoy.day-1, dias_mes-1), key="dia_cap")

        tipo = st.selectbox("Tipo", ["Vacaciones", "Permiso", "Sanción"], key="tipo_cap")
        fecha = dt.date(int(anio), int(mes), int(dia))

        personas_mismo_dia = agenda_df[agenda_df["fecha"].dt.date == fecha]
        dia_lleno = len(personas_mismo_dia) >= 3
        mismo_equipo = any(personas_mismo_dia["equipo"] == emp["equipo"])

        if dia_lleno:
            st.warning("Seleccione otro día, ya que el día que solicitas ya está llena la agenda")
            registrar_habilitado = False
        elif mismo_equipo:
            st.warning("No puedes seleccionar este día porque ya hay alguien de tu equipo registrado")
            registrar_habilitado = False
        else:
            registrar_habilitado = True

        colA, colB = st.columns([1,2])
        with colA:
            if st.button("Registrar día", disabled=not registrar_habilitado, key="btn_registrar"):
                append_agenda_row({
                    "numero": numero_empleado,
                    "nombre": emp["nombre"],
                    "equipo": emp["equipo"],
                    "fecha": fecha.isoformat(),
                    "tipo": tipo
                })
                clear_cache()
                st.success("Día registrado exitosamente")
        with colB:
            st.info(
                f"Registrados el {fecha.isoformat()}: "
                + (", ".join(personas_mismo_dia["nombre"].tolist()) if not personas_mismo_dia.empty else "ninguno")
            )

        if not personas_mismo_dia.empty:
            st.write("**Detalle del día**")
            st.table(personas_mismo_dia[["numero","nombre","equipo","tipo"]])

    else:
        st.info("Ingresa tu contraseña y un número de empleado válido para capturar.")

with tab2:
    st.subheader("Calendario mensual y exportación")
    empleados_db = load_empleados()
    df = load_agenda_df()

    hoy = dt.date.today()
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        anioC = st.number_input("Año", value=hoy.year, min_value=hoy.year-1, max_value=hoy.year+3, key="anio_cal")
    with c2:
        mesC = st.selectbox("Mes", list(range(1,13)), index=hoy.month-1, format_func=lambda m: MESES[m-1], key="mes_cal")
    with c3:
        equipos = sorted({ v["equipo"] for v in empleados_db.values() })
        equipo_sel = st.selectbox("Equipo", ["Todos"] + equipos, key="equipo_cal")
    with c4:
        solo_llenos = st.checkbox("Solo días llenos (3)", value=False, key="llenos_cal")

    dias_mes = calendar.monthrange(int(anioC), int(mesC))[1]
    f_ini_date = dt.date(int(anioC), int(mesC), 1)
    f_fin_date = dt.date(int(anioC), int(mesC), dias_mes)

    if not df.empty:
        fechas_date = df["fecha"].dt.date
        mask = (fechas_date >= f_ini_date) & (fechas_date <= f_fin_date)
        df_mes = df[mask].copy()
        df_mes["dia"] = df_mes["fecha"].dt.day
    else:
        df_mes = df.copy()
        df_mes["dia"] = []

    if equipo_sel != "Todos" and not df_mes.empty:
        df_eq = df_mes[df_mes["equipo"] == equipo_sel]
    else:
        df_eq = pd.DataFrame(columns=df_mes.columns)

    conteo_total = df_mes.groupby("dia")["numero"].count().to_dict() if not df_mes.empty else {}
    conteo_equipo = df_eq.groupby("dia")["numero"].count().to_dict() if not df_eq.empty else {}

    def color_for(c):
        if not c or c == 0: return "#e9ecef"
        if c == 1: return "#2ecc71"
        if c == 2: return "#f1c40f"
        return "#e74c3c"

    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(int(anioC), int(mesC))

    legend = """
    <div style='display:flex; gap:12px; align-items:center; font-size:14px;'>
      <div style='display:flex; align-items:center; gap:6px;'><span style='display:inline-block;width:16px;height:16px;background:#e9ecef;border:1px solid #ccc;'></span> 0</div>
      <div style='display:flex; align-items:center; gap:6px;'><span style='display:inline-block;width:16px;height:16px;background:#2ecc71;'></span> 1</div>
      <div style='display:flex; align-items:center; gap:6px;'><span style='display:inline-block;width:16px;height:16px;background:#f1c40f;'></span> 2</div>
      <div style='display:flex; align-items:center; gap:6px;'><span style='display:inline-block;width:16px;height:16px;background:#e74c3c;'></span> 3</div>
      <div style='display:flex; align-items:center; gap:6px;'><span style='display:inline-block;width:12px;height:12px;border-radius:50%;background:#00bcd4;'></span> Equipo seleccionado</div>
    </div>
    """
    st.markdown(legend, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    html = "<table style='border-collapse:separate;border-spacing:8px;width:100%;table-layout:fixed;'>"
    html += "<tr>" + "".join([f"<th style='text-align:center;font-weight:600;color:#333'>{d}</th>" for d in DIAS]) + "</tr>"
    for week in weeks:
        html += "<tr>"
        for d in week:
            if d == 0:
                html += "<td></td>"
                continue
            count = int(conteo_total.get(d, 0))
            if solo_llenos and count < 3:
                html += "<td style='height:90px'></td>"
                continue
            color = color_for(count)
            dot = ""
            if equipo_sel != "Todos" and conteo_equipo.get(d, 0) > 0:
                dot = "<div style='margin-top:6px;'><span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:#00bcd4;'></span></div>"
            cell = f"""
            <td style='vertical-align:top; padding:8px; background:{color}; border:1px solid #ddd; border-radius:10px; text-align:center; height:90px;'>
              <div style='font-weight:700;color:#1b1e23;font-size:16px'>{d}</div>
              <div style='font-size:12px;color:#1b1e23'>{count} registro(s)</div>
              {dot}
            </td>
            """
            html += cell
        html += "</tr>"
    html += "</table>"

    cal_height = 80 + (len(weeks) * 120)
    components.html(html, height=cal_height, scrolling=True)

    st.markdown("---")
    cD1, cD2 = st.columns([1,3])
    with cD1:
        dia_sel = st.number_input("Día", min_value=1, max_value=dias_mes, value=min(dt.date.today().day, dias_mes), key="dia_cal")
    with cD2:
        st.write("**Detalle del día seleccionado**")

    if not df_mes.empty:
        df_dia = df_mes[df_mes["dia"] == int(dia_sel)].copy()
    else:
        df_dia = pd.DataFrame(columns=df_mes.columns.tolist())

    if equipo_sel != "Todos" and not df_dia.empty:
        df_dia = df_dia[df_dia["equipo"] == equipo_sel]

    if df_dia.empty:
        st.info("Sin registros para este día (con el filtro actual).")
    else:
        df_show = df_dia.copy()
        df_show["fecha"] = df_show["fecha"].dt.strftime("%Y-%m-%d")
        st.dataframe(df_show[["numero","nombre","equipo","fecha","tipo"]].sort_values(by=["equipo","nombre"]), use_container_width=True, hide_index=True)

        if st.session_state.is_admin:
            st.markdown("**Acciones de administrador**")
            opciones = [f"{r['numero']} · {r['nombre']} · {r['equipo']} · {r['tipo']}" for _, r in df_show.iterrows()]
            to_delete = st.multiselect("Selecciona registros a eliminar", opciones, key="del_multi")
            if st.button("Eliminar seleccionados", type="primary", key="btn_delete"):
                if to_delete:
                    df_all = load_agenda_df().copy()
                    df_all["etag"] = df_all["numero"].astype(str) + " · " + df_all["nombre"] + " · " + df_all["equipo"] + " · " + df_all["tipo"]
                    fecha_sel = dt.date(int(anioC), int(mesC), int(dia_sel))
                    mask_keep = ~( (df_all["fecha"].dt.date == fecha_sel) & (df_all["etag"].isin(to_delete)) )
                    df_new = df_all[mask_keep][["numero","nombre","equipo","fecha","tipo"]].copy()
                    replace_agenda_df(df_new)
                    clear_cache()
                    st.success("Registros eliminados")
                    st.experimental_rerun()

    st.markdown("---")
    if st.session_state.is_admin:
        df_export = load_agenda_df().copy()
        if df_export.empty:
            st.warning("No hay datos para exportar.")
        else:
            df_export["fecha"] = pd.to_datetime(df_export["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
            df_req = df_export[["numero","nombre","fecha","equipo","tipo"]]
            excel_io = BytesIO()
            with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
                df_req.to_excel(writer, index=False, sheet_name="Agenda")
            st.download_button(
                "⬇️ Descargar Excel (Agenda)",
                data=excel_io.getvalue(),
                file_name="agenda_vacaciones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_excel"
            )
            st.download_button(
                "⬇️ Descargar CSV (Agenda)",
                data=df_req.to_csv(index=False).encode("utf-8"),
                file_name="agenda_vacaciones.csv",
                mime="text/csv",
                key="dl_csv"
            )
    else:
        st.info("Inicia sesión como admin (sidebar) para exportar o borrar registros.")
