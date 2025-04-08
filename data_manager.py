import pandas as pd
import os
import numpy as np
from datetime import datetime
from database import session, AireAcondicionado, Lectura, init_db
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
    
    def eliminar_aire(self, aire_id):
        # Obtener el aire a eliminar
        aire = session.query(AireAcondicionado).filter(AireAcondicionado.id == aire_id).first()
        
        if aire:
            # SQLAlchemy eliminará automáticamente las lecturas asociadas debido a la relación cascade
            session.delete(aire)
            session.commit()
    
    def exportar_datos(self, formato='csv'):
        # Asegurar que el directorio exista
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Obtener datos de la base de datos
        aires_df = self.obtener_aires()
        lecturas_df = self.obtener_lecturas()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'csv':
            aires_export = os.path.join(self.data_dir, f'aires_export_{timestamp}.csv')
            lecturas_export = os.path.join(self.data_dir, f'lecturas_export_{timestamp}.csv')
            
            aires_df.to_csv(aires_export, index=False)
            lecturas_df.to_csv(lecturas_export, index=False)
            
            return aires_export, lecturas_export
        
        elif formato == 'excel':
            export_file = os.path.join(self.data_dir, f'export_{timestamp}.xlsx')
            
            with pd.ExcelWriter(export_file) as writer:
                aires_df.to_excel(writer, sheet_name='Aires', index=False)
                lecturas_df.to_excel(writer, sheet_name='Lecturas', index=False)
            
            return export_file
        
        return None
