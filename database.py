import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Obtener la URL de conexión desde las variables de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Crear una sesión
Session = sessionmaker(bind=engine)
session = Session()

# Crear la base declarativa
Base = declarative_base()

# Definir el modelo para aires acondicionados
class AireAcondicionado(Base):
    __tablename__ = 'aires_acondicionados'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(200))
    fecha_instalacion = Column(String(10))
    
    # Relación con las lecturas
    lecturas = relationship("Lectura", back_populates="aire", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AireAcondicionado(id={self.id}, nombre='{self.nombre}')>"

# Definir el modelo para lecturas
class Lectura(Base):
    __tablename__ = 'lecturas'
    
    id = Column(Integer, primary_key=True)
    aire_id = Column(Integer, ForeignKey('aires_acondicionados.id'))
    fecha = Column(DateTime, nullable=False)
    temperatura = Column(Float, nullable=False)
    humedad = Column(Float, nullable=False)
    
    # Relación con el aire acondicionado
    aire = relationship("AireAcondicionado", back_populates="lecturas")
    
    def __repr__(self):
        return f"<Lectura(id={self.id}, aire_id={self.aire_id}, fecha='{self.fecha}')>"

# Crear todas las tablas en la base de datos
def init_db():
    Base.metadata.create_all(engine)