import streamlit as st
import holidays
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Configuración de página
st.set_page_config(page_title="RomoLegal - Auditoría NRD", layout="centered")

# --- SIDEBAR DE IDENTIDAD ---
with st.sidebar:
    st.markdown("# ⚖️ RomoLegal")
    st.markdown("---")
    st.markdown("### **Developed by:**")
    st.write("Lorena Romo")
    st.write("---") 

def obtener_siguiente_habil(fecha, festivos_co):
    # Guardamos la fecha original para saber si hubo cambios
    fecha_inicial = fecha
    while fecha.weekday() >= 5 or fecha in festivos_co:
        fecha += timedelta(days=1)
    return fecha, fecha_inicial

st.title("⏳ Calculador de Caducidad (CPACA)")
st.subheader("Análisis de caducidad de la acción de Nulidad y Restablecimiento del Derecho para acudir a la JCA.")

# --- BLOQUE DE ENTRADA ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        f_notif = st.date_input("Fecha de Notificación", value=None)
        tipo_notif = st.selectbox("Tipo de Notificación", ["Personal", "Aviso"])
    with col2:
        f_demanda = st.date_input("Fecha de Presentación Demanda", value=None)

    st.divider()
    st.write("### Suspensiones")
    
    usa_csj = st.checkbox("¿Hubo suspensión extraordinaria (CSJ/Paros)?")
    f_inicio_csj, f_fin_csj = None, None
    if usa_csj:
        c1, c2 = st.columns(2)
        f_inicio_csj = c1.date_input("Inicio Suspensión CSJ")
        f_fin_csj = c2.date_input("Levantamiento CSJ")

    usa_conc = st.checkbox("¿Se agotó requisito de conciliación?")
    f_sol, f_con = None, None
    if usa_conc:
        c1, c2 = st.columns(2)
        f_sol = c1.date_input("Fecha Solicitud")
        f_con = c2.date_input("Fecha Acta/Constancia")

# --- LÓGICA DE CÁLCULO ---
if st.button("Realizar Análisis Jurídico"):
    if not f_notif or not f_demanda:
        st.warning("Por favor, ingrese las fechas básicas.")
    else:
        notif = datetime.combine(f_notif, datetime.min.time())
        demanda = datetime.combine(f_demanda, datetime.min.time())
        festivos = holidays.Colombia(years=range(notif.year, notif.year + 3))

        f_inicio = notif + timedelta(days=2 if tipo_notif == "Aviso" else 1)
        vencimiento_orig = f_inicio + relativedelta(months=4)

        vencimiento_final = vencimiento_orig
        punto_reanuda = None
        remanente_str = "0 meses y 0 días"

        suspensiones = []
        if usa_csj and f_inicio_csj and f_fin_csj:
            suspensiones.append((datetime.combine(f_inicio_csj, datetime.min.time()), 
                                 datetime.combine(f_fin_csj, datetime.min.time())))
        if usa_conc and f_sol and f_con:
            suspensiones.append((datetime.combine(f_sol, datetime.min.time()), 
                                 datetime.combine(f_con, datetime.min.time())))

        if suspensiones:
            suspensiones.sort(key=lambda x: x[0])
            primera = suspensiones[0]
            if primera[0] < vencimiento_orig:
                delta = relativedelta(vencimiento_orig, primera[0])
                r_meses, r_dias = delta.months, delta.days
                remanente_str = f"{r_meses} mes(es) y {r_dias} día(s)"
                punto_reanuda = max(s[1] for s in suspensiones)
                vencimiento_final = punto_reanuda + relativedelta(months=r_meses) + timedelta(days=r_dias)

        # AJUSTE POR INHÁBIL CON ADVERTENCIA
        vencimiento_final, fecha_antes_ajuste = obtener_siguiente_habil(vencimiento_final, festivos)

        # --- RESULTADOS ---
        st.divider()
        
        # 1. Alerta de traslado por festivo (Lo que pediste)
        if vencimiento_final != fecha_antes_ajuste:
            nombre_motivo = festivos.get(fecha_antes_ajuste, "fin de semana")
            st.warning(f"⚠️ **Aviso de Traslado:** El término vencía originalmente el {fecha_antes_ajuste.strftime('%d/%m/%Y')}, pero por ser **{nombre_motivo}**, se traslada al primer día hábil siguiente: **{vencimiento_final.strftime('%d/%m/%Y')}** (Art. 62 Ley 4 de 1913).")

        # 2. Control de Procedibilidad
        if not usa_conc:
            st.error("### ESTADO: RECHAZO POR PROCEDIBILIDAD")
            st.write("No presentó solicitud de conciliación: no puede acudir a la Jurisdicción Contencioso Administrativa (Art. 161 CPACA).")
        
        # 3. Control de Temporalidad
        elif demanda > vencimiento_final:
            st.error("### ESTADO: CADUCADA")
        else:
            st.success("### ESTADO: OPORTUNA")
            
        st.info(f"""
        **Sustentación del Cálculo:**
        * **Inicio de conteo:** {f_inicio.strftime('%d/%m/%Y')}
        * **Vencimiento original:** {vencimiento_orig.strftime('%d/%m/%Y')}
        * **Remanente congelado:** {remanente_str}
        * **Punto de reanudación:** {punto_reanuda.strftime('%d/%m/%Y') if punto_reanuda else 'N/A'}
        * **Vencimiento Final:** {vencimiento_final.strftime('%d/%m/%Y')}
        """)
