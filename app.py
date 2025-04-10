import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import os
import base64

from data_manager import DataManager
from database import init_db
from utils import (
    crear_grafico_temperatura_humedad,
    crear_grafico_comparativo,
    crear_grafico_variacion,
    generar_reporte_estadistico
)

# Inicializar la base de datos
init_db()

# Configurar la página
st.set_page_config(
    page_title="Monitoreo de Aires Acondicionados",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Instanciar el gestor de datos
@st.cache_resource
def get_data_manager():
    dm = DataManager()
    # Crear usuario administrador por defecto si no existe ninguno
    dm.crear_admin_por_defecto()
    return dm

data_manager = get_data_manager()

# Configurar variables de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
    
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# Funciones para las páginas de autenticación
def mostrar_login():
    st.title("Iniciar Sesión")
    
    with st.form("login_form"):
        username = st.text_input("Usuario o Email")
        password = st.text_input("Contraseña", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Iniciar Sesión", use_container_width=True)
        
        with col2:
            if st.form_submit_button("Registrarse", use_container_width=True):
                st.session_state.show_page = "registro"
                st.rerun()
        
        if submit_button:
            if username and password:
                # Verificar credenciales
                usuario = data_manager.verificar_credenciales(username, password)
                
                if usuario:
                    # Guardar información de la sesión
                    st.session_state.logged_in = True
                    st.session_state.user_id = usuario.id
                    st.session_state.user_name = f"{usuario.nombre} {usuario.apellido}"
                    st.session_state.user_role = usuario.rol
                    st.session_state.show_page = "dashboard"
                    st.success(f"Bienvenido/a, {usuario.nombre}!")
                    st.rerun()
                else:
                    st.error("Credenciales inválidas. Por favor, intenta de nuevo.")
            else:
                st.error("Por favor, completa todos los campos.")

def mostrar_registro():
    st.title("Registro de Usuario")
    
    with st.form("registro_form"):
        nombre = st.text_input("Nombre")
        apellido = st.text_input("Apellido")
        email = st.text_input("Email")
        username = st.text_input("Nombre de Usuario")
        password = st.text_input("Contraseña", type="password")
        password_confirm = st.text_input("Confirmar Contraseña", type="password")
        
        # Sólo mostrar selección de rol si hay un administrador conectado
        rol = "operador"  # Rol por defecto
        if st.session_state.logged_in and st.session_state.user_role == "admin":
            roles = ["operador", "supervisor", "admin"]
            rol = st.selectbox("Rol", options=roles)
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Registrarse", use_container_width=True)
        
        with col2:
            if st.form_submit_button("Volver al inicio de sesión", use_container_width=True):
                st.session_state.show_page = "login"
                st.rerun()
        
        if submit_button:
            if nombre and apellido and email and username and password and password_confirm:
                if password != password_confirm:
                    st.error("Las contraseñas no coinciden.")
                else:
                    # Crear usuario
                    usuario_id = data_manager.crear_usuario(
                        nombre=nombre,
                        apellido=apellido,
                        email=email,
                        username=username,
                        password=password,
                        rol=rol
                    )
                    
                    if usuario_id:
                        st.success(f"Usuario registrado exitosamente! Ya puedes iniciar sesión.")
                        # Redirigir a login
                        st.session_state.show_page = "login"
                        st.rerun()
                    else:
                        st.error("No se pudo crear el usuario. El email o nombre de usuario ya están en uso.")
            else:
                st.error("Por favor, completa todos los campos.")

def mostrar_logout():
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# Inicializar estado de la página
if 'show_page' not in st.session_state:
    st.session_state.show_page = "login"

# Sidebar para navegación (mostrar solo si el usuario está autenticado)
if st.session_state.logged_in:
    st.sidebar.title("Monitoreo AC")
    
    # Mostrar información del usuario
    st.sidebar.write(f"Usuario: {st.session_state.user_name}")
    st.sidebar.write(f"Rol: {st.session_state.user_role}")
    
    # Opciones de navegación según el rol
    if st.session_state.user_role in ["admin", "supervisor"]:
        paginas = [
            "Dashboard",
            "Registro de Lecturas",
            "Gestión de Aires",
            "Registro de Mantenimientos",
            "Análisis y Estadísticas",
            "Configuración de Umbrales",
            "Gestión de Usuarios",
            "Exportar Datos"
        ]
    else:  # operador
        paginas = [
            "Dashboard",
            "Registro de Lecturas",
            "Análisis y Estadísticas"
        ]
    
    pagina_seleccionada = st.sidebar.radio("Navegar a:", paginas)
    
    # Opción para cerrar sesión
    mostrar_logout()
else:
    # Si el usuario no está autenticado, mostrar el formulario de login o registro
    if st.session_state.show_page == "login":
        mostrar_login()
        st.stop()  # Detener la ejecución aquí
    elif st.session_state.show_page == "registro":
        mostrar_registro()
        st.stop()  # Detener la ejecución aquí

# Función para mostrar el dashboard principal
def mostrar_dashboard():
    st.title("Dashboard de Monitoreo de Aires Acondicionados")
    
    # Obtener datos
    aires_df = data_manager.obtener_aires()
    lecturas_df = data_manager.obtener_lecturas()
    
    # Estadísticas generales
    stats = data_manager.obtener_estadisticas_generales()
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total de Aires", value=len(aires_df))
    
    with col2:
        st.metric(label="Total de Lecturas", value=stats['total_lecturas'])
    
    with col3:
        st.metric(
            label="Temperatura Promedio",
            value=f"{stats['temperatura']['promedio']} °C"
        )
    
    with col4:
        st.metric(
            label="Humedad Promedio",
            value=f"{stats['humedad']['promedio']} %"
        )
    
    # Filtros para gráficos
    st.subheader("Visualización de Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Opción para mostrar datos de todos los aires o uno específico
        aires_opciones = [("Todos los aires", None)] + [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
        
        aire_seleccionado_nombre, aire_seleccionado_id = aires_opciones[0]
        if len(aires_opciones) > 1:
            aire_seleccionado_nombre, aire_seleccionado_id = st.selectbox(
                "Seleccionar Aire Acondicionado:",
                options=aires_opciones,
                format_func=lambda x: x[0]
            )
    
    with col2:
        # Período de tiempo para visualizar
        periodo_options = {
            "Última semana": "semana",
            "Último mes": "mes",
            "Último año": "año",
            "Todo el tiempo": "todo"
        }
        periodo = st.selectbox(
            "Período de tiempo:",
            options=list(periodo_options.keys()),
            index=3
        )
        periodo_valor = periodo_options[periodo]
    
    # Preparar datos para gráficos
    if not lecturas_df.empty:
        # Si hay lecturas registradas
        fig_temp, fig_hum = crear_grafico_temperatura_humedad(
            lecturas_df, 
            aire_id=aire_seleccionado_id, 
            periodo=periodo_valor
        )
        
        # Mostrar gráficos
        st.plotly_chart(fig_temp, use_container_width=True)
        st.plotly_chart(fig_hum, use_container_width=True)
        
        # Mostrar gráficos comparativos
        st.subheader("Comparativa entre Aires Acondicionados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_comp_temp = crear_grafico_comparativo(lecturas_df, variable='temperatura')
            st.plotly_chart(fig_comp_temp, use_container_width=True)
        
        with col2:
            fig_comp_hum = crear_grafico_comparativo(lecturas_df, variable='humedad')
            st.plotly_chart(fig_comp_hum, use_container_width=True)
    else:
        # Si no hay lecturas registradas
        st.info("No hay lecturas registradas. Por favor, agrega lecturas para visualizar los gráficos.")

# Función para la página de registro de lecturas
def mostrar_registro_lecturas():
    st.title("Registro de Lecturas")
    
    # Obtener lista de aires acondicionados
    aires_df = data_manager.obtener_aires()
    
    if aires_df.empty:
        st.warning("No hay aires acondicionados registrados. Por favor, agrega un aire primero.")
        return
    
    # Crear tabs para organizar las diferentes funcionalidades
    tab1, tab2 = st.tabs(["Registrar Lecturas", "Administrar Lecturas"])
    
    with tab1:
        # Formulario para agregar lectura
        st.subheader("Nueva Lectura")
        
        with st.form("formulario_lectura", clear_on_submit=True):
            # Seleccionar aire acondicionado
            aire_options = [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
            aire_nombre, aire_id = st.selectbox(
                "Seleccionar Aire Acondicionado:",
                options=aire_options,
                format_func=lambda x: x[0]
            )
            
            # Fecha de la lectura
            fecha = st.date_input("Fecha de la lectura:", datetime.now())
            
            # Horarios predefinidos
            horas_predefinidas = {
                "2:00 AM": "02:00:00",
                "6:00 AM": "06:00:00",
                "9:00 AM": "09:00:00",
                "12:00 PM": "12:00:00",
                "3:00 PM": "15:00:00",
                "6:00 PM": "18:00:00",
                "10:00 PM": "22:00:00"
            }
            
            # Selección de hora
            hora_seleccionada = st.selectbox(
                "Hora de la lectura:",
                options=list(horas_predefinidas.keys())
            )
            
            # Valores de temperatura y humedad
            col1, col2 = st.columns(2)
            
            with col1:
                temperatura = st.number_input(
                    "Temperatura (°C):",
                    min_value=-10.0,
                    max_value=50.0,
                    value=25.0,
                    step=0.1
                )
            
            with col2:
                humedad = st.number_input(
                    "Humedad (%):",
                    min_value=0.0,
                    max_value=100.0,
                    value=50.0,
                    step=0.1
                )
            
            # Botón para enviar
            submitted = st.form_submit_button("Registrar Lectura", type="primary")
            
            if submitted:
                # Obtener la hora seleccionada
                hora_str = horas_predefinidas[hora_seleccionada]
                
                # Combinar fecha y hora para crear el datetime
                fecha_hora_str = f"{fecha.strftime('%Y-%m-%d')} {hora_str}"
                fecha_dt = pd.to_datetime(fecha_hora_str)
                
                # Agregar lectura
                lectura_id = data_manager.agregar_lectura(
                    aire_id,
                    fecha_dt,
                    temperatura,
                    humedad
                )
                
                st.success(f"Lectura registrada exitosamente con ID: {lectura_id}")
        
        # Mostrar últimas lecturas
        st.subheader("Últimas Lecturas Registradas")
        
        lecturas_df = data_manager.obtener_lecturas()
        
        if not lecturas_df.empty:
            # Ordenar por fecha (más recientes primero)
            lecturas_df = lecturas_df.sort_values(by='fecha', ascending=False)
            
            # Añadir información del nombre del aire
            lecturas_con_info = lecturas_df.merge(
                aires_df[['id', 'nombre']],
                left_on='aire_id',
                right_on='id',
                suffixes=('', '_aire')
            )
            
            # Seleccionar y renombrar columnas para mostrar
            lecturas_display = lecturas_con_info[['id', 'nombre', 'fecha', 'temperatura', 'humedad']].copy()
            
            # Formatear la fecha para incluir fecha y hora
            lecturas_display['fecha'] = lecturas_display['fecha'].dt.strftime('%Y-%m-%d %H:%M')
            
            lecturas_display.columns = ['ID Lectura', 'Aire', 'Fecha y Hora', 'Temperatura (°C)', 'Humedad (%)']
            
            # Mostrar tabla con las últimas 10 lecturas
            st.dataframe(lecturas_display.head(10), use_container_width=True)
        else:
            st.info("No hay lecturas registradas aún.")
    
    with tab2:
        st.subheader("Administrar Lecturas Existentes")
        
        # Filtro por aire acondicionado
        aire_filter_options = [("Todos los aires", None)] + [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
        col1, col2 = st.columns([3, 1])
        
        with col1:
            aire_filter_nombre, aire_filter_id = st.selectbox(
                "Filtrar por Aire Acondicionado:",
                options=aire_filter_options,
                format_func=lambda x: x[0],
                key="filtro_lecturas"
            )
        
        with col2:
            if st.button("Aplicar Filtro", use_container_width=True):
                st.rerun()
                
        # Mostrar lecturas según el filtro
        lecturas_df = data_manager.obtener_lecturas()
        
        if not lecturas_df.empty:
            # Filtrar por aire_id si se seleccionó uno
            if aire_filter_id is not None:
                lecturas_df = lecturas_df[lecturas_df['aire_id'] == aire_filter_id]
            
            # Ordenar por fecha (más recientes primero)
            lecturas_df = lecturas_df.sort_values(by='fecha', ascending=False)
            
            # Añadir información del nombre del aire
            lecturas_con_info = lecturas_df.merge(
                aires_df[['id', 'nombre']],
                left_on='aire_id',
                right_on='id',
                suffixes=('', '_aire')
            )
            
            # Seleccionar y renombrar columnas para mostrar
            lecturas_display = lecturas_con_info[['id', 'nombre', 'fecha', 'temperatura', 'humedad']].copy()
            
            # Formatear la fecha para incluir fecha y hora
            lecturas_display['fecha'] = lecturas_display['fecha'].dt.strftime('%Y-%m-%d %H:%M')
            
            lecturas_display.columns = ['ID Lectura', 'Aire', 'Fecha y Hora', 'Temperatura (°C)', 'Humedad (%)']
            
            if not lecturas_display.empty:
                # Mostrar todas las lecturas que cumplen con el filtro
                st.dataframe(lecturas_display, use_container_width=True)
                
                # Sección para eliminar lecturas
                st.subheader("Eliminar Lectura")
                
                # Crear opciones con detalles de cada lectura
                lectura_options = [(f"ID: {row['ID Lectura']} - {row['Aire']} ({row['Fecha y Hora']}): {row['Temperatura (°C)']}°C, {row['Humedad (%)']}%", 
                                 row['ID Lectura']) for _, row in lecturas_display.iterrows()]
                
                if lectura_options:
                    lectura_seleccionada_texto, lectura_seleccionada_id = st.selectbox(
                        "Seleccionar Lectura para eliminar:",
                        options=lectura_options,
                        format_func=lambda x: x[0]
                    )
                    
                    if st.button("Eliminar Lectura Seleccionada", type="primary"):
                        confirmacion = st.warning(f"¿Estás seguro de eliminar esta lectura? Esta acción no se puede deshacer.")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Sí, eliminar", key="confirmar_eliminar_lectura"):
                                eliminado = data_manager.eliminar_lectura(lectura_seleccionada_id)
                                if eliminado:
                                    st.success("Lectura eliminada exitosamente")
                                else:
                                    st.error("No se pudo eliminar la lectura")
                                st.rerun()
                        
                        with col2:
                            if st.button("Cancelar", key="cancelar_eliminar_lectura"):
                                st.rerun()
                else:
                    st.info("No hay lecturas para seleccionar")
            else:
                st.info(f"No hay lecturas registradas para el filtro seleccionado.")
        else:
            st.info("No hay lecturas registradas aún.")

# Función para la página de gestión de aires
def mostrar_gestion_aires():
    st.title("Gestión de Aires Acondicionados")
    
    # Tabs para organizar las diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["Registrar Aires", "Editar Aires", "Eliminar Aires"])
    
    with tab1:
        # Formulario para agregar nuevo aire
        st.subheader("Agregar Nuevo Aire Acondicionado")
        
        with st.form("formulario_aire", clear_on_submit=True):
            nombre = st.text_input("Nombre:", placeholder="Ej: Aire Oficina Principal")
            ubicacion = st.text_input("Ubicación:", placeholder="Ej: Planta 1, Sala 3")
            fecha_instalacion = st.date_input("Fecha de instalación:", datetime.now())
            
            # Botón para enviar
            submitted = st.form_submit_button("Agregar Aire", type="primary")
            
            if submitted:
                if nombre and ubicacion:
                    # Convertir fecha a string
                    fecha_str = fecha_instalacion.strftime('%Y-%m-%d')
                    
                    # Agregar aire
                    aire_id = data_manager.agregar_aire(
                        nombre,
                        ubicacion,
                        fecha_str
                    )
                    
                    st.success(f"Aire acondicionado agregado exitosamente con ID: {aire_id}")
                else:
                    st.error("Por favor, completa todos los campos.")
    
    # Obtener aires registrados
    aires_df = data_manager.obtener_aires()
    
    if not aires_df.empty:
        with tab1:
            # Mostrar aires registrados
            st.subheader("Aires Acondicionados Registrados")
            # Mostrar tabla con los aires
            st.dataframe(aires_df, use_container_width=True)
            
        with tab2:
            # Sección para editar aires acondicionados
            st.subheader("Editar Aire Acondicionado")
            
            # Crear opciones para selectbox con nombres e IDs
            aire_options = [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
            
            aire_seleccionado_nombre, aire_seleccionado_id = st.selectbox(
                "Seleccionar Aire Acondicionado a Editar:",
                options=aire_options,
                format_func=lambda x: x[0],
                key="editar_aire_select"
            )
            
            # Obtener datos actuales del aire seleccionado
            aire_actual = aires_df[aires_df['id'] == aire_seleccionado_id].iloc[0]
            
            with st.form("formulario_editar_aire"):
                nombre_edit = st.text_input("Nombre del Aire Acondicionado", 
                                           value=aire_actual['nombre'])
                ubicacion_edit = st.text_input("Ubicación", 
                                              value=aire_actual['ubicacion'])
                
                # Convertir la fecha de texto a objeto date si es necesario
                fecha_actual = aire_actual['fecha_instalacion']
                if isinstance(fecha_actual, str):
                    try:
                        fecha_obj = datetime.strptime(fecha_actual, "%Y-%m-%d").date()
                    except:
                        fecha_obj = datetime.now().date()
                else:
                    fecha_obj = datetime.now().date()
                
                fecha_instalacion_edit = st.date_input("Fecha de Instalación", 
                                                     value=fecha_obj)
                
                submit_edit_button = st.form_submit_button("Actualizar Aire Acondicionado", type="primary")
                
                if submit_edit_button:
                    if nombre_edit and ubicacion_edit:
                        # Formatear fecha
                        fecha_formateada = fecha_instalacion_edit.strftime("%Y-%m-%d")
                        
                        # Actualizar aire en la base de datos
                        actualizado = data_manager.actualizar_aire(
                            aire_seleccionado_id, 
                            nombre_edit, 
                            ubicacion_edit, 
                            fecha_formateada
                        )
                        
                        if actualizado:
                            st.success(f"Aire acondicionado actualizado exitosamente")
                            st.rerun()
                        else:
                            st.error("Error al actualizar el aire acondicionado")
                    else:
                        st.warning("Debes completar el nombre y la ubicación del aire acondicionado")
        
        with tab3:
            # Sección para eliminar aires acondicionados
            st.subheader("Eliminar Aire Acondicionado")
            
            # Crear opciones para selectbox con nombres e IDs
            aire_options = [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
            
            aire_a_eliminar_nombre, aire_a_eliminar_id = st.selectbox(
                "Seleccionar Aire para eliminar:",
                options=aire_options,
                format_func=lambda x: x[0],
                key="eliminar_aire_select"
            )
            
            if st.button("Eliminar Aire Seleccionado", type="primary"):
                confirmacion = st.warning(f"¿Estás seguro de eliminar '{aire_a_eliminar_nombre}'? Esta acción eliminará también todas sus lecturas asociadas.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Sí, eliminar", key="confirmar_eliminar"):
                        data_manager.eliminar_aire(aire_a_eliminar_id)
                        st.success(f"Aire acondicionado eliminado exitosamente")
                        st.rerun()
                
                with col2:
                    if st.button("Cancelar", key="cancelar_eliminar"):
                        st.rerun()
    else:
        with tab1:
            st.info("No hay aires acondicionados registrados aún.")
        with tab2:
            st.info("No hay aires acondicionados para editar.")
        with tab3:
            st.info("No hay aires acondicionados para eliminar.")

# Función para la página de registro de mantenimientos
def mostrar_registro_mantenimientos():
    st.title("Registro de Mantenimientos")
    
    # Obtener lista de aires acondicionados
    aires_df = data_manager.obtener_aires()
    
    if aires_df.empty:
        st.warning("No hay aires acondicionados registrados. Por favor, agrega un aire primero.")
        return
    
    # Dividir en pestañas
    tab1, tab2 = st.tabs(["Registrar Mantenimiento", "Ver Mantenimientos"])
    
    with tab1:
        # Formulario para agregar mantenimiento
        st.subheader("Nuevo Registro de Mantenimiento")
        
        with st.form("formulario_mantenimiento", clear_on_submit=True):
            # Seleccionar aire acondicionado
            aire_options = [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
            aire_nombre, aire_id = st.selectbox(
                "Seleccionar Aire Acondicionado:",
                options=aire_options,
                format_func=lambda x: x[0]
            )
            
            # Tipo de mantenimiento
            tipos_mantenimiento = [
                "Preventivo programado",
                "Correctivo",
                "Limpieza de filtros",
                "Recarga de refrigerante",
                "Revisión eléctrica",
                "Cambio de partes",
                "Otro"
            ]
            
            tipo_mantenimiento = st.selectbox(
                "Tipo de Mantenimiento:",
                options=tipos_mantenimiento
            )
            
            # Descripción del mantenimiento
            descripcion = st.text_area(
                "Descripción detallada:",
                placeholder="Describe el mantenimiento realizado, piezas cambiadas, observaciones, etc."
            )
            
            # Nombre del técnico
            tecnico = st.text_input(
                "Nombre del Técnico:",
                placeholder="Nombre y apellido del técnico que realizó el mantenimiento"
            )
            
            # Subir imagen o documento
            imagen_file = st.file_uploader(
                "Adjuntar imagen o documento (opcional):",
                type=["jpg", "jpeg", "png", "pdf"]
            )
            
            # Botón para enviar
            submitted = st.form_submit_button("Registrar Mantenimiento")
            
            if submitted:
                if tipo_mantenimiento and descripcion and tecnico:
                    # Agregar mantenimiento
                    try:
                        mantenimiento_id = data_manager.agregar_mantenimiento(
                            aire_id,
                            tipo_mantenimiento,
                            descripcion,
                            tecnico,
                            imagen_file
                        )
                        
                        st.success(f"Mantenimiento registrado exitosamente con ID: {mantenimiento_id}")
                    except Exception as e:
                        st.error(f"Error al registrar el mantenimiento: {str(e)}")
                else:
                    st.error("Por favor, completa todos los campos obligatorios.")
    
    with tab2:
        st.subheader("Historial de Mantenimientos")
        
        # Filtro por aire
        col1, col2 = st.columns([3, 1])
        
        with col1:
            aire_filter_options = [("Todos los aires", None)] + [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
            
            aire_filter_nombre, aire_filter_id = st.selectbox(
                "Filtrar por Aire:",
                options=aire_filter_options,
                format_func=lambda x: x[0]
            )
        
        with col2:
            if st.button("Aplicar Filtro", use_container_width=True):
                st.rerun()
        
        # Obtener mantenimientos
        mantenimientos_df = data_manager.obtener_mantenimientos(aire_id=aire_filter_id)
        
        if not mantenimientos_df.empty:
            # Añadir información del nombre del aire
            mantenimientos_con_info = mantenimientos_df.merge(
                aires_df[['id', 'nombre']],
                left_on='aire_id',
                right_on='id',
                suffixes=('', '_aire')
            )
            
            # Formatear la fecha
            mantenimientos_con_info['fecha'] = pd.to_datetime(mantenimientos_con_info['fecha']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Seleccionar y renombrar columnas para mostrar
            mantenimientos_display = mantenimientos_con_info[[
                'id', 'nombre', 'fecha', 'tipo_mantenimiento', 'tecnico', 'tiene_imagen'
            ]].copy()
            
            mantenimientos_display.columns = [
                'ID', 'Aire', 'Fecha', 'Tipo', 'Técnico', 'Tiene Imagen'
            ]
            
            # Mostrar tabla con mantenimientos
            st.dataframe(mantenimientos_display, use_container_width=True)
            
            # Sección para ver detalles de un mantenimiento
            st.subheader("Detalles de Mantenimiento")
            
            mantenimiento_options = [(f"ID: {row['ID']} - {row['Tipo']} ({row['Fecha']})", row['ID']) for _, row in mantenimientos_display.iterrows()]
            
            if mantenimiento_options:
                mantenimiento_seleccionado_texto, mantenimiento_seleccionado_id = st.selectbox(
                    "Seleccionar Mantenimiento para ver detalles:",
                    options=mantenimiento_options,
                    format_func=lambda x: x[0]
                )
                
                # Obtener detalles del mantenimiento seleccionado
                mantenimiento = data_manager.obtener_mantenimiento_por_id(mantenimiento_seleccionado_id)
                
                if mantenimiento:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Aire:** {aires_df[aires_df['id'] == mantenimiento.aire_id]['nombre'].values[0]}")
                        st.write(f"**Fecha:** {mantenimiento.fecha.strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Tipo:** {mantenimiento.tipo_mantenimiento}")
                        st.write(f"**Técnico:** {mantenimiento.tecnico}")
                    
                    st.write("**Descripción:**")
                    st.write(mantenimiento.descripcion)
                    
                    # Mostrar imagen si existe
                    if mantenimiento.imagen_datos:
                        st.write("**Imagen adjunta:**")
                        imagen_b64 = mantenimiento.get_imagen_base64()
                        if imagen_b64:
                            st.image(imagen_b64, caption=mantenimiento.imagen_nombre)
                    
                    # Botón para eliminar mantenimiento
                    if st.button("Eliminar este mantenimiento", type="primary"):
                        confirmacion = st.warning(f"¿Estás seguro de eliminar este registro de mantenimiento? Esta acción no se puede deshacer.")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Sí, eliminar", key="confirmar_eliminar_mant"):
                                eliminado = data_manager.eliminar_mantenimiento(mantenimiento_seleccionado_id)
                                if eliminado:
                                    st.success("Mantenimiento eliminado exitosamente")
                                else:
                                    st.error("No se pudo eliminar el mantenimiento")
                                st.rerun()
                        
                        with col2:
                            if st.button("Cancelar", key="cancelar_eliminar_mant"):
                                st.rerun()
            else:
                st.info("No hay mantenimientos para seleccionar")
        else:
            st.info("No hay mantenimientos registrados aún.")

# Función para la página de análisis y estadísticas
def mostrar_analisis_estadisticas():
    st.title("Análisis y Estadísticas")
    
    # Obtener datos
    aires_df = data_manager.obtener_aires()
    lecturas_df = data_manager.obtener_lecturas()
    
    if aires_df.empty or lecturas_df.empty:
        st.warning("No hay suficientes datos para generar estadísticas. Asegúrate de tener aires acondicionados y lecturas registradas.")
        return
    
    # Opciones de análisis
    analisis_options = [
        "Estadísticas Generales",
        "Análisis por Ubicación",
        "Variabilidad de Temperatura",
        "Variabilidad de Humedad",
        "Reporte Completo"
    ]
    
    analisis_seleccionado = st.radio(
        "Selecciona el tipo de análisis:",
        options=analisis_options
    )
    
    if analisis_seleccionado == "Estadísticas Generales":
        # Mostrar estadísticas generales
        st.subheader("Estadísticas Generales por Aire Acondicionado")
        
        # Seleccionar aire acondicionado
        aire_options = [("Todos los aires", None)] + [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
        
        aire_seleccionado_nombre, aire_seleccionado_id = st.selectbox(
            "Seleccionar Aire Acondicionado:",
            options=aire_options,
            format_func=lambda x: x[0]
        )
        
        if aire_seleccionado_id is None:
            # Estadísticas para todos los aires
            stats_df = generar_reporte_estadistico(lecturas_df)
            
            # Añadir nombres de los aires
            stats_df = stats_df.merge(
                aires_df[['id', 'nombre']],
                left_on='aire_id',
                right_on='id',
                how='left'
            )
            
            # Seleccionar y renombrar columnas para mostrar
            stats_display = stats_df[[
                'nombre',
                'temperatura_promedio',
                'temperatura_min',
                'temperatura_max',
                'temperatura_std',
                'humedad_promedio',
                'humedad_min',
                'humedad_max',
                'humedad_std',
                'lecturas_totales'
            ]].copy()
            
            stats_display.columns = [
                'Aire',
                'Temp. Promedio (°C)',
                'Temp. Mínima (°C)',
                'Temp. Máxima (°C)',
                'Temp. Desv. Estándar',
                'Humedad Promedio (%)',
                'Humedad Mínima (%)',
                'Humedad Máxima (%)',
                'Humedad Desv. Estándar',
                'Total Lecturas'
            ]
            
            st.dataframe(stats_display, use_container_width=True)
        else:
            # Estadísticas para un aire específico
            lecturas_aire = data_manager.obtener_lecturas_por_aire(aire_seleccionado_id)
            
            if lecturas_aire.empty:
                st.info(f"No hay lecturas registradas para {aire_seleccionado_nombre}.")
                return
            
            stats = data_manager.obtener_estadisticas_por_aire(aire_seleccionado_id)
            
            # Mostrar estadísticas en tarjetas
            st.subheader(f"Estadísticas para {aire_seleccionado_nombre}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Temperatura")
                col1a, col1b, col1c, col1d = st.columns(4)
                
                with col1a:
                    st.metric("Promedio", f"{stats['temperatura']['promedio']} °C")
                
                with col1b:
                    st.metric("Mínima", f"{stats['temperatura']['minimo']} °C")
                
                with col1c:
                    st.metric("Máxima", f"{stats['temperatura']['maximo']} °C")
                
                with col1d:
                    st.metric("Desviación", f"{stats['temperatura']['desviacion']} °C")
            
            with col2:
                st.write("### Humedad")
                col2a, col2b, col2c, col2d = st.columns(4)
                
                with col2a:
                    st.metric("Promedio", f"{stats['humedad']['promedio']} %")
                
                with col2b:
                    st.metric("Mínima", f"{stats['humedad']['minimo']} %")
                
                with col2c:
                    st.metric("Máxima", f"{stats['humedad']['maximo']} %")
                
                with col2d:
                    st.metric("Desviación", f"{stats['humedad']['desviacion']} %")
            
            # Mostrar gráficos de temperatura y humedad
            fig_temp, fig_hum = crear_grafico_temperatura_humedad(
                lecturas_aire, 
                aire_id=aire_seleccionado_id, 
                periodo='todo'
            )
            
            st.plotly_chart(fig_temp, use_container_width=True)
            st.plotly_chart(fig_hum, use_container_width=True)
    
    elif analisis_seleccionado == "Análisis por Ubicación":
        # Mostrar análisis por ubicación
        st.subheader("Análisis por Ubicación")
        
        # Obtener estadísticas por ubicación
        stats_ubicacion_df = data_manager.obtener_estadisticas_por_ubicacion()
        
        if stats_ubicacion_df.empty:
            st.info("No hay suficientes datos para generar estadísticas por ubicación. Asegúrate de tener aires acondicionados en diferentes ubicaciones con lecturas registradas.")
            return
        
        # Mostrar tabla de estadísticas por ubicación
        st.write("### Comparativa entre Ubicaciones")
        
        # Renombrar columnas para mostrar
        stats_display = stats_ubicacion_df[[
            'ubicacion',
            'num_aires',
            'temperatura_promedio',
            'temperatura_min',
            'temperatura_max',
            'temperatura_std',
            'humedad_promedio',
            'humedad_min',
            'humedad_max',
            'humedad_std',
            'lecturas_totales'
        ]].copy()
        
        stats_display.columns = [
            'Ubicación',
            'Nº Aires',
            'Temp. Promedio (°C)',
            'Temp. Mínima (°C)',
            'Temp. Máxima (°C)',
            'Temp. Desv. Estándar',
            'Humedad Promedio (%)',
            'Humedad Mínima (%)',
            'Humedad Máxima (%)',
            'Humedad Desv. Estándar',
            'Total Lecturas'
        ]
        
        st.dataframe(stats_display, use_container_width=True)
        
        # Crear gráficos comparativos entre ubicaciones
        st.write("### Gráficos Comparativos por Ubicación")
        
        # Gráfico de temperaturas promedio por ubicación
        fig_temp_ubicacion = px.bar(
            stats_ubicacion_df, 
            x='ubicacion', 
            y='temperatura_promedio',
            error_y='temperatura_std',
            title='Temperatura Promedio por Ubicación',
            labels={'ubicacion': 'Ubicación', 'temperatura_promedio': 'Temperatura Promedio (°C)'},
            color='ubicacion',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        
        # Personalizar el diseño
        fig_temp_ubicacion.update_layout(
            xaxis_title="Ubicación",
            yaxis_title="Temperatura (°C)",
            legend_title="Ubicación",
            height=500
        )
        
        st.plotly_chart(fig_temp_ubicacion, use_container_width=True)
        
        # Gráfico de humedad promedio por ubicación
        fig_hum_ubicacion = px.bar(
            stats_ubicacion_df, 
            x='ubicacion', 
            y='humedad_promedio',
            error_y='humedad_std',
            title='Humedad Promedio por Ubicación',
            labels={'ubicacion': 'Ubicación', 'humedad_promedio': 'Humedad Promedio (%)'},
            color='ubicacion',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        
        # Personalizar el diseño
        fig_hum_ubicacion.update_layout(
            xaxis_title="Ubicación",
            yaxis_title="Humedad (%)",
            legend_title="Ubicación",
            height=500
        )
        
        st.plotly_chart(fig_hum_ubicacion, use_container_width=True)
        
        # Seleccionar ubicación específica para análisis detallado
        st.subheader("Análisis Detallado por Ubicación")
        
        # Obtener todas las ubicaciones
        ubicaciones = data_manager.obtener_ubicaciones()
        
        if ubicaciones:
            ubicacion_seleccionada = st.selectbox(
                "Seleccionar Ubicación:",
                options=ubicaciones
            )
            
            # Obtener aires en esta ubicación
            aires_ubicacion_df = data_manager.obtener_aires_por_ubicacion(ubicacion_seleccionada)
            
            if not aires_ubicacion_df.empty:
                st.write(f"### Aires Acondicionados en {ubicacion_seleccionada}")
                st.dataframe(aires_ubicacion_df, use_container_width=True)
                
                # Obtener estadísticas específicas de esta ubicación
                ubicacion_stats = data_manager.obtener_estadisticas_por_ubicacion(ubicacion_seleccionada).iloc[0] if not data_manager.obtener_estadisticas_por_ubicacion(ubicacion_seleccionada).empty else None
                
                if ubicacion_stats is not None:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("### Temperatura")
                        st.metric("Promedio", f"{ubicacion_stats['temperatura_promedio']} °C")
                        st.metric("Desviación Estándar", f"{ubicacion_stats['temperatura_std']} °C")
                        st.metric("Rango", f"{ubicacion_stats['temperatura_min']} - {ubicacion_stats['temperatura_max']} °C")
                    
                    with col2:
                        st.write("### Humedad")
                        st.metric("Promedio", f"{ubicacion_stats['humedad_promedio']} %")
                        st.metric("Desviación Estándar", f"{ubicacion_stats['humedad_std']} %")
                        st.metric("Rango", f"{ubicacion_stats['humedad_min']} - {ubicacion_stats['humedad_max']} %")
            else:
                st.info(f"No hay aires acondicionados registrados en la ubicación {ubicacion_seleccionada}")
        else:
            st.info("No hay ubicaciones registradas")
        
        # Información adicional
        st.write("""
        **Nota sobre el análisis por ubicación:**
        
        - Este análisis ayuda a identificar patrones y diferencias entre distintas áreas o zonas donde están instalados los aires acondicionados.
        - Una diferencia significativa en las temperaturas o humedades promedio entre ubicaciones puede indicar:
            - Diferencias en la eficiencia de los equipos
            - Variaciones en la carga térmica de cada zona
            - Posibles problemas de instalación o mantenimiento en ubicaciones específicas
        - La desviación estándar alta en una ubicación específica puede indicar condiciones variables o inconsistentes.
        """)

    elif analisis_seleccionado == "Variabilidad de Temperatura":
        # Mostrar análisis de variabilidad de temperatura
        st.subheader("Análisis de Variabilidad de Temperatura")
        
        # Seleccionar aire acondicionado
        aire_options = [("Todos los aires", None)] + [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
        
        aire_seleccionado_nombre, aire_seleccionado_id = st.selectbox(
            "Seleccionar Aire Acondicionado:",
            options=aire_options,
            format_func=lambda x: x[0]
        )
        
        # Crear gráfico de variabilidad
        fig_var = crear_grafico_variacion(lecturas_df, aire_seleccionado_id, 'temperatura')
        st.plotly_chart(fig_var, use_container_width=True)
        
        # Explicación
        st.write("""
        **Interpretación:**
        
        - El gráfico muestra la desviación estándar de la temperatura, que indica qué tan dispersas están las lecturas.
        - Una mayor desviación estándar significa mayor variabilidad en las lecturas.
        - La línea roja muestra el promedio de temperatura.
        - Si la variabilidad es alta, podría indicar problemas con el aire acondicionado o influencias externas significativas.
        """)
    
    elif analisis_seleccionado == "Variabilidad de Humedad":
        # Mostrar análisis de variabilidad de humedad
        st.subheader("Análisis de Variabilidad de Humedad")
        
        # Seleccionar aire acondicionado
        aire_options = [("Todos los aires", None)] + [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
        
        aire_seleccionado_nombre, aire_seleccionado_id = st.selectbox(
            "Seleccionar Aire Acondicionado:",
            options=aire_options,
            format_func=lambda x: x[0]
        )
        
        # Crear gráfico de variabilidad
        fig_var = crear_grafico_variacion(lecturas_df, aire_seleccionado_id, 'humedad')
        st.plotly_chart(fig_var, use_container_width=True)
        
        # Explicación
        st.write("""
        **Interpretación:**
        
        - El gráfico muestra la desviación estándar de la humedad, que indica qué tan dispersas están las lecturas.
        - Una mayor desviación estándar significa mayor variabilidad en las lecturas.
        - La línea roja muestra el promedio de humedad.
        - La variabilidad de la humedad puede verse afectada por factores externos como la ventilación o la ocupación del espacio.
        """)
    
    elif analisis_seleccionado == "Reporte Completo":
        # Generar reporte completo
        st.subheader("Reporte Estadístico Completo")
        
        # Generar y mostrar el reporte
        stats_df = generar_reporte_estadistico(lecturas_df)
        
        # Añadir nombres de los aires
        stats_df = stats_df.merge(
            aires_df[['id', 'nombre']],
            left_on='aire_id',
            right_on='id',
            how='left'
        )
        
        # Seleccionar y renombrar columnas para mostrar
        stats_display = stats_df[[
            'nombre',
            'temperatura_promedio',
            'temperatura_min',
            'temperatura_max',
            'temperatura_std',
            'humedad_promedio',
            'humedad_min',
            'humedad_max',
            'humedad_std',
            'lecturas_totales'
        ]].copy()
        
        stats_display.columns = [
            'Aire',
            'Temp. Promedio (°C)',
            'Temp. Mínima (°C)',
            'Temp. Máxima (°C)',
            'Temp. Desv. Estándar',
            'Humedad Promedio (%)',
            'Humedad Mínima (%)',
            'Humedad Máxima (%)',
            'Humedad Desv. Estándar',
            'Total Lecturas'
        ]
        
        st.dataframe(stats_display, use_container_width=True)
        
        # Gráficos comparativos
        st.subheader("Comparativa de Temperatura entre Aires")
        fig_comp_temp = crear_grafico_comparativo(lecturas_df, variable='temperatura')
        st.plotly_chart(fig_comp_temp, use_container_width=True)
        
        st.subheader("Comparativa de Humedad entre Aires")
        fig_comp_hum = crear_grafico_comparativo(lecturas_df, variable='humedad')
        st.plotly_chart(fig_comp_hum, use_container_width=True)
        
        # Análisis de tendencias
        st.subheader("Tendencias a lo largo del tiempo")
        
        if not lecturas_df.empty:
            # Crear gráficos generales de tendencia
            fig_temp, fig_hum = crear_grafico_temperatura_humedad(lecturas_df, periodo='todo')
            
            st.plotly_chart(fig_temp, use_container_width=True)
            st.plotly_chart(fig_hum, use_container_width=True)
        else:
            st.info("No hay suficientes datos para mostrar tendencias temporales.")

# Función para la página de configuración de umbrales
def mostrar_configuracion_umbrales():
    st.title("Configuración de Umbrales de Temperatura y Humedad")
    
    # Obtener datos
    aires_df = data_manager.obtener_aires()
    
    # Crear tabs para organizar las diferentes funcionalidades
    tab1, tab2 = st.tabs(["Configurar Umbrales", "Administrar Umbrales"])
    
    with tab1:
        st.subheader("Crear Nueva Configuración de Umbrales")
        
        with st.form("formulario_umbral", clear_on_submit=True):
            # Información general
            nombre = st.text_input("Nombre de la configuración:", 
                                  placeholder="Ej: Umbrales Estándar Verano")
            
            # Tipo de configuración (global o específica)
            tipo_config = st.radio(
                "Tipo de Configuración:",
                options=["Global (aplica a todos los aires)", "Específica (solo para un aire)"],
                index=0
            )
            
            es_global = tipo_config == "Global (aplica a todos los aires)"
            
            # Si es específica, mostrar selector de aire
            aire_id = None
            if not es_global:
                if not aires_df.empty:
                    aire_options = [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
                    aire_nombre, aire_id = st.selectbox(
                        "Seleccionar Aire Acondicionado:",
                        options=aire_options,
                        format_func=lambda x: x[0]
                    )
                else:
                    st.warning("No hay aires acondicionados registrados para configurar umbrales específicos.")
                    st.stop()
            
            # Configuración de umbrales
            st.subheader("Umbrales de Temperatura")
            col1, col2 = st.columns(2)
            
            with col1:
                temp_min = st.number_input(
                    "Temperatura Mínima (°C):",
                    min_value=-10.0,
                    max_value=40.0,
                    value=18.0,
                    step=0.5
                )
            
            with col2:
                temp_max = st.number_input(
                    "Temperatura Máxima (°C):",
                    min_value=0.0,
                    max_value=50.0,
                    value=24.0,
                    step=0.5
                )
            
            st.subheader("Umbrales de Humedad")
            col1, col2 = st.columns(2)
            
            with col1:
                hum_min = st.number_input(
                    "Humedad Mínima (%):",
                    min_value=0.0,
                    max_value=100.0,
                    value=30.0,
                    step=5.0
                )
            
            with col2:
                hum_max = st.number_input(
                    "Humedad Máxima (%):",
                    min_value=0.0,
                    max_value=100.0,
                    value=70.0,
                    step=5.0
                )
            
            # Configuración de notificaciones
            notificar_activo = st.checkbox("Activar notificaciones para estos umbrales", value=True)
            
            # Validaciones básicas
            if temp_min >= temp_max:
                st.warning("La temperatura mínima debe ser menor que la máxima.")
            
            if hum_min >= hum_max:
                st.warning("La humedad mínima debe ser menor que la máxima.")
            
            # Botón para enviar
            submit_button = st.form_submit_button("Guardar Configuración", type="primary")
            
            if submit_button:
                if nombre:
                    if temp_min < temp_max and hum_min < hum_max:
                        # Crear la configuración
                        umbral_id = data_manager.crear_umbral_configuracion(
                            nombre=nombre,
                            es_global=es_global,
                            temp_min=temp_min,
                            temp_max=temp_max,
                            hum_min=hum_min,
                            hum_max=hum_max,
                            aire_id=None if es_global else aire_id,
                            notificar_activo=notificar_activo
                        )
                        
                        if umbral_id:
                            st.success(f"Configuración de umbrales creada exitosamente con ID: {umbral_id}")
                        else:
                            st.error("No se pudo crear la configuración de umbrales. Verifica los valores.")
                    else:
                        st.error("Los valores mínimos deben ser menores que los máximos.")
                else:
                    st.error("Por favor, ingresa un nombre para la configuración.")
    
    with tab2:
        st.subheader("Administrar Configuraciones de Umbrales")
        
        # Filtros para mostrar configuraciones
        col1, col2 = st.columns(2)
        
        with col1:
            mostrar_globales = st.checkbox("Mostrar configuraciones globales", value=True)
        
        with col2:
            aire_filtro = None
            mostrar_especificas = st.checkbox("Mostrar configuraciones específicas", value=True)
            
            if mostrar_especificas and not aires_df.empty:
                aire_filter_options = [("Todos los aires", None)] + [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
                
                aire_filtro_nombre, aire_filtro = st.selectbox(
                    "Filtrar por Aire Acondicionado:",
                    options=aire_filter_options,
                    format_func=lambda x: x[0]
                )
        
        # Obtener configuraciones según los filtros
        if mostrar_globales and not mostrar_especificas:
            umbrales_df = data_manager.obtener_umbrales_configuracion(solo_globales=True)
        elif not mostrar_globales and mostrar_especificas:
            umbrales_df = data_manager.obtener_umbrales_configuracion(aire_id=aire_filtro, solo_globales=False)
            # Filtrar solo las no globales
            if not umbrales_df.empty:
                umbrales_df = umbrales_df[~umbrales_df['es_global']]
        else:
            # Mostrar ambas
            umbrales_df = data_manager.obtener_umbrales_configuracion(aire_id=aire_filtro)
        
        # Mostrar tabla de configuraciones
        if not umbrales_df.empty:
            # Preparar DataFrame para mostrar
            umbrales_display = umbrales_df.copy()
            
            # Añadir columna descriptiva del tipo
            umbrales_display['tipo'] = umbrales_display['es_global'].apply(
                lambda x: "Global" if x else "Específico"
            )
            
            # Formatear fechas
            if 'fecha_creacion' in umbrales_display.columns:
                umbrales_display['fecha_creacion'] = pd.to_datetime(umbrales_display['fecha_creacion']).dt.strftime('%Y-%m-%d %H:%M')
            
            if 'ultima_modificacion' in umbrales_display.columns:
                umbrales_display['ultima_modificacion'] = pd.to_datetime(umbrales_display['ultima_modificacion']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Seleccionar y renombrar columnas para mostrar
            cols_display = ['id', 'nombre', 'tipo', 'aire_nombre' if 'aire_nombre' in umbrales_display.columns else 'aire_id',
                           'temp_min', 'temp_max', 'hum_min', 'hum_max', 'notificar_activo', 'fecha_creacion']
            
            # Filtrar solo las columnas que existen
            cols_display = [col for col in cols_display if col in umbrales_display.columns]
            
            # Crear el DataFrame a mostrar
            umbrales_show = umbrales_display[cols_display].copy()
            
            # Renombrar columnas
            column_rename = {
                'id': 'ID',
                'nombre': 'Nombre',
                'tipo': 'Tipo',
                'aire_id': 'ID Aire',
                'aire_nombre': 'Aire',
                'temp_min': 'Temp. Min (°C)',
                'temp_max': 'Temp. Max (°C)',
                'hum_min': 'Hum. Min (%)',
                'hum_max': 'Hum. Max (%)',
                'notificar_activo': 'Notificaciones',
                'fecha_creacion': 'Creación'
            }
            
            # Aplicar solo los renombres para columnas presentes
            rename_dict = {k: v for k, v in column_rename.items() if k in umbrales_show.columns}
            umbrales_show.rename(columns=rename_dict, inplace=True)
            
            # Mostrar la tabla
            st.dataframe(umbrales_show, use_container_width=True)
            
            # Sección para editar configuraciones
            st.subheader("Editar Configuración")
            
            # Crear opciones con detalles de cada configuración
            umbral_options = []
            for _, row in umbrales_df.iterrows():
                if row['es_global']:
                    desc = f"ID: {row['id']} - {row['nombre']} (Global)"
                else:
                    aire_desc = row.get('aire_nombre', f"Aire ID: {row['aire_id']}")
                    desc = f"ID: {row['id']} - {row['nombre']} ({aire_desc})"
                
                umbral_options.append((desc, row['id']))
            
            if umbral_options:
                umbral_seleccionado_texto, umbral_seleccionado_id = st.selectbox(
                    "Seleccionar Configuración a Editar:",
                    options=umbral_options,
                    format_func=lambda x: x[0]
                )
                
                # Obtener la configuración seleccionada
                umbral = data_manager.obtener_umbral_por_id(umbral_seleccionado_id)
                
                if umbral:
                    with st.form("formulario_editar_umbral"):
                        st.subheader(f"Editar: {umbral.nombre}")
                        
                        # Campo para editar nombre
                        nombre_edit = st.text_input("Nombre:", value=umbral.nombre)
                        
                        # No se puede cambiar si es global o a qué aire aplica
                        if umbral.es_global:
                            st.info("Esta es una configuración global que aplica a todos los aires acondicionados.")
                        else:
                            aire_info = aires_df[aires_df['id'] == umbral.aire_id]
                            if not aire_info.empty:
                                st.info(f"Esta configuración aplica al aire: {aire_info.iloc[0]['nombre']}")
                            else:
                                st.warning(f"Esta configuración aplica a un aire con ID {umbral.aire_id} que ya no existe.")
                        
                        # Umbrales de temperatura
                        st.subheader("Umbrales de Temperatura")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            temp_min_edit = st.number_input(
                                "Temperatura Mínima (°C):",
                                min_value=-10.0,
                                max_value=40.0,
                                value=float(umbral.temp_min),
                                step=0.5,
                                key="temp_min_edit"
                            )
                        
                        with col2:
                            temp_max_edit = st.number_input(
                                "Temperatura Máxima (°C):",
                                min_value=0.0,
                                max_value=50.0,
                                value=float(umbral.temp_max),
                                step=0.5,
                                key="temp_max_edit"
                            )
                        
                        # Umbrales de humedad
                        st.subheader("Umbrales de Humedad")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            hum_min_edit = st.number_input(
                                "Humedad Mínima (%):",
                                min_value=0.0,
                                max_value=100.0,
                                value=float(umbral.hum_min),
                                step=5.0,
                                key="hum_min_edit"
                            )
                        
                        with col2:
                            hum_max_edit = st.number_input(
                                "Humedad Máxima (%):",
                                min_value=0.0,
                                max_value=100.0,
                                value=float(umbral.hum_max),
                                step=5.0,
                                key="hum_max_edit"
                            )
                        
                        # Configuración de notificaciones
                        notificar_activo_edit = st.checkbox(
                            "Activar notificaciones para estos umbrales", 
                            value=umbral.notificar_activo,
                            key="notificar_edit"
                        )
                        
                        # Validaciones básicas
                        if temp_min_edit >= temp_max_edit:
                            st.warning("La temperatura mínima debe ser menor que la máxima.")
                        
                        if hum_min_edit >= hum_max_edit:
                            st.warning("La humedad mínima debe ser menor que la máxima.")
                        
                        # Botón para actualizar
                        submit_edit_button = st.form_submit_button("Actualizar Configuración", type="primary")
                        
                        if submit_edit_button:
                            if nombre_edit:
                                if temp_min_edit < temp_max_edit and hum_min_edit < hum_max_edit:
                                    # Actualizar la configuración
                                    actualizado = data_manager.actualizar_umbral_configuracion(
                                        umbral_id=umbral_seleccionado_id,
                                        nombre=nombre_edit,
                                        temp_min=temp_min_edit,
                                        temp_max=temp_max_edit,
                                        hum_min=hum_min_edit,
                                        hum_max=hum_max_edit,
                                        notificar_activo=notificar_activo_edit
                                    )
                                    
                                    if actualizado:
                                        st.success("Configuración actualizada exitosamente")
                                        st.rerun()
                                    else:
                                        st.error("No se pudo actualizar la configuración. Verifica los valores.")
                                else:
                                    st.error("Los valores mínimos deben ser menores que los máximos.")
                            else:
                                st.error("Por favor, ingresa un nombre para la configuración.")
                else:
                    st.error("No se pudo encontrar la configuración seleccionada.")
                    
                # Sección para eliminar configuración
                st.subheader("Eliminar Configuración")
                
                if st.button("Eliminar Configuración Seleccionada", type="primary"):
                    confirmacion = st.warning(f"¿Estás seguro de eliminar esta configuración? Esta acción no se puede deshacer.")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Sí, eliminar", key="confirmar_eliminar_umbral"):
                            eliminado = data_manager.eliminar_umbral_configuracion(umbral_seleccionado_id)
                            if eliminado:
                                st.success("Configuración eliminada exitosamente")
                            else:
                                st.error("No se pudo eliminar la configuración")
                            st.rerun()
                    
                    with col2:
                        if st.button("Cancelar", key="cancelar_eliminar_umbral"):
                            st.rerun()
            else:
                st.info("No hay configuraciones para editar.")
        else:
            st.info("No hay configuraciones de umbrales registradas que cumplan con los filtros seleccionados.")
            
        # Botón para actualizar vista
        if st.button("Actualizar Lista"):
            st.rerun()

# Función para la página de gestión de usuarios
def mostrar_gestion_usuarios():
    st.title("Gestión de Usuarios")
    
    # Verificar que sea un administrador
    if st.session_state.user_role != "admin":
        st.warning("No tienes permiso para acceder a esta página.")
        return
    
    # Crear tabs para organizar las diferentes funcionalidades
    tab1, tab2 = st.tabs(["Usuarios", "Crear Usuario"])
    
    with tab1:
        st.subheader("Usuarios Registrados")
        
        # Obtener todos los usuarios
        usuarios_df = data_manager.obtener_usuarios(solo_activos=False)
        
        if not usuarios_df.empty:
            # Formatear fechas
            if 'fecha_registro' in usuarios_df.columns:
                usuarios_df['fecha_registro'] = pd.to_datetime(usuarios_df['fecha_registro']).dt.strftime('%Y-%m-%d %H:%M')
            
            if 'ultima_conexion' in usuarios_df.columns and usuarios_df['ultima_conexion'].notnull().any():
                usuarios_df['ultima_conexion'] = pd.to_datetime(usuarios_df['ultima_conexion']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Mostrar tabla de usuarios
            st.dataframe(usuarios_df, use_container_width=True)
            
            # Sección para editar usuario
            st.subheader("Editar Usuario")
            
            # Crear opciones con detalles de cada usuario
            usuario_options = [(f"{row['username']} - {row['nombre']} {row['apellido']} ({row['rol']})", row['id']) 
                              for _, row in usuarios_df.iterrows()]
            
            if usuario_options:
                usuario_seleccionado_texto, usuario_seleccionado_id = st.selectbox(
                    "Seleccionar Usuario a Editar:",
                    options=usuario_options,
                    format_func=lambda x: x[0]
                )
                
                # Obtener el usuario seleccionado
                usuario_row = usuarios_df[usuarios_df['id'] == usuario_seleccionado_id].iloc[0]
                
                with st.form("formulario_editar_usuario"):
                    nombre_edit = st.text_input("Nombre:", value=usuario_row['nombre'])
                    apellido_edit = st.text_input("Apellido:", value=usuario_row['apellido'])
                    email_edit = st.text_input("Email:", value=usuario_row['email'])
                    rol_edit = st.selectbox("Rol:", options=["operador", "supervisor", "admin"], index=["operador", "supervisor", "admin"].index(usuario_row['rol']))
                    activo_edit = st.checkbox("Usuario Activo", value=usuario_row['activo'])
                    
                    submit_edit_button = st.form_submit_button("Actualizar Usuario", use_container_width=True)
                    
                    if submit_edit_button:
                        if nombre_edit and apellido_edit and email_edit:
                            # Actualizar usuario
                            actualizado = data_manager.actualizar_usuario(
                                usuario_id=usuario_seleccionado_id,
                                nombre=nombre_edit,
                                apellido=apellido_edit,
                                email=email_edit,
                                rol=rol_edit,
                                activo=activo_edit
                            )
                            
                            if actualizado:
                                st.success("Usuario actualizado exitosamente")
                                st.rerun()
                            else:
                                st.error("No se pudo actualizar el usuario. Verifica si el email ya está en uso.")
                        else:
                            st.error("Por favor, completa todos los campos.")
            else:
                st.info("No hay usuarios para editar.")
        else:
            st.info("No hay usuarios registrados.")
    
    with tab2:
        st.subheader("Crear Nuevo Usuario")
        
        with st.form("formulario_crear_usuario"):
            nombre = st.text_input("Nombre:")
            apellido = st.text_input("Apellido:")
            email = st.text_input("Email:")
            username = st.text_input("Nombre de Usuario:")
            password = st.text_input("Contraseña:", type="password")
            password_confirm = st.text_input("Confirmar Contraseña:", type="password")
            
            roles = ["operador", "supervisor", "admin"]
            rol = st.selectbox("Rol:", options=roles)
            
            submit_button = st.form_submit_button("Crear Usuario", type="primary")
            
            if submit_button:
                if nombre and apellido and email and username and password and password_confirm:
                    if password != password_confirm:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        # Crear usuario
                        usuario_id = data_manager.crear_usuario(
                            nombre=nombre,
                            apellido=apellido,
                            email=email,
                            username=username,
                            password=password,
                            rol=rol
                        )
                        
                        if usuario_id:
                            st.success(f"Usuario creado exitosamente con ID: {usuario_id}")
                            st.rerun()
                        else:
                            st.error("No se pudo crear el usuario. El email o nombre de usuario ya están en uso.")
                else:
                    st.error("Por favor, completa todos los campos.")

def mostrar_exportar_datos():
    st.title("Exportar Datos")
    
    st.write("""
    Desde esta sección puedes exportar todos los datos registrados para análisis adicionales
    en herramientas externas como Excel o software estadístico.
    """)
    
    # Opciones de exportación
    formato_exportacion = st.radio(
        "Selecciona el formato de exportación:",
        options=["CSV", "Excel"]
    )
    
    if st.button("Exportar Datos", type="primary"):
        # Obtener datos
        aires_df = data_manager.obtener_aires()
        lecturas_df = data_manager.obtener_lecturas()
        
        if aires_df.empty or lecturas_df.empty:
            st.warning("No hay suficientes datos para exportar.")
            return
        
        # Exportar según formato seleccionado
        if formato_exportacion == "CSV":
            # Crear buffers para los archivos CSV
            aires_buffer = io.StringIO()
            lecturas_buffer = io.StringIO()
            
            # Escribir DataFrames a buffers
            aires_df.to_csv(aires_buffer, index=False)
            lecturas_df.to_csv(lecturas_buffer, index=False)
            
            # Añadir enlaces de descarga
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="Descargar Datos de Aires (CSV)",
                    data=aires_buffer.getvalue(),
                    file_name="aires_acondicionados.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.download_button(
                    label="Descargar Datos de Lecturas (CSV)",
                    data=lecturas_buffer.getvalue(),
                    file_name="lecturas.csv",
                    mime="text/csv"
                )
        
        elif formato_exportacion == "Excel":
            # Crear buffer para archivo Excel
            excel_buffer = io.BytesIO()
            
            # Escribir DataFrames a buffer
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                aires_df.to_excel(writer, sheet_name='Aires', index=False)
                lecturas_df.to_excel(writer, sheet_name='Lecturas', index=False)
            
            # Añadir enlace de descarga
            st.download_button(
                label="Descargar Datos en Excel",
                data=excel_buffer.getvalue(),
                file_name="datos_aires_acondicionados.xlsx",
                mime="application/vnd.ms-excel"
            )
        
        st.success("Exportación completada exitosamente.")
    
    # Información adicional
    st.subheader("Resumen de Datos Disponibles")
    
    # Obtener datos
    aires_df = data_manager.obtener_aires()
    lecturas_df = data_manager.obtener_lecturas()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Aires Acondicionados:** {len(aires_df)}")
    
    with col2:
        st.write(f"**Lecturas Registradas:** {len(lecturas_df)}")
    
    # Mostrar vista previa de los datos
    if not aires_df.empty:
        st.subheader("Vista Previa: Aires Acondicionados")
        st.dataframe(aires_df.head(5), use_container_width=True)
    
    if not lecturas_df.empty:
        st.subheader("Vista Previa: Lecturas")
        preview_df = lecturas_df.sort_values("fecha", ascending=False).head(5)
        st.dataframe(preview_df, use_container_width=True)

# Ejecutar la página seleccionada
if pagina_seleccionada == "Dashboard":
    mostrar_dashboard()
elif pagina_seleccionada == "Registro de Lecturas":
    mostrar_registro_lecturas()
elif pagina_seleccionada == "Gestión de Aires":
    mostrar_gestion_aires()
elif pagina_seleccionada == "Registro de Mantenimientos":
    mostrar_registro_mantenimientos()
elif pagina_seleccionada == "Análisis y Estadísticas":
    mostrar_analisis_estadisticas()
elif pagina_seleccionada == "Configuración de Umbrales":
    mostrar_configuracion_umbrales()
elif pagina_seleccionada == "Gestión de Usuarios":
    mostrar_gestion_usuarios()
elif pagina_seleccionada == "Exportar Datos":
    mostrar_exportar_datos()
