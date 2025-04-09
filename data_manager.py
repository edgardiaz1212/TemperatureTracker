import pandas as pd
import os
import numpy as np
import io
from datetime import datetime
from database import session, AireAcondicionado, Lectura, Mantenimiento, init_db
from sqlalchemy import func, distinct

class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.aires_file = os.path.join(self.data_dir, "aires_acondicionados.csv")
        self.lecturas_file = os.path.join(self.data_dir, "lecturas.csv")
        
        # Asegurar que el directorio de datos exista
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Inicializar la base de datos
        init_db()
        
        # Migrar datos de CSV a base de datos si es necesario
        self.migrar_datos_si_necesario()
    
    def migrar_datos_si_necesario(self):
        # Verificar si hay datos en la base de datos
        aires_count = session.query(AireAcondicionado).count()
        
        # Solo migrar si no hay datos en la BD y existen los archivos CSV
        if aires_count == 0:
            # Migrar aires acondicionados
            if os.path.exists(self.aires_file):
                aires_df = pd.read_csv(self.aires_file)
                for _, row in aires_df.iterrows():
                    aire = AireAcondicionado(
                        id=int(row['id']),
                        nombre=row['nombre'],
                        ubicacion=row['ubicacion'],
                        fecha_instalacion=row['fecha_instalacion']
                    )
                    session.add(aire)
                session.commit()
            else:
                # Crear aires predeterminados
                for i in range(1, 8):
                    aire = AireAcondicionado(
                        nombre=f'Aire {i}',
                        ubicacion='Ubicación por definir',
                        fecha_instalacion=datetime.now().strftime('%Y-%m-%d')
                    )
                    session.add(aire)
                session.commit()
            
            # Migrar lecturas si existen
            if os.path.exists(self.lecturas_file):
                lecturas_df = pd.read_csv(self.lecturas_file)
                if not lecturas_df.empty:
                    # Convertir fecha a datetime si es string
                    if lecturas_df['fecha'].dtype == 'object':
                        lecturas_df['fecha'] = pd.to_datetime(lecturas_df['fecha'])
                    
                    for _, row in lecturas_df.iterrows():
                        lectura = Lectura(
                            id=int(row['id']),
                            aire_id=int(row['aire_id']),
                            fecha=row['fecha'],
                            temperatura=float(row['temperatura']),
                            humedad=float(row['humedad'])
                        )
                        session.add(lectura)
                    session.commit()
    
    def obtener_aires(self):
        # Consultar todos los aires de la base de datos
        aires = session.query(AireAcondicionado).all()
        
        # Convertir a DataFrame
        aires_data = [
            {
                'id': aire.id,
                'nombre': aire.nombre,
                'ubicacion': aire.ubicacion,
                'fecha_instalacion': aire.fecha_instalacion
            }
            for aire in aires
        ]
        
        return pd.DataFrame(aires_data)
    
    def obtener_lecturas(self):
        # Consultar todas las lecturas de la base de datos
        lecturas = session.query(Lectura).all()
        
        # Convertir a DataFrame
        lecturas_data = [
            {
                'id': lectura.id,
                'aire_id': lectura.aire_id,
                'fecha': lectura.fecha,
                'temperatura': lectura.temperatura,
                'humedad': lectura.humedad
            }
            for lectura in lecturas
        ]
        
        return pd.DataFrame(lecturas_data)
    
    def agregar_aire(self, nombre, ubicacion, fecha_instalacion):
        # Crear nuevo aire acondicionado en la base de datos
        nuevo_aire = AireAcondicionado(
            nombre=nombre,
            ubicacion=ubicacion,
            fecha_instalacion=fecha_instalacion
        )
        
        session.add(nuevo_aire)
        session.commit()
        
        return nuevo_aire.id
    
    def agregar_lectura(self, aire_id, fecha, temperatura, humedad):
        # Crear nueva lectura en la base de datos
        nueva_lectura = Lectura(
            aire_id=aire_id,
            fecha=fecha,
            temperatura=temperatura,
            humedad=humedad
        )
        
        session.add(nueva_lectura)
        session.commit()
        
        return nueva_lectura.id
    
    def obtener_lecturas_por_aire(self, aire_id):
        # Consultar lecturas de un aire específico
        lecturas = session.query(Lectura).filter(Lectura.aire_id == aire_id).all()
        
        # Convertir a DataFrame
        lecturas_data = [
            {
                'id': lectura.id,
                'aire_id': lectura.aire_id,
                'fecha': lectura.fecha,
                'temperatura': lectura.temperatura,
                'humedad': lectura.humedad
            }
            for lectura in lecturas
        ]
        
        return pd.DataFrame(lecturas_data)
    
    def obtener_estadisticas_por_aire(self, aire_id):
        # Consultar estadísticas de un aire específico desde la base de datos
        result = session.query(
            func.avg(Lectura.temperatura).label('temp_avg'),
            func.min(Lectura.temperatura).label('temp_min'),
            func.max(Lectura.temperatura).label('temp_max'),
            func.stddev(Lectura.temperatura).label('temp_std'),
            func.avg(Lectura.humedad).label('hum_avg'),
            func.min(Lectura.humedad).label('hum_min'),
            func.max(Lectura.humedad).label('hum_max'),
            func.stddev(Lectura.humedad).label('hum_std')
        ).filter(Lectura.aire_id == aire_id).first()
        
        # Si no hay lecturas, devolver valores predeterminados
        if result.temp_avg is None:
            return {
                'temperatura': {
                    'promedio': 0,
                    'minimo': 0,
                    'maximo': 0,
                    'desviacion': 0
                },
                'humedad': {
                    'promedio': 0,
                    'minimo': 0,
                    'maximo': 0,
                    'desviacion': 0
                }
            }
        
        # Convertir a diccionario
        return {
            'temperatura': {
                'promedio': round(result.temp_avg, 2) if result.temp_avg else 0,
                'minimo': round(result.temp_min, 2) if result.temp_min else 0,
                'maximo': round(result.temp_max, 2) if result.temp_max else 0,
                'desviacion': round(result.temp_std, 2) if result.temp_std else 0
            },
            'humedad': {
                'promedio': round(result.hum_avg, 2) if result.hum_avg else 0,
                'minimo': round(result.hum_min, 2) if result.hum_min else 0,
                'maximo': round(result.hum_max, 2) if result.hum_max else 0,
                'desviacion': round(result.hum_std, 2) if result.hum_std else 0
            }
        }
    
    def obtener_estadisticas_generales(self):
        # Consultar estadísticas generales desde la base de datos
        result = session.query(
            func.avg(Lectura.temperatura).label('temp_avg'),
            func.min(Lectura.temperatura).label('temp_min'),
            func.max(Lectura.temperatura).label('temp_max'),
            func.avg(Lectura.humedad).label('hum_avg'),
            func.min(Lectura.humedad).label('hum_min'),
            func.max(Lectura.humedad).label('hum_max'),
            func.count(distinct(Lectura.id)).label('total_lecturas')
        ).first()
        
        # Si no hay lecturas, devolver valores predeterminados
        if result.temp_avg is None:
            return {
                'temperatura': {
                    'promedio': 0,
                    'minimo': 0,
                    'maximo': 0
                },
                'humedad': {
                    'promedio': 0,
                    'minimo': 0,
                    'maximo': 0
                },
                'total_lecturas': 0
            }
        
        # Convertir a diccionario
        return {
            'temperatura': {
                'promedio': round(result.temp_avg, 2) if result.temp_avg else 0,
                'minimo': round(result.temp_min, 2) if result.temp_min else 0,
                'maximo': round(result.temp_max, 2) if result.temp_max else 0
            },
            'humedad': {
                'promedio': round(result.hum_avg, 2) if result.hum_avg else 0,
                'minimo': round(result.hum_min, 2) if result.hum_min else 0,
                'maximo': round(result.hum_max, 2) if result.hum_max else 0
            },
            'total_lecturas': result.total_lecturas or 0
        }
        
    def obtener_ubicaciones(self):
        """
        Obtiene todas las ubicaciones únicas de los aires acondicionados.
        
        Returns:
            Lista de ubicaciones únicas
        """
        ubicaciones = session.query(distinct(AireAcondicionado.ubicacion)).all()
        return [ubicacion[0] for ubicacion in ubicaciones]
    
    def obtener_aires_por_ubicacion(self, ubicacion):
        """
        Obtiene los aires acondicionados en una ubicación específica.
        
        Args:
            ubicacion: La ubicación a filtrar
            
        Returns:
            DataFrame con los aires en esa ubicación
        """
        aires = session.query(AireAcondicionado).filter(AireAcondicionado.ubicacion == ubicacion).all()
        
        # Convertir a DataFrame
        aires_data = [
            {
                'id': aire.id,
                'nombre': aire.nombre,
                'ubicacion': aire.ubicacion,
                'fecha_instalacion': aire.fecha_instalacion
            }
            for aire in aires
        ]
        
        return pd.DataFrame(aires_data)
    
    def obtener_estadisticas_por_ubicacion(self, ubicacion=None):
        """
        Obtiene estadísticas agrupadas por ubicación.
        
        Args:
            ubicacion: Opcional, filtrar por una ubicación específica
            
        Returns:
            DataFrame con estadísticas por ubicación
        """
        # Si no hay lecturas o aires, devolver DataFrame vacío
        aires_count = session.query(AireAcondicionado).count()
        if aires_count == 0:
            return pd.DataFrame()
        
        # Obtener todas las ubicaciones o la ubicación específica
        if ubicacion:
            ubicaciones = [ubicacion]
        else:
            ubicaciones = self.obtener_ubicaciones()
        
        # Lista para almacenar resultados
        resultados = []
        
        # Para cada ubicación, obtener sus aires y estadísticas
        for ubicacion_actual in ubicaciones:
            # Obtener IDs de aires en esta ubicación
            aires_ids = session.query(AireAcondicionado.id).filter(
                AireAcondicionado.ubicacion == ubicacion_actual
            ).all()
            aires_ids = [aire_id[0] for aire_id in aires_ids]
            
            if not aires_ids:
                continue
            
            # Consultar estadísticas para estos aires
            result = session.query(
                func.avg(Lectura.temperatura).label('temp_avg'),
                func.min(Lectura.temperatura).label('temp_min'),
                func.max(Lectura.temperatura).label('temp_max'),
                func.stddev(Lectura.temperatura).label('temp_std'),
                func.avg(Lectura.humedad).label('hum_avg'),
                func.min(Lectura.humedad).label('hum_min'),
                func.max(Lectura.humedad).label('hum_max'),
                func.stddev(Lectura.humedad).label('hum_std'),
                func.count(distinct(Lectura.id)).label('total_lecturas')
            ).filter(Lectura.aire_id.in_(aires_ids)).first()
            
            # Si hay lecturas para esta ubicación
            if result.temp_avg is not None:
                resultados.append({
                    'ubicacion': ubicacion_actual,
                    'num_aires': len(aires_ids),
                    'temperatura_promedio': round(result.temp_avg, 2) if result.temp_avg else 0,
                    'temperatura_min': round(result.temp_min, 2) if result.temp_min else 0,
                    'temperatura_max': round(result.temp_max, 2) if result.temp_max else 0,
                    'temperatura_std': round(result.temp_std, 2) if result.temp_std else 0,
                    'humedad_promedio': round(result.hum_avg, 2) if result.hum_avg else 0,
                    'humedad_min': round(result.hum_min, 2) if result.hum_min else 0,
                    'humedad_max': round(result.hum_max, 2) if result.hum_max else 0,
                    'humedad_std': round(result.hum_std, 2) if result.hum_std else 0,
                    'lecturas_totales': result.total_lecturas or 0
                })
        
        # Convertir resultados a DataFrame
        return pd.DataFrame(resultados)
    
    def eliminar_aire(self, aire_id):
        # Obtener el aire a eliminar
        aire = session.query(AireAcondicionado).filter(AireAcondicionado.id == aire_id).first()
        
        if aire:
            # SQLAlchemy eliminará automáticamente las lecturas asociadas debido a la relación cascade
            session.delete(aire)
            session.commit()
    
    def agregar_mantenimiento(self, aire_id, tipo_mantenimiento, descripcion, tecnico, imagen_file=None):
        """
        Agrega un nuevo registro de mantenimiento a la base de datos.
        
        Args:
            aire_id: ID del aire acondicionado
            tipo_mantenimiento: Tipo de mantenimiento realizado
            descripcion: Descripción detallada del mantenimiento
            tecnico: Nombre del técnico que realizó el mantenimiento
            imagen_file: Archivo de imagen subido (bytes y metadatos)
            
        Returns:
            ID del nuevo mantenimiento registrado
        """
        # Crear nuevo registro de mantenimiento
        nuevo_mantenimiento = Mantenimiento(
            aire_id=aire_id,
            fecha=datetime.now(),
            tipo_mantenimiento=tipo_mantenimiento,
            descripcion=descripcion,
            tecnico=tecnico
        )
        
        # Si se cargó una imagen, guardarla en la base de datos
        if imagen_file is not None:
            # Obtener bytes de la imagen
            imagen_bytes = imagen_file.read()
            
            # Guardar datos de la imagen
            nuevo_mantenimiento.imagen_nombre = imagen_file.name
            nuevo_mantenimiento.imagen_tipo = imagen_file.type
            nuevo_mantenimiento.imagen_datos = imagen_bytes
        
        # Guardar en la base de datos
        session.add(nuevo_mantenimiento)
        session.commit()
        
        return nuevo_mantenimiento.id
    
    def obtener_mantenimientos(self, aire_id=None):
        """
        Obtiene todos los mantenimientos, opcionalmente filtrados por aire_id.
        
        Args:
            aire_id: Opcional, ID del aire acondicionado para filtrar
            
        Returns:
            DataFrame con los mantenimientos
        """
        # Construir la consulta
        query = session.query(Mantenimiento)
        
        # Filtrar por aire_id si se proporciona
        if aire_id is not None:
            query = query.filter(Mantenimiento.aire_id == aire_id)
        
        # Ordenar por fecha (más recientes primero)
        mantenimientos = query.order_by(Mantenimiento.fecha.desc()).all()
        
        # Convertir a DataFrame
        mantenimientos_data = [
            {
                'id': mant.id,
                'aire_id': mant.aire_id,
                'fecha': mant.fecha,
                'tipo_mantenimiento': mant.tipo_mantenimiento,
                'descripcion': mant.descripcion,
                'tecnico': mant.tecnico,
                'tiene_imagen': mant.imagen_datos is not None
            }
            for mant in mantenimientos
        ]
        
        return pd.DataFrame(mantenimientos_data)
    
    def obtener_mantenimiento_por_id(self, mantenimiento_id):
        """
        Obtiene un mantenimiento específico por su ID.
        
        Args:
            mantenimiento_id: ID del mantenimiento a obtener
            
        Returns:
            Objeto Mantenimiento o None si no existe
        """
        return session.query(Mantenimiento).filter(Mantenimiento.id == mantenimiento_id).first()
    
    def eliminar_mantenimiento(self, mantenimiento_id):
        """
        Elimina un mantenimiento por su ID.
        
        Args:
            mantenimiento_id: ID del mantenimiento a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        mantenimiento = session.query(Mantenimiento).filter(Mantenimiento.id == mantenimiento_id).first()
        
        if mantenimiento:
            session.delete(mantenimiento)
            session.commit()
            return True
        
        return False
    
    def exportar_datos(self, formato='csv'):
        # Asegurar que el directorio exista
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Obtener datos de la base de datos
        aires_df = self.obtener_aires()
        lecturas_df = self.obtener_lecturas()
        mantenimientos_df = self.obtener_mantenimientos()
        
        # Eliminar columna de imagen binaria para exportación
        if not mantenimientos_df.empty:
            mantenimientos_export_df = mantenimientos_df.copy()
        else:
            mantenimientos_export_df = pd.DataFrame()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'csv':
            aires_export = os.path.join(self.data_dir, f'aires_export_{timestamp}.csv')
            lecturas_export = os.path.join(self.data_dir, f'lecturas_export_{timestamp}.csv')
            mantenimientos_export = os.path.join(self.data_dir, f'mantenimientos_export_{timestamp}.csv')
            
            aires_df.to_csv(aires_export, index=False)
            lecturas_df.to_csv(lecturas_export, index=False)
            
            if not mantenimientos_export_df.empty:
                mantenimientos_export_df.to_csv(mantenimientos_export, index=False)
            
            return aires_export, lecturas_export, mantenimientos_export
        
        elif formato == 'excel':
            export_file = os.path.join(self.data_dir, f'export_{timestamp}.xlsx')
            
            with pd.ExcelWriter(export_file) as writer:
                aires_df.to_excel(writer, sheet_name='Aires', index=False)
                lecturas_df.to_excel(writer, sheet_name='Lecturas', index=False)
                
                if not mantenimientos_export_df.empty:
                    mantenimientos_export_df.to_excel(writer, sheet_name='Mantenimientos', index=False)
            
            return export_file
        
        return None
