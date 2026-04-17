import streamlit as st
import holidays
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Configuración de página
st.set_page_config(page_title="Auditoría de Caducidad NRD", layout="centered")

# --- SIDEBAR DE IDENTIDAD ---
with st.sidebar:
    st.markdown("# ⚖️ RomoLegal")
    st.markdown("---")
    st.markdown("### **Developed by:**")
    st.write("Lorena Romo")
    st.write("---") # 

def obtener_siguiente_habil(fecha, festivos_co):
    while fecha.weekday() >= 5 or fecha in festivos_co:
        fecha += timedelta(days=1)
    return fecha

st.title("⚖️ Calculador de Caducidad (CPACA)")
st.subheader("Análisis de Nulidad y Restablecimiento del Derecho")

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
    
    # Suspensión CSJ
    usa_csj = st.checkbox("¿Hubo suspensión extraordinaria (CSJ/Paros)?")
    f_inicio_csj, f_fin_csj = None, None
    if usa_csj:
        c1, c2 = st.columns(2)
        f_inicio_csj = c1.date_input("Inicio Suspensión CSJ")
        f_fin_csj = c2.date_input("Levantamiento CSJ")

    # Conciliación
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
        # Convertir a datetime para lógica de relativedelta
        notif = datetime.combine(f_notif, datetime.min.time())
        demanda = datetime.combine(f_demanda, datetime.min.time())
        festivos = holidays.Colombia(years=range(notif.year, notif.year + 3))

        # Dies a quo
        f_inicio = notif + timedelta(days=2 if tipo_notif == "Aviso" else 1)
        vencimiento_orig = f_inicio + relativedelta(months=4)

        # Manejo de suspensiones
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

        vencimiento_final = obtener_siguiente_habil(vencimiento_final, festivos)

        # --- RESULTADOS ACTUALIZADOS ---
        st.divider()
        
        # 1. Control de Procedibilidad (Prioritario)
        if not usa_conc:
            st.error("### ESTADO: RECHAZO POR PROCEDIBILIDAD")
            st.warning("No presentó solicitud de conciliación: no puede acudir a la Jurisdicción Contencioso Administrativa (Art. 161 CPACA).")
        
        # 2. Control de Temporalidad (Caducidad)
        elif demanda > vencimiento_final:
            st.error("### ESTADO: CADUCADA")
        else:
            st.success("### ESTADO: OPORTUNA")
            
        # Siempre mostramos la sustentación para que el analista vea los términos
        st.info(f"""
        **Sustentación del Cálculo:**
        * **Inicio de conteo:** {f_inicio.strftime('%d/%m/%Y')}
        * **Vencimiento original:** {vencimiento_orig.strftime('%d/%m/%Y')}
        * **Remanente congelado:** {remanente_str}
        * **Punto de reanudación:** {punto_reanuda.strftime('%d/%m/%Y') if punto_reanuda else 'N/A'}
        * **Vencimiento Final:** {vencimiento_final.strftime('%d/%m/%Y')}
        """)
