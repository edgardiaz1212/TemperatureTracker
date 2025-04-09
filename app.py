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
    return DataManager()

data_manager = get_data_manager()

# Sidebar para navegación
st.sidebar.title("Monitoreo AC")
paginas = [
    "Dashboard",
    "Registro de Lecturas",
    "Gestión de Aires",
    "Registro de Mantenimientos",
    "Análisis y Estadísticas",
    "Exportar Datos"
]

pagina_seleccionada = st.sidebar.radio("Navegar a:", paginas)

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
    
    # Formulario para agregar lectura
    with st.form("formulario_lectura"):
        st.subheader("Nueva Lectura")
        
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
        submitted = st.form_submit_button("Registrar Lectura")
        
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

# Función para la página de gestión de aires
def mostrar_gestion_aires():
    st.title("Gestión de Aires Acondicionados")
    
    # Formulario para agregar nuevo aire
    with st.form("formulario_aire"):
        st.subheader("Agregar Nuevo Aire Acondicionado")
        
        nombre = st.text_input("Nombre:", placeholder="Ej: Aire Oficina Principal")
        ubicacion = st.text_input("Ubicación:", placeholder="Ej: Planta 1, Sala 3")
        fecha_instalacion = st.date_input("Fecha de instalación:", datetime.now())
        
        # Botón para enviar
        submitted = st.form_submit_button("Agregar Aire")
        
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
    
    # Mostrar aires registrados
    st.subheader("Aires Acondicionados Registrados")
    
    aires_df = data_manager.obtener_aires()
    
    if not aires_df.empty:
        # Mostrar tabla con los aires
        st.dataframe(aires_df, use_container_width=True)
        
        # Sección para eliminar aire
        st.subheader("Eliminar Aire Acondicionado")
        
        aire_options = [(f"{row['nombre']} (ID: {row['id']})", row['id']) for _, row in aires_df.iterrows()]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            aire_a_eliminar_nombre, aire_a_eliminar_id = st.selectbox(
                "Seleccionar Aire para eliminar:",
                options=aire_options,
                format_func=lambda x: x[0]
            )
        
        with col2:
            if st.button("Eliminar Aire", type="primary", use_container_width=True):
                # Confirmar eliminación
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
        st.info("No hay aires acondicionados registrados aún.")

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
            
            mantenimiento_options = [(f"ID: {row['id']} - {row['Tipo']} ({row['Fecha']})", row['id']) for _, row in mantenimientos_display.iterrows()]
            
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

# Función para la página de exportación de datos
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
elif pagina_seleccionada == "Exportar Datos":
    mostrar_exportar_datos()
