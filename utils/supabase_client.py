import os
import requests
from dotenv import load_dotenv

load_dotenv()

class SimpleSupabase:
    def __init__(self, url, key):
        self.url = url
        self.headers = {
            "apikey": key, 
            "Authorization": f"Bearer {key}", 
            "Content-Type": "application/json",
            "Prefer": "return=representation" # Chiede a Supabase di restituire i dati aggiornati
        }
        self.reset_state()

    def reset_state(self):
        """Azzera le variabili per prepararsi a una nuova query"""
        self.table_name = ""
        self.query_string = ""
        self.method = "GET"
        self.payload = None

    def table(self, table_name):
        self.reset_state()
        self.table_name = table_name
        self.order_by_param = None
        return self

    def select(self, columns="*"):
        self.method = "GET"
        self.query_string = f"?select={columns}"
        return self

    def update(self, data):
        """Prepara un'operazione di aggiornamento (PATCH)"""
        self.method = "PATCH"
        self.payload = data
        return self

    def insert(self, data):
        """Prepara un'operazione di creazione (POST)"""
        self.method = "POST"
        self.payload = data
        return self
    
    def eq(self, column, value):
        """Aggiunge un filtro alla query (es. id == valore)"""
        # Se c'è già un '?', usiamo '&' per aggiungere altri parametri
        separator = "&" if "?" in self.query_string else "?"
        self.query_string += f"{separator}{column}=eq.{value}"
        return self

    def gte(self, column, value):
        """Filtro Maggiore o Uguale (>=)"""
        separator = "&" if "?" in self.query_string else "?"
        self.query_string += f"{separator}{column}=gte.{value}"
        return self

    def lte(self, column, value):
        """Filtro Minore o Uguale (<=)"""
        separator = "&" if "?" in self.query_string else "?"
        self.query_string += f"{separator}{column}=lte.{value}"
        return self

    def limit(self, n):
        separator = "&" if "?" in self.query_string else "?"
        self.query_string += f"{separator}limit={n}"
        return self

    def delete(self):
        """Prepara un'operazione di eliminazione (DELETE)"""
        self.method = "DELETE"
        self.payload = None
        return self

    def order(self, column, desc=False):
        """Imposta l'ordine dei risultati (ascendente o discendente)"""
        direction = "desc" if desc else "asc"
        self.order_by_param = f"{column}.{direction}"
        return self

    def execute(self):
        """Esegue la chiamata HTTP reale a Supabase"""
        full_url = f"{self.url}/rest/v1/{self.table_name}{self.query_string}"
        
        if hasattr(self, 'order_by_param') and self.order_by_param:
            separatore = "&" if "?" in full_url else "?"
            full_url = f"{full_url}{separatore}order={self.order_by_param}"

        if self.method == "GET":
            response = requests.get(full_url, headers=self.headers)
        elif self.method == "PATCH":
            response = requests.patch(full_url, headers=self.headers, json=self.payload)
        elif self.method == "POST":
            response = requests.post(full_url, headers=self.headers, json=self.payload)
        elif self.method == "DELETE":
            response = requests.delete(full_url, headers=self.headers)


        # --- NUOVO GESTORE ERRORI ---
        if not response.ok:
            dettagli_errore = response.text
            try:
                # Prova a estrarre il messaggio JSON pulito di Supabase
                errore_json = response.json()
                dettagli_errore = errore_json.get('message', response.text)
            except:
                pass
            # Lancia l'eccezione con il VERO motivo del blocco
            raise Exception(f"Errore DB: {dettagli_errore}")
        # ----------------------------
        
        class Result:
            def __init__(self, data): 
                self.data = data
                
        try:
            return Result(response.json())
        except ValueError:
            return Result([])
        
def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Chiavi non trovate nel file .env!")
    return SimpleSupabase(url, key)


