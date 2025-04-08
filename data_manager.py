import pandas as pd
import os
import numpy as np
from datetime import datetime

class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.aires_file = os.path.join(self.data_dir, "aires_acondicionados.csv")
        self.lecturas_file = os.path.join(self.data_dir, "lecturas.csv")
        
        # Asegurar que el directorio de datos exista
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Cargar o crear archivos de datos
        self.cargar_datos()
    
    def cargar_datos(self):
        # Cargar o crear el archivo de aires acondicionados
        if os.path.exists(self.aires_file):
            self.aires_df = pd.read_csv(self.aires_file)
        else:
            # Crear DataFrame con los 7 aires predeterminados
            self.aires_df = pd.DataFrame({
                'id': range(1, 8),
                'nombre': [f'Aire {i}' for i in range(1, 8)],
                'ubicacion': ['Ubicación por definir' for _ in range(7)],
                'fecha_instalacion': [datetime.now().strftime('%Y-%m-%d') for _ in range(7)]
            })
            self.guardar_aires()
        
        # Cargar o crear el archivo de lecturas
        if os.path.exists(self.lecturas_file):
            self.lecturas_df = pd.read_csv(self.lecturas_file)
            # Convertir fecha a datetime
            self.lecturas_df['fecha'] = pd.to_datetime(self.lecturas_df['fecha'])
        else:
            self.lecturas_df = pd.DataFrame(columns=[
                'id', 'aire_id', 'fecha', 'temperatura', 'humedad'
            ])
            self.guardar_lecturas()
    
    def guardar_aires(self):
        self.aires_df.to_csv(self.aires_file, index=False)
    
    def guardar_lecturas(self):
        self.lecturas_df.to_csv(self.lecturas_file, index=False)
    
    def obtener_aires(self):
        return self.aires_df
    
    def obtener_lecturas(self):
        return self.lecturas_df
    
    def agregar_aire(self, nombre, ubicacion, fecha_instalacion):
        # Generar nuevo ID (máximo actual + 1)
        nuevo_id = 1
        if not self.aires_df.empty:
            nuevo_id = self.aires_df['id'].max() + 1
        
        # Agregar nuevo aire
        nuevo_aire = pd.DataFrame({
            'id': [nuevo_id],
            'nombre': [nombre],
            'ubicacion': [ubicacion],
            'fecha_instalacion': [fecha_instalacion]
        })
        
        self.aires_df = pd.concat([self.aires_df, nuevo_aire], ignore_index=True)
        self.guardar_aires()
        return nuevo_id
    
    def agregar_lectura(self, aire_id, fecha, temperatura, humedad):
        # Generar nuevo ID (máximo actual + 1)
        nuevo_id = 1
        if not self.lecturas_df.empty:
            nuevo_id = self.lecturas_df['id'].max() + 1
        
        # Agregar nueva lectura
        nueva_lectura = pd.DataFrame({
            'id': [nuevo_id],
            'aire_id': [aire_id],
            'fecha': [fecha],
            'temperatura': [temperatura],
            'humedad': [humedad]
        })
        
        self.lecturas_df = pd.concat([self.lecturas_df, nueva_lectura], ignore_index=True)
        self.guardar_lecturas()
        return nuevo_id
    
    def obtener_lecturas_por_aire(self, aire_id):
        return self.lecturas_df[self.lecturas_df['aire_id'] == aire_id]
    
    def obtener_estadisticas_por_aire(self, aire_id):
        lecturas_aire = self.obtener_lecturas_por_aire(aire_id)
        
        if lecturas_aire.empty:
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
        
        return {
            'temperatura': {
                'promedio': round(lecturas_aire['temperatura'].mean(), 2),
                'minimo': round(lecturas_aire['temperatura'].min(), 2),
                'maximo': round(lecturas_aire['temperatura'].max(), 2),
                'desviacion': round(lecturas_aire['temperatura'].std(), 2)
            },
            'humedad': {
                'promedio': round(lecturas_aire['humedad'].mean(), 2),
                'minimo': round(lecturas_aire['humedad'].min(), 2),
                'maximo': round(lecturas_aire['humedad'].max(), 2),
                'desviacion': round(lecturas_aire['humedad'].std(), 2)
            }
        }
    
    def obtener_estadisticas_generales(self):
        if self.lecturas_df.empty:
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
        
        return {
            'temperatura': {
                'promedio': round(self.lecturas_df['temperatura'].mean(), 2),
                'minimo': round(self.lecturas_df['temperatura'].min(), 2),
                'maximo': round(self.lecturas_df['temperatura'].max(), 2)
            },
            'humedad': {
                'promedio': round(self.lecturas_df['humedad'].mean(), 2),
                'minimo': round(self.lecturas_df['humedad'].min(), 2),
                'maximo': round(self.lecturas_df['humedad'].max(), 2)
            },
            'total_lecturas': len(self.lecturas_df)
        }
    
    def eliminar_aire(self, aire_id):
        # Eliminar el aire del DataFrame
        self.aires_df = self.aires_df[self.aires_df['id'] != aire_id]
        self.guardar_aires()
        
        # Eliminar lecturas asociadas
        self.lecturas_df = self.lecturas_df[self.lecturas_df['aire_id'] != aire_id]
        self.guardar_lecturas()
    
    def exportar_datos(self, formato='csv'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'csv':
            aires_export = os.path.join(self.data_dir, f'aires_export_{timestamp}.csv')
            lecturas_export = os.path.join(self.data_dir, f'lecturas_export_{timestamp}.csv')
            
            self.aires_df.to_csv(aires_export, index=False)
            self.lecturas_df.to_csv(lecturas_export, index=False)
            
            return aires_export, lecturas_export
        
        elif formato == 'excel':
            export_file = os.path.join(self.data_dir, f'export_{timestamp}.xlsx')
            
            with pd.ExcelWriter(export_file) as writer:
                self.aires_df.to_excel(writer, sheet_name='Aires', index=False)
                self.lecturas_df.to_excel(writer, sheet_name='Lecturas', index=False)
            
            return export_file
        
        return None
