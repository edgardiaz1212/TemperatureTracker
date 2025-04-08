import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def crear_grafico_temperatura_humedad(lecturas_df, aire_id=None, periodo='todo'):
    """
    Crea gráficos de línea para temperatura y humedad
    
    Args:
        lecturas_df: DataFrame con las lecturas
        aire_id: ID del aire acondicionado (None para todos)
        periodo: 'semana', 'mes', 'año' o 'todo'
    
    Returns:
        Dos objetos de gráfico (temperatura y humedad)
    """
    # Filtrar por aire_id si se especifica
    if aire_id is not None:
        df = lecturas_df[lecturas_df['aire_id'] == aire_id]
    else:
        df = lecturas_df.copy()
    
    # Si no hay datos, devolver gráficos vacíos
    if df.empty:
        fig_temp = go.Figure()
        fig_temp.update_layout(title="No hay datos de temperatura disponibles")
        
        fig_hum = go.Figure()
        fig_hum.update_layout(title="No hay datos de humedad disponibles")
        
        return fig_temp, fig_hum
    
    # Convertir fecha a datetime si no lo está
    if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
        df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Filtrar por período
    fecha_actual = datetime.now()
    if periodo == 'semana':
        fecha_inicio = fecha_actual - timedelta(days=7)
        df = df[df['fecha'] >= fecha_inicio]
    elif periodo == 'mes':
        fecha_inicio = fecha_actual - timedelta(days=30)
        df = df[df['fecha'] >= fecha_inicio]
    elif periodo == 'año':
        fecha_inicio = fecha_actual - timedelta(days=365)
        df = df[df['fecha'] >= fecha_inicio]
    
    # Si después del filtrado no hay datos, devolver gráficos vacíos
    if df.empty:
        fig_temp = go.Figure()
        fig_temp.update_layout(title="No hay datos de temperatura para el período seleccionado")
        
        fig_hum = go.Figure()
        fig_hum.update_layout(title="No hay datos de humedad para el período seleccionado")
        
        return fig_temp, fig_hum
    
    # Crear gráficos de temperatura y humedad
    if aire_id is not None:
        # Para un solo aire acondicionado
        fig_temp = px.line(
            df, x='fecha', y='temperatura',
            title=f'Temperatura a lo largo del tiempo',
            labels={'temperatura': 'Temperatura (°C)', 'fecha': 'Fecha'},
            line_shape='linear'
        )
        
        fig_hum = px.line(
            df, x='fecha', y='humedad',
            title=f'Humedad a lo largo del tiempo',
            labels={'humedad': 'Humedad (%)', 'fecha': 'Fecha'},
            line_shape='linear'
        )
    else:
        # Para todos los aires acondicionados
        fig_temp = px.line(
            df, x='fecha', y='temperatura', color='aire_id',
            title='Temperatura por aire acondicionado',
            labels={'temperatura': 'Temperatura (°C)', 'fecha': 'Fecha', 'aire_id': 'ID Aire'},
            line_shape='linear'
        )
        
        fig_hum = px.line(
            df, x='fecha', y='humedad', color='aire_id',
            title='Humedad por aire acondicionado',
            labels={'humedad': 'Humedad (%)', 'fecha': 'Fecha', 'aire_id': 'ID Aire'},
            line_shape='linear'
        )
    
    # Personalizar gráficos
    fig_temp.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Temperatura (°C)',
        hovermode='x unified'
    )
    
    fig_hum.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Humedad (%)',
        hovermode='x unified'
    )
    
    return fig_temp, fig_hum

def crear_grafico_comparativo(lecturas_df, variable='temperatura'):
    """
    Crea un gráfico de barras para comparar temperatura o humedad entre aires acondicionados
    
    Args:
        lecturas_df: DataFrame con las lecturas
        variable: 'temperatura' o 'humedad'
    
    Returns:
        Objeto de gráfico
    """
    if lecturas_df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"No hay datos de {variable} disponibles")
        return fig
    
    # Agrupar por aire_id y calcular estadísticas
    df_agrupado = lecturas_df.groupby('aire_id')[variable].agg(['mean', 'min', 'max']).reset_index()
    df_agrupado.columns = ['aire_id', 'promedio', 'minimo', 'maximo']
    
    # Crear gráfico
    fig = go.Figure()
    
    # Añadir barras para promedio
    fig.add_trace(go.Bar(
        x=df_agrupado['aire_id'],
        y=df_agrupado['promedio'],
        name='Promedio',
        marker_color='rgb(55, 83, 109)'
    ))
    
    # Añadir rangos min-max
    fig.add_trace(go.Scatter(
        x=df_agrupado['aire_id'],
        y=df_agrupado['maximo'],
        mode='markers',
        name='Máximo',
        marker=dict(color='red', size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_agrupado['aire_id'],
        y=df_agrupado['minimo'],
        mode='markers',
        name='Mínimo',
        marker=dict(color='blue', size=8)
    ))
    
    # Personalizar gráfico
    unidad = '°C' if variable == 'temperatura' else '%'
    
    fig.update_layout(
        title=f'Comparación de {variable} entre aires acondicionados',
        xaxis_title='ID del Aire Acondicionado',
        yaxis_title=f'{variable.capitalize()} ({unidad})',
        barmode='group',
        hovermode='x unified'
    )
    
    return fig

def crear_grafico_variacion(lecturas_df, aire_id=None, variable='temperatura'):
    """
    Crea un gráfico de variación (desviación estándar) para temperatura o humedad
    
    Args:
        lecturas_df: DataFrame con las lecturas
        aire_id: ID del aire acondicionado (None para todos)
        variable: 'temperatura' o 'humedad'
    
    Returns:
        Objeto de gráfico
    """
    if lecturas_df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"No hay datos de variación de {variable}")
        return fig
    
    # Filtrar por aire_id si se especifica
    if aire_id is not None:
        df = lecturas_df[lecturas_df['aire_id'] == aire_id]
    else:
        df = lecturas_df.copy()
    
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"No hay datos de variación de {variable} para el aire seleccionado")
        return fig
    
    # Convertir fecha a datetime si no lo está
    if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
        df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Crear columna de mes-año para agrupar
    df['mes_año'] = df['fecha'].dt.strftime('%Y-%m')
    
    if aire_id is not None:
        # Calcular variación por mes para un solo aire
        df_variacion = df.groupby('mes_año')[variable].agg(['mean', 'std']).reset_index()
        df_variacion.columns = ['mes_año', 'promedio', 'desviacion']
        
        # Evitar NaN en desviación
        df_variacion['desviacion'] = df_variacion['desviacion'].fillna(0)
        
        # Ordenar por mes-año
        df_variacion = df_variacion.sort_values('mes_año')
        
        # Crear gráfico
        fig = go.Figure()
        
        # Añadir barras de desviación
        fig.add_trace(go.Bar(
            x=df_variacion['mes_año'],
            y=df_variacion['desviacion'],
            name='Desviación Estándar',
            marker_color='rgb(55, 83, 109)'
        ))
        
        # Añadir línea de promedio
        fig.add_trace(go.Scatter(
            x=df_variacion['mes_año'],
            y=df_variacion['promedio'],
            mode='lines+markers',
            name='Promedio',
            marker=dict(color='red', size=8)
        ))
        
        # Personalizar gráfico
        unidad = '°C' if variable == 'temperatura' else '%'
        
        fig.update_layout(
            title=f'Variación de {variable} por mes',
            xaxis_title='Mes',
            yaxis_title=f'{variable.capitalize()} ({unidad})',
            hovermode='x unified'
        )
    else:
        # Calcular variación por aire acondicionado
        df_variacion = df.groupby('aire_id')[variable].agg(['mean', 'std']).reset_index()
        df_variacion.columns = ['aire_id', 'promedio', 'desviacion']
        
        # Evitar NaN en desviación
        df_variacion['desviacion'] = df_variacion['desviacion'].fillna(0)
        
        # Ordenar por aire_id
        df_variacion = df_variacion.sort_values('aire_id')
        
        # Crear gráfico
        fig = go.Figure()
        
        # Añadir barras de desviación
        fig.add_trace(go.Bar(
            x=df_variacion['aire_id'].astype(str),
            y=df_variacion['desviacion'],
            name='Desviación Estándar',
            marker_color='rgb(55, 83, 109)'
        ))
        
        # Añadir línea de promedio
        fig.add_trace(go.Scatter(
            x=df_variacion['aire_id'].astype(str),
            y=df_variacion['promedio'],
            mode='lines+markers',
            name='Promedio',
            marker=dict(color='red', size=8)
        ))
        
        # Personalizar gráfico
        unidad = '°C' if variable == 'temperatura' else '%'
        
        fig.update_layout(
            title=f'Variación de {variable} por aire acondicionado',
            xaxis_title='ID del Aire Acondicionado',
            yaxis_title=f'{variable.capitalize()} ({unidad})',
            hovermode='x unified'
        )
    
    return fig

def generar_reporte_estadistico(lecturas_df):
    """
    Genera un reporte estadístico completo de las lecturas
    
    Args:
        lecturas_df: DataFrame con las lecturas
    
    Returns:
        DataFrame con las estadísticas
    """
    if lecturas_df.empty:
        return pd.DataFrame({
            'aire_id': [],
            'temperatura_promedio': [],
            'temperatura_min': [],
            'temperatura_max': [],
            'temperatura_std': [],
            'humedad_promedio': [],
            'humedad_min': [],
            'humedad_max': [],
            'humedad_std': [],
            'lecturas_totales': []
        })
    
    # Agrupar por aire_id y calcular estadísticas
    stats = lecturas_df.groupby('aire_id').agg({
        'temperatura': ['mean', 'min', 'max', 'std'],
        'humedad': ['mean', 'min', 'max', 'std'],
        'id': 'count'
    }).reset_index()
    
    # Aplanar columnas multiíndice
    stats.columns = [
        'aire_id',
        'temperatura_promedio',
        'temperatura_min',
        'temperatura_max',
        'temperatura_std',
        'humedad_promedio',
        'humedad_min',
        'humedad_max',
        'humedad_std',
        'lecturas_totales'
    ]
    
    # Redondear valores numéricos
    for col in stats.columns:
        if col != 'aire_id' and col != 'lecturas_totales':
            stats[col] = stats[col].round(2)
    
    return stats
