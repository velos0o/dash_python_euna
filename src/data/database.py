"""Módulo de conexão com o banco de dados"""
import mysql.connector
from mysql.connector import Error
import pandas as pd
from sqlalchemy import create_engine
from ..utils.constants import DATABASE_CONFIG
from typing import Optional, Dict, Any, Union
import streamlit as st

class Database:
    """Classe para gerenciar conexões com o banco de dados"""
    _instance = None
    _engine = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    @property
    def engine(self):
        """Obtém ou cria a engine SQLAlchemy"""
        if self._engine is None:
            conn_str = (
                f"mysql+mysqlconnector://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
                f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
            )
            self._engine = create_engine(
                conn_str,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
        return self._engine

    def get_connection(self) -> Optional[mysql.connector.MySQLConnection]:
        """Cria uma nova conexão com o banco de dados"""
        try:
            return mysql.connector.connect(**DATABASE_CONFIG)
        except Error as e:
            st.error(f"Erro ao conectar ao banco de dados: {e}")
            return None

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
        """Executa uma query e retorna um DataFrame"""
        try:
            with self.engine.connect() as conn:
                return pd.read_sql(query, conn, params=params)
        except Exception as e:
            st.error(f"Erro ao executar query: {e}")
            return None

    def execute_raw_query(self, query: str, params: Optional[tuple] = None) -> Optional[pd.DataFrame]:
        """Executa uma query raw usando mysql.connector"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Erro ao executar query: {e}")
            return None
        finally:
            if conn.is_connected():
                conn.close()

# Instância global
db = Database()