from sqlalchemy import create_engine
import pandas as pd
from typing import Tuple, Optional
from queries import get_family_status_query, get_payment_options_query

class Database:
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.connection_string = (
            f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
        )
        self._engine = None
    
    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self.connection_string)
        return self._engine
    
    def get_family_data(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Busca dados das famílias e opções de pagamento"""
        try:
            # Buscar status das famílias
            df = pd.read_sql(get_family_status_query(), self.engine)
            
            # Buscar distribuição das opções de pagamento
            df_options = pd.read_sql(get_payment_options_query(), self.engine)
            
            return df, df_options
        except Exception:
            return None, None