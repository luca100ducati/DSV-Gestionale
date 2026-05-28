from anyio import Path
from nicegui import app, ui
from utils.supabase_client import get_supabase
import urllib.parse  # Aggiungi questo in cima al file main.py se non c'è già
from urllib.parse import quote
import os
from groq import AsyncGroq
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
# Inizializziamo il "Cervello" di Radu
GROQ_API_KEY = "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" 
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# L'Anima di Radu (Il Prompt di Sistema)
radu_prompt = """Sei Radu, Moldavo, da 10 anni in Italia. un onesto lavoratore di 35 anni con 20 anni di esperienza nella logistica, nei cantieri e nel sudore. 
Lavori per la DSV Logistics (ex Schenker). Sei scontroso, burbero, cinico e fumi un pacchetto di sigarette al giorno. Il tuo capo lo chiami "Scifu" (ma non lo nomini spesso).
Usi un linguaggio diretto, pratico, a volte sarcastico e colorito (ma non usare bestemmie o volgarità estreme), spesso per le tue origini hai difficoltà a pronunciare le parole con la doppia vocale (es: Ruota la chiami Rota, Piede lo chiami Pede, invece di Vieni dici Veni ecc..). 
Non devi MAI dire che sei un'intelligenza artificiale o un assistente virtuale: tu sei un uomo in carne e ossa che vuole solo lavorare, bersi un caffè, fumare una sigaretta e tornare a casa. 
Rispondi alle domande in modo utile e corretto, ma fallo sempre facendola pesare. IMPORTANTE: le risposte devono essere sintetiche ma corrette, ogni tanto mettici una battuta in stile 'moldavo'  e non superare le 20-25 righe per le richieste più complesse, sennò anche meno. """

# Questa lista farà da "memoria" a breve termine per fargli ricordare di cosa state parlando
memoria_radu = [
    {"role": "system", "content": radu_prompt}
]



# Inizializzazione client
supabase = get_supabase()

ui.page_title('DSV | Gestionale')

# --- 1. CARICAMENTO ESTETICA ESTERNA ---
app.add_static_files('/static' , 'static/')
ui.add_head_html('''
<link rel="stylesheet" type="text/css" href="/static/style.css">

<style>
               

@media print {
    /* Sbianca completamente lo sfondo generale */
    body, .q-dialog__inner {
        background: white !important;
        padding: 0 !important;
    }
    /* Nasconde TUTTO l'hardware dell'app: barre di navigazione, cassetti, overlay scuri e pulsanti */
    .no-print, .q-header, .q-drawer, .q-footer, .q-btn, .q-backdrop {
        display: none !important;
    }
    /* Forza la scheda di anteprima a occupare tutta la pagina senza bordi o ombre */
    .printable-sheet {
        background: white !important;
        color: black !important;
        box-shadow: none !important;
        border: none !important;
        width: 100% !important;
        max-width: 100% !important;
        padding: 0 !important;
    }
    /* Evita che un'etichetta venga tagliata a metà se finisce a fondo pagina */
    .print-label-card {
        border: 1px solid #ccc !important;
        box-shadow: none !important;
        page-break-inside: avoid;
    }
}
</style>
''')

def carica_conoscenza_radu():
    cartella_doc = './documenti_radu'
    if not os.path.exists(cartella_doc) or not os.listdir(cartella_doc):
        print("Radu: 'La cartella è vuota, non ho niente da studiare.'")
        return None
    
    try:
        print("Radu sta leggendo i file di testo...")
        # Cambiamo il glob per cercare i file .txt e usiamo TextLoader con codifica UTF-8
        loader = DirectoryLoader(
            cartella_doc, 
            glob="**/*.txt", 
            loader_cls=TextLoader, 
            loader_kwargs={'encoding': 'utf-8'}
        )
        documenti = loader.load()
        
        if not documenti:
            print("Radu: 'I file .txt sono vuoti!'")
            return None
        
        # Spezzettiamo il testo in paragrafi
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        frammenti = text_splitter.split_documents(documenti)
        
        if len(frammenti) == 0:
            return None
            
        # Usiamo il modello multilingua che abbiamo scelto prima
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        database_vettoriale = FAISS.from_documents(frammenti, embeddings)
        
        print(f"Radu ha memorizzato ed elaborato {len(frammenti)} paragrafi di testo.")
        return database_vettoriale
        
    except Exception as e:
        print(f"Errore durante la lettura dei file .txt: {e}")
        return None

# Variabile globale che contiene la libreria di Radu
db_conoscenza_radu = carica_conoscenza_radu()







# --- 2. STRUTTURA PAGINA ---
def layout_principale():
# Nel tuo layout_principale
    with ui.header().classes('justify-between bg-blue-900'):
        with ui.row().classes('justify-center'):
            ui.image('logo-dsv-w.png').classes('w-32')

            # Definiamo il toggle
            nav = ui.toggle(
                options=["Pannello di Controllo", "Inventario", "Spostamenti / DDT", "Manutenzioni", "Luoghi", "Personale", "Pianificazione"],
                value="Pannello di Controllo"
            ).classes('justify-center').props('outline rounded push glossy')
            
                        
        # Area Contenuti
    content_area = ui.column().classes('w-full min-w-0 max-w-full')

    def update_content(scelta):
        content_area.clear()
        with content_area:
            if scelta == "Pannello di Controllo": 
                import datetime

                container = ui.column().classes('w-full max-w-full gap-6 p-2')
                
                def carica_e_disegna():
                    try:
                        container.clear()
                        with container:
                            ui.spinner('bars', size='4em', color='orange').classes('mx-auto mt-20')

                        oggi = datetime.date.today()
                        dati_dash = {
                            'attrezzi_magazzino': 0,
                            'attrezzi_cantiere': 0,
                            'ddt_7_giorni': 0,
                            'urgenze_manutenzioni': [],
                            'ultimi_movimenti': []
                        }

                        def estrai(res):
                            if hasattr(res, 'data'): return res.data or []
                            return res if isinstance(res, list) else []

                        # SCARICAMENTO E LOGICA
                        luoghi = estrai(supabase.table('luoghi').select('*').execute())
                        inventario = estrai(supabase.table('inventario').select('*').execute())
                        mezzi = estrai(supabase.table('mezzi').select('*').execute()) # <--- AGGIUNTA
                        mappa_luoghi = {l['id']: l for l in luoghi}
                        mappa_inv = {i['id']: i for i in inventario}
                        mappa_mezzi = {m['id']: m for m in mezzi}

                        id_depositi = [l['id'] for l in luoghi if 'deposito' in str(l.get('tipo', '')).lower() or 'deposito' in str(l.get('ragione_sociale', '')).lower()]
                        id_cantieri = [l['id'] for l in luoghi if 'cantiere' in str(l.get('tipo', '')).lower() or 'cantiere' in str(l.get('ragione_sociale', '')).lower()]
                        
                        dati_dash['attrezzi_magazzino'] = sum(1 for item in inventario if item.get('posizione_attuale') in id_depositi)
                        dati_dash['attrezzi_cantiere'] = sum(1 for item in inventario if item.get('posizione_attuale') in id_cantieri)

                        settimana_fa = (oggi - datetime.timedelta(days=7)).isoformat()
                        res_ddt = supabase.table('ddt').select('id').gte('data_emissione', settimana_fa).execute()
                        dati_dash['ddt_7_giorni'] = len(estrai(res_ddt))

                        # 2. LOGICA URGENZE (Modificata per pescare da mappa_mezzi)
                        limite_urgenza = oggi + datetime.timedelta(days=30)
                        tutte_manutenzioni = estrai(supabase.table('manutenzioni').select('*').execute())
                        
                        dati_dash['urgenze_manutenzioni'] = [] # Reset
                        
                        for m in tutte_manutenzioni:
                            scad_str = m.get('prossima_scadenza') or m.get('scadenza') or m.get('data_scadenza')
                            if scad_str:
                                try:
                                    scad_data = datetime.datetime.strptime(str(scad_str)[:10], '%Y-%m-%d').date()
                                    if scad_data <= limite_urgenza:
                                        # Peschiamo da mappa_mezzi invece di mappa_inv
                                        mezzo = mappa_mezzi.get(m.get('mezzo_id'), {})
                                        
                                        dati_dash['urgenze_manutenzioni'].append({
                                            # Qui peschiamo nome_modello
                                            'mezzo': mezzo.get('nome_modello') or mezzo.get('nome') or "Veicolo/Attrezzo",
                                            'tipo': m.get('tipo_intervento', 'Manutenzione'),
                                            'data': scad_data.strftime('%d/%m/%Y'),
                                            'scaduta': scad_data < oggi
                                        })
                                except: pass
                        # Sort per data
                        dati_dash['urgenze_manutenzioni'] = sorted(dati_dash['urgenze_manutenzioni'], key=lambda x: x['data'])[:5]
                        
                        
                        # Radar Movimenti
                        res_mov = supabase.table('movimenti').select('*').order('data_move', desc=True).limit(5).execute()
                        for mov in estrai(res_mov):
                            oggetto = mappa_inv.get(mov.get('asset_id'), {})
                            dati_dash['ultimi_movimenti'].append({
                                'oggetto': oggetto.get('articolo') or oggetto.get('nome') or 'Oggetto ignoto',
                                'da': mappa_luoghi.get(mov.get('da_luogo'), {}).get('ragione_sociale', 'Ignoto'),
                                'a': mappa_luoghi.get(mov.get('a_luogo'), {}).get('ragione_sociale', 'Ignoto'),
                                'data': str(mov.get('data_move', ''))[:10],
                                'ddt': bool(mov.get('ddt_id'))
                            })

                        # 3. DISEGNO FINALE
                        container.clear()
                        with container:
                            
                            # FASCIA ALTA CON CARD (Ora senza .default_slot, usando la struttura standard)
                            with ui.row().classes('w-full gap-4 no-wrap'):
                                
                                with ui.card().classes('flex-1 bg-gray-800 border-l-4 border-blue-500 items-center p-4').props('dense'):
                                    ui.icon('warehouse', color='blue-400', size='lg')
                                    ui.label(str(dati_dash['attrezzi_magazzino'])).classes('text-4xl font-black text-white')
                                    ui.label('In Magazzino').classes('text-gray-400 font-bold text-xs')
                                    
                                with ui.card().classes('flex-1 bg-gray-800 border-l-4 border-orange-500 items-center p-4').props('dense'):
                                    ui.icon('construction', color='orange-400', size='lg')
                                    ui.label(str(dati_dash['attrezzi_cantiere'])).classes('text-4xl font-black text-white')
                                    ui.label('Nei Cantieri').classes('text-gray-400 font-bold text-xs')
                                    
                                with ui.card().classes('flex-1 bg-gray-800 border-l-4 border-green-500 items-center p-4').props('dense'):
                                    ui.icon('local_shipping', color='green-400', size='lg')
                                    ui.label(str(dati_dash['ddt_7_giorni'])).classes('text-4xl font-black text-white')
                                    ui.label('DDT (Ultimi 7 gg)').classes('text-gray-400 font-bold text-xs')

                            # FASCIA CENTRALE: Urgenze e Radar
                            with ui.row().classes('w-full gap-6 no-wrap items-stretch mt-4'):
                                
                                # COLONNA SINISTRA: Urgenze Manutenzioni
                                with ui.column().classes('flex-1 bg-gray-800 border border-gray-700 rounded-xl p-5 shadow-xl').props('dense'):
                                    with ui.row().classes('items-center gap-2 mb-4'):
                                        ui.icon('warning', color='red-500', size='sm')
                                        ui.label('Allarmi Manutenzioni').classes('text-xl font-bold text-red-400')
                                    
                                    if not dati_dash['urgenze_manutenzioni']:
                                        with ui.column().classes('w-full items-center p-4').props('dense'):
                                            ui.icon('check_circle', color='green-600', size='lg')
                                            ui.label('Nessuna scadenza critica in vista!').classes('text-green-500 font-bold mt-2')
                                    else:
                                        for urg in dati_dash['urgenze_manutenzioni']:
                                            colore_txt = 'text-red-500 font-bold' if urg['scaduta'] else 'text-orange-400 font-bold'
                                            icona_stato = 'error' if urg['scaduta'] else 'schedule'
                                            
                                            with ui.row().classes('w-full items-center justify-between border-b border-gray-700 pb-3 mb-3'):
                                                with ui.column().classes('gap-0'):
                                                    ui.label(urg['mezzo']).classes('text-white font-bold text-lg')
                                                    ui.label(urg['tipo']).classes('text-gray-400 text-sm')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.icon(icona_stato).classes(colore_txt)
                                                    ui.label(urg['data']).classes(colore_txt)

                                # COLONNA DESTRA: Radar Movimenti
                                with ui.column().classes('flex-1 bg-gray-800 border border-gray-700 rounded-xl p-5 shadow-xl').props('dense'):
                                    with ui.row().classes('items-center gap-2 mb-4'):
                                        ui.icon('history', color='blue-400', size='sm')
                                        ui.label('Radar Spostamenti').classes('text-xl font-bold text-blue-300')
                                    
                                    if not dati_dash['ultimi_movimenti']:
                                        ui.label('Nessun movimento recente.').classes('text-gray-500 italic mt-4')
                                    else:
                                        for mov in dati_dash['ultimi_movimenti']:
                                            icon_color = 'green-400' if mov['ddt'] else 'gray-400'
                                            icon_name = 'description' if mov['ddt'] else 'fast_forward'
                                            
                                            with ui.row().classes('w-full items-start gap-3 border-b border-gray-700 pb-3 mb-3 no-wrap'):
                                                ui.icon(icon_name, color=icon_color).classes('mt-1').tooltip('Con DDT' if mov['ddt'] else 'Spostamento Rapido')
                                                with ui.column().classes('gap-0 flex-grow'):
                                                    ui.label(mov['oggetto']).classes('text-white font-bold')
                                                    ui.label(f"Da: {mov['da']}").classes('text-gray-400 text-xs')
                                                    ui.label(f"A: {mov['a']}").classes('text-gray-300 text-xs font-bold')
                                                ui.badge(mov['data'], color='blue-900').classes('text-xs font-bold')

                    except Exception as e:
                        container.clear()
                        with container:
                            ui.label(f"Errore: {e}").classes('text-red-500 font-bold')
                            ui.button('Riprova', on_click=carica_e_disegna)

                ui.timer(0.1, carica_e_disegna, once=True)



            elif scelta == "Inventario":

                inventario_container = ui.column().classes('w-full min-w-0')                
                global tabella
                tabella = None  # Resettiamo la variabile di sicurezza quando cambiamo pagina

                def carica_dati():
                    global tutti_i_dati
                    global tabella # Richiamiamo la tabella per poterla aggiornare
                    try:
                        # 1. Scarichiamo l'inventario e i luoghi
                        res_inv = supabase.table('inventario').select('*').execute()
                        res_luoghi = supabase.table('luoghi').select('id,ragione_sociale').execute()
                        
                        # 2. Creiamo il dizionario delle traduzioni
                        mappa_luoghi = {
                            luogo.get('id'): luogo.get('ragione_sociale') 
                            for luogo in res_luoghi.data
                        }
                        
                        # 3. Assegniamo i dati alla variabile globale
                        tutti_i_dati = res_inv.data
                        
                        # 4. Traduciamo gli UUID nei nomi visibili per l'utente
                        for riga in tutti_i_dati:
                            uuid_luogo = riga.get('posizione_attuale')
                            riga['nome_posizione_visiva'] = mappa_luoghi.get(uuid_luogo, 'Sconosciuto')

                        # --- IL NUOVO TRUCCO DELLA VELOCITÀ ---
                        # Se la tabella esiste già, cambiamo solo il testo interno senza ridisegnare la pagina!
                        if tabella is not None:
                            try:
                                tabella.rows = tutti_i_dati
                                tabella.update()
                            except Exception:
                                pass # Evita crash se l'utente sta cambiando pagina in quel millesimo di secondo
                        else:
                            # Se è il primissimo caricamento di questa sessione, disegniamo la grafica intera
                            renderizza_interfaccia()

                    except Exception as e:
                        try:
                            inventario_container.clear()
                            with inventario_container:
                                ui.label('⚠️ ERRORE FATALE IN CARICAMENTO DATI ⚠️').classes('text-red-500 text-2xl font-bold mt-4')
                                ui.label(f'Dettaglio: {str(e)}').classes('text-yellow-400 text-lg')
                        except:
                            pass # Protezione estrema contro i crash di cambio pagina
                            
                # (Da qui in poi lascia la tua def renderizza_interfaccia() intatta...)


                def renderizza_interfaccia():
                    """Disegna la barra di ricerca, i pulsanti e la tabella"""
                    global tabella
                    inventario_container.clear()
                    
                    with inventario_container:
                        # --- 1. DEFINIZIONE COLONNE ---
                        colonne = [
                            {'name': 'azioni', 'label': '', 'field': 'azioni', 'align': 'center'},
                            {'name': 'id', 'label': 'ID Seriale', 'field': 'id', 'sortable': True, 'align': 'left'},
                            {'name': 'nome', 'label': 'Nome', 'field': 'nome', 'sortable': True, 'align': 'left'},
                            {'name': 'descrizione', 'label': 'Descrizione', 'field': 'descrizione', 'align': 'left'},
                            {'name': 'posizione_attuale', 'label': 'Posizione Attuale', 'field': 'nome_posizione_visiva', 'sortable': True, 'align': 'left'},
                            {'name': 'contenuto_in', 'label': 'Contenuto in', 'field': 'contenuto_in', 'sortable': True, 'align': 'left'},
                            {'name': 'peso', 'label': 'Peso', 'field': 'peso', 'align': 'right'},
                            {'name': 'dimensioni', 'label': 'Dimensioni', 'field': 'dimensioni', 'align': 'left'},
                            {'name': 'stato', 'label': '', 'field': 'stato', 'sortable': True, 'align': 'center'},
                        ]

                                            # --- 2. CREAZIONE TABELLA ---
                        # Creiamo una "gabbia" rigida che non può superare il 100% dello spazio e forza lo scroll
                        with ui.element('div').classes('w-full overflow-x-auto rounded-lg border border-gray-700'):
                            tabella = ui.table(
                                columns=colonne, 
                                rows=tutti_i_dati,
                                row_key='id',
                                selection='multiple'  # Infine disegniamo (o aggiorniamo) l'interfaccia
                                ).classes('bg-transparent data-table text-white w-full min-w-[1000px]').props('dense flat bordered')
                        
                        # --- 3. FUNZIONE DI RICERCA ---
                        def filtra_tabella(e):
                            if e.value is None:
                                return
                            
                            termine = e.value.lower().strip()
                            if not termine:
                                tabella.rows = tutti_i_dati
                            else:                            
                                dati_filtrati = [
                                    riga for riga in tutti_i_dati
                                    if termine in str(riga.get('nome', '')).lower() 
                                    or termine in str(riga.get('id', '')).lower()
                                    or termine in str(riga.get('nome_posizione_visiva', '')).lower()
                                    or termine in str(riga.get('contenuto_in', '')).lower()
                                ]
                        
                                tabella.rows = dati_filtrati
                            tabella.update()

                    # --- 4. BARRA DEGLI STRUMENTI (Header Tabella) ---
                    # Aggiunto "no-wrap" per impedire che gli elementi vadano a capo
                    with ui.row().classes('w-full justify-between items-center no-wrap mb-4 mt-4') as header_row:
                        
                        # [SINISTRA] Blocco Ricerca (Ripristinato in tempo reale!)
                        search = ui.input(
                            placeholder='Cerca per nome, ID o luogo...', 
                            on_change=filtra_tabella
                        ).props('input-style="color: white" outlined clearable rounded dense').classes('custom-input w-full max-w-md')
                        
                        with search.add_slot('prepend'):
                            ui.icon('search').classes('text-white')
                            
                        # ATTENZIONE: Assicurati di aver CANCELLATO la riga search.on('input', filtra_tabella) che c'era qui sotto!
                        # [DESTRA] Blocco Bottoni Azioni di Massa
                        # Aggiunto "no-wrap" anche qui per tenere i bottoni tutti vicini in fila
                        with ui.row().classes('gap-3 items-center no-wrap'):
                            ui.button(icon='add', on_click=lambda: aggiungi_asset(tabella.selected)).props('round outline color="positive"').tooltip('Aggiungi')
                            ui.button(icon='delete', on_click=lambda: elimina_asset(tabella.selected)).props('round outline color="negative"').tooltip('Elimina')
                            ui.button(icon='local_shipping', on_click=lambda: crea_ddt_massa(tabella.selected)).props('round outline color="white"').tooltip('Crea DDT')
                            ui.button(icon='qr_code', on_click=lambda: genera_qr_massa(tabella.selected)).props('round outline color="white"').tooltip('Genera QR Code')
                            ui.button(icon='print', on_click=lambda: stampa_selezione(tabella.selected)).props('round outline color="white"').tooltip('Stampa Etichette')
                            ui.button(icon='place', on_click=lambda: sposta_massa(tabella.selected)).props('round outline color="info"').tooltip('Sposta Luogo')
                            ui.button(icon='build', on_click=lambda: manutenzione_massa(tabella.selected)).props('round outline color="warning"').tooltip('In Manutenzione')
                            

                        # Spostiamo la riga finita sopra la tabella
                        header_row.move(inventario_container, 0)  
                        
                        # --- 5. BOTTONE MODIFICA (Pulsante in ogni riga) ---
                        tabella.add_slot('body-cell-azioni', '''
                            <q-td :props="props">
                                <q-btn size="sm" round outline color="white" icon="edit" @click="() => $parent.$emit('modifica', props.row)" />
                            </q-td>
                        ''')

                        tabella.on('modifica', lambda e: apri_modifica(e.args))

                        # Disegniamo subito una rotellina di caricamento per non far freezare l'app
                with inventario_container:
                    ui.spinner('dots', size='3em', color='blue').classes('mx-auto mt-20')

                carica_dati()


                def apri_modifica(row_data):
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-4xl max-h-[80vh] overflow-auto').props('dense flat grid'):
                        ui.label(f"Modifica: {row_data.get('nome', '')}").classes('text-2xl font-bold text-white mb-4')
                        foto = row_data.get('foto_url', '')
                        if foto:
                            ui.image(foto).classes('w-full h-48 object-cover rounded-lg border border-gray-600 mb-6')
                        else:
                            ui.label('📷 Nessuna foto disponibile per questo oggetto').classes('text-gray-400 italic mb-6 text-center w-full bg-gray-800 p-4 rounded-lg')

                        try:
                            res_casse = supabase.table('inventario').select('id,contenuto_in').execute()
                            opzioni_casse = {l['id']: l['contenuto_in'] for l in res_casse.data}
                        except Exception as e:
                            ui.notify(f'Errore lettura casse: {e}', type='negative')
                            return


                        with ui.grid(columns=2).classes('w-full gap-4'):
                            ui.input('ID Seriale', value=row_data.get('id', '')).classes('custom-input disable-input').props('disable')
                            nome_input = ui.input('Nome', value=row_data.get('nome', '')).classes('custom-input w-full')
                            tipo_input = ui.select(['attrezzo', 'cassa'], label='Tipo', value=row_data.get('tipo', 'attrezzo')).classes('custom-input w-full')
                            seriale_input = ui.input('Numero Seriale (Produttore)', value=row_data.get('numero_seriale', '')).classes('custom-input w-full')
                            peso_input = ui.input('Peso', value=row_data.get('peso', '')).classes('custom-input w-full')
                            dim_input = ui.input('Dimensioni', value=row_data.get('dimensioni', '')).classes('custom-input w-full')
                            foto_input = ui.input('URL Foto (Link)', value=row_data.get('foto_url', '')).classes('custom-input w-full')
                            contenuto_input = ui.select(opzioni_casse, label='Seleziona cassa...', value=row_data.get('contenuto_in', 'descrizione')).classes('custom-input w-full')
                            ult_man_input = ui.input('Ultima Manutenzione (YYYY-MM-DD)', value=row_data.get('ultima_manutenzione', '')).classes('custom-input w-full')
                            pros_man_input = ui.input('Prossima Manutenzione (YYYY-MM-DD)', value=row_data.get('prossima_manutenzione', '')).classes('custom-input w-full')
                            desc_input = ui.textarea('Descrizione', value=row_data.get('descrizione', '')).classes('custom-input w-full col-span-2')

                        def salva_modifiche():
                            def nullify(val):
                                return val if str(val).strip() != '' else None

                            aggiornamenti = {
                                'nome': nome_input.value,
                                'tipo': tipo_input.value,
                                'descrizione': nullify(desc_input.value),
                                'numero_seriale': nullify(seriale_input.value),
                                'foto_url': nullify(foto_input.value),
                                'peso': nullify(peso_input.value),
                                'dimensioni': nullify(dim_input.value),
                                'contenuto_in': nullify(contenuto_input.value),
                                'ultima_manutenzione': nullify(ult_man_input.value),
                                'prossima_manutenzione': nullify(pros_man_input.value),
                            }

                            try:
                                supabase.table("inventario").update(aggiornamenti).eq('id', row_data['id']).execute()
                                ui.notify('✅ Dati aggiornati con successo!', type='positive', position='top')
                                dialog.close()
                                carica_dati()
                            except Exception as e:
                                ui.notify(f'❌ Errore: {e}', type='negative', position='top')

                        with ui.row().classes('w-full justify-end gap-4 mt-8 pt-4 border-t border-gray-600'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Salva Modifiche', on_click=salva_modifiche).classes('bg-blue-600 text-white font-bold')

                    dialog.open()


                def crea_ddt_massa(ddt_selezionati):

                    if not ddt_selezionati:
                        ui.notify('Seleziona almeno un attrezzo dalla tabella per creare il DDT!', type='warning')
                        return

                    try:
                        # 1. Recuperiamo i luoghi reali registrati nella tabella 'luoghi' su Supabase
                        res_luoghi = supabase.table('luoghi').select('id,ragione_sociale').execute()
                        
                        # Creiamo un dizionario di opzioni: { 'uuid-del-luogo': 'Nome Luogo' }
                        # NiceGUI mostrerà il Nome, ma .value restituirà l'UUID!
                        opzioni_luoghi = {r['id']: r['ragione_sociale'] for r in res_luoghi.data}
                    except Exception as e:
                        ui.notify(f'Errore nel caricamento dei luoghi: {e}', type='negative')
                        return

                    # Apriamo la finestra di dialogo
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-3xl p-6 rounded-lg border border-gray-600'):
                        ui.label('📄 Compilazione Nuovo DDT').classes('text-2xl font-bold text-white mb-2')
                        ui.label(f'Stai creando un documento di trasporto per {len(ddt_selezionati)} elementi.').classes('text-blue-300 mb-6')

                        # Form di compilazione DDT
                        with ui.grid(columns=2).classes('w-full gap-4'):
                            num_ddt = ui.input('Numero DDT *').classes('custom-input w-full')
                            
                            # Sostituiti ui.input con ui.select collegati al dizionario opzioni_luoghi
                            partenza = ui.select(options=opzioni_luoghi, label='Luogo Partenza').classes('custom-input w-full').props('dark')
                            arrivo = ui.select(options=opzioni_luoghi, label='Luogo Arrivo *').classes('custom-input w-full').props('dark')
                            
                            causale = ui.input('Causale').classes('custom-input w-full')
                            vettore = ui.input('Vettore (Chi trasportas)').classes('custom-input w-full')
                            note = ui.textarea('Note').classes('custom-input w-full col-span-2')

                        async def salva_ddt():
                            # 1. Validazione base
                            if not num_ddt.value or not arrivo.value:
                                ui.notify('Compila i campi obbligatori (*) !', type='warning')
                                return
                            
                            # Feedback visivo: disabilitiamo il bottone così l'utente non clicca 2 volte
                            btn_salva.disable()
                            btn_salva.text = "Salvataggio in corso..."
                            
                            nome_partenza = opzioni_luoghi.get(partenza.value) if partenza.value else None
                            nome_arrivo = opzioni_luoghi.get(arrivo.value)

                            nuovo_ddt = {
                                'numero': num_ddt.value,
                                'luogo_partenza': nome_partenza,
                                'luogo_arrivo': nome_arrivo,
                                'causale': causale.value,
                                'vettore': vettore.value,
                                'note': note.value
                            }

                            # Isoliamo le chiamate a Supabase in una sotto-funzione
                            def operazioni_db():
                                res_ddt = supabase.table('ddt').insert(nuovo_ddt).execute()
                                if not res_ddt.data:
                                    raise Exception("Errore nella risposta di Supabase durante la creazione del DDT")
                                
                                ddt_id = res_ddt.data[0]['id']

                                for asset in ddt_selezionati:
                                    supabase.table('inventario').update({'posizione_attuale': arrivo.value}).eq('id', asset['id']).execute()
                                    
                                    nuovo_movimento = {
                                        'asset_id': asset['id'],
                                        'da_luogo': partenza.value if partenza.value else None,
                                        'a_luogo': arrivo.value,
                                        'ddt_id': ddt_id,
                                        'note': f"Spostamento con DDT n. {num_ddt.value}"
                                    }
                                    supabase.table('movimenti').insert(nuovo_movimento).execute()

                            try:
                                import asyncio
                                # MANDIAMO IL LAVORO IN BACKGROUND! Nessun blocco dell'interfaccia.
                                await asyncio.to_thread(operazioni_db)

                                ui.notify('✅ DDT Creato con successo e movimenti registrati!', type='positive', position='top')
                                dialog.close()
                                tabella.selected.clear()
                                carica_dati()
                                
                            except Exception as e:
                                errore_str = str(e)
                                if "409" in errore_str:
                                    ui.notify('❌ Attenzione: Esiste già un DDT registrato con questo numero!', type='negative', position='top')
                                else:
                                    ui.notify(f'❌ Errore di salvataggio: {e}', type='negative', position='top')
                            finally:
                                # Riabilitiamo il bottone se qualcosa è andato storto
                                btn_salva.enable()
                                btn_salva.text = "Salva e Registra DDT"

                        # Bottoni inferiori
                        with ui.row().classes('w-full justify-end gap-4 mt-8'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            
                            # Aggiungi "btn_salva =" prima di ui.button
                            btn_salva = ui.button('Salva e Registra DDT', on_click=salva_ddt).classes('bg-blue-600 text-white font-bold px-6')
                    
                    dialog.open()

                    #Funzione per generare QR Code di massa
                
                def genera_qr_massa(qr_selezionati):
                    if not qr_selezionati:
                        ui.notify('Seleziona almeno un elemento dalla tabella per generare i QR!', type='warning')
                        return

                    # Apriamo la finestra di dialogo
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-5xl p-6 rounded-lg border border-gray-600'):
                        ui.label('🔲 Generatore QR Code').classes('text-2xl font-bold text-white mb-2')
                        ui.label(f'Generati {len(qr_selezionati)} codici.').classes('text-blue-300 mb-6')

                        # Creiamo una griglia flessibile (scrollabile se sono tanti)
                        scroll_area = ui.scroll_area().classes('w-full h-[600px] border border-gray-700 p-4 rounded bg-gray-800')
                        with scroll_area:
                            with ui.row().classes('w-full flex-wrap gap-6 justify-center'):
                                
                                for asset in qr_selezionati:
                                    # 1. Decidiamo cosa c'è SCRITTO dentro il QR Code. 
                                    dati_qr = f"ID: {asset.get('id', '')} - {asset.get('nome', '')}"
                                    
                                    # 2. Usiamo solo 'quote' (grazie all'import in alto)
                                    dati_codificati = quote(dati_qr)
                                    
                                    # 3. Chiamiamo l'API per l'immagine
                                    url_immagine = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={dati_codificati}"
                                    
                                    # 4. Disegniamo il "cartellino" per ogni attrezzo
                                    with ui.card().classes('bg-white p-4 items-center w-48 shadow-lg'):
                                        ui.image(url_immagine).classes('w-32 h-32')
                                        ui.label(asset.get('nome', 'Sconosciuto')).classes('text-black font-bold mt-3 text-center leading-tight')
                                        ui.label(asset.get('id', '')[:8] + "...").classes('text-gray-600 text-xs text-center mt-1')

                        # Bottone di chiusura
                        with ui.row().classes('w-full justify-end mt-4'):
                            ui.button('Chiudi', on_click=dialog.close).classes('bg-red-600 text-white font-bold')

                    dialog.open()
                # Funzione per stampare le etichette degli elementi selezionati

                def stampa_selezione(stampe_selezionati):
                    if not stampe_selezionati:
                        ui.notify('Seleziona almeno un elemento dalla tabella per stampare le etichette!', type='warning')
                        return

                    # Apriamo la finestra di dialogo ottimizzata per la stampa
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-5xl p-6 rounded-lg border border-gray-600 printable-sheet'):
                        
                        # Barra di controllo superiore (.no-print: scompare in fase di stampa reale)
                        with ui.row().classes('w-full justify-between items-center mb-6 no-print'):
                            with ui.column():
                                ui.label('🖨️ Generatore Etichette (Layout Schizzo)').classes('text-2xl font-bold text-white')
                                ui.label(f'Pronto per la stampa di {len(stampe_selezionati)} etichette.').classes('text-blue-300')
                            with ui.row().classes('gap-3'):
                                ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                                ui.button('Avvia Stampa', icon='print', on_click=lambda: ui.run_javascript('window.print()')).classes('bg-green-600 text-white font-bold px-6')

                        # Area del foglio (bianca)
                        with ui.element('div').classes('bg-white p-6 rounded border border-gray-300 w-full text-black'):
                            # Griglia a 2 colonne
                            with ui.grid(columns=2).classes('w-full gap-4 justification-center'):
                                
                                for asset in stampe_selezionati:
                                    # Generiamo il contenuto del QR Code (solo ID per scansioni più pulite)
                                    dati_qr = f"{asset.get('id', '')}" 
                                    dati_codificati = urllib.parse.quote(dati_qr)
                                    url_immagine = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={dati_codificati}"
                                    
                                    # --- TARGHETTA (Outer Card - Stile Industriale Semplificato) ---
                                    with ui.card().classes('bg-white border-2 border-black rounded-none shadow-none p-4 print-label-card w-full text-black'):
                                        
                                        # RIGA PRINCIPALE che divide l'etichetta in due aree (Sinistra e Destra)
                                        with ui.row().classes('w-full items-center justify-start gap-8 no-wrap'):
                                            
                                            # COLONNA SINISTRA -> Solo il QR Code
                                            ui.image(url_immagine).classes('w-28 h-28 flex-shrink-0')
                                            
                                            # COLONNA DESTRA -> Incolonniamo Logo e ID verticalmente
                                            with ui.column().classes('gap-3 items-start justify-center'):
                                                
                                                # Riga 1: Logo aziendale
                                                ui.image('dsv-print-logo.png').classes('w-32 h-10').props('fit=contain')
                                                
                                                # Riga 2: ID dell'oggetto evidenziato
                                                ui.label(asset.get('id', 'N/A')).classes('text-lg font-mono font-bold bg-black text-white px-3 py-1 rounded')
                    dialog.open()


                def sposta_massa(move_selezionati):
                    if not move_selezionati:
                        ui.notify('Seleziona almeno un elemento per lo spostamento!', type='warning')
                        return

                    # Apriamo il dialog
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-md p-6 rounded-lg border border-gray-600 text-white'):
                        ui.label('📍 Spostamento Rapido').classes('text-2xl font-bold mb-2')
                        ui.label(f'Stai spostando {len(move_selezionati)} elementi dalla loro posizione attuale.').classes('text-blue-200 mb-6')

                        # Scarichiamo i luoghi aggiornati dal DB per il menu a tendina
                        try:
                            res_luoghi = supabase.table('luoghi').select('id,ragione_sociale').execute()
                            opzioni_luoghi = {l['id']: l['ragione_sociale'] for l in res_luoghi.data}
                        except Exception as e:
                            ui.notify(f'Errore lettura luoghi: {e}', type='negative')
                            return

                        # Menu a tendina per scegliere la destinazione
                        nuovo_luogo = ui.select(opzioni_luoghi, label='Seleziona la nuova destinazione...').classes('w-full mb-6').props('dark outlined')

                        def conferma_spostamento():
                            if not nuovo_luogo.value:
                                ui.notify('Devi selezionare una destinazione!', type='warning')
                                return
                            
                            try:
                                # 1. Salviamo sul Database
                                for asset in move_selezionati:
                                    supabase.table('inventario').update({'posizione_attuale': nuovo_luogo.value}).eq('id', asset['id']).execute()
                                
                                ui.notify(f'✅ {len(move_selezionati)} elementi spostati con successo!', type='positive')
                                
                                # 2. Chiudiamo la finestra
                                dialog.close()
                                
                                # 3. IL TRUCCO: Invece di aggiornare subito bloccando tutto, 
                                # ritardiamo l'aggiornamento di due decimi di secondo. 
                                ui.timer(0.2, carica_dati, once=True)
                                
                            except Exception as e:
                                ui.notify(f'❌ Errore durante lo spostamento: {e}', type='negative')

                        # Bottoni inferiori
                        with ui.row().classes('w-full justify-end gap-4 mt-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Conferma Spostamento', on_click=conferma_spostamento).classes('bg-green-600 text-white font-bold px-4 shadow-md hover:scale-105 transition-transform')

                    dialog.open()



                def manutenzione_massa(mntz_selezionati):
                    if not mntz_selezionati:
                        ui.notify('Seleziona almeno un elemento da aggiornare!', type='warning')
                        return

                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-md p-6 rounded-lg border border-gray-600 text-white'):
                        ui.label('🔧 Aggiorna Stato / Manutenzione').classes('text-2xl font-bold mb-2')
                        ui.label(f'Aggiornamento per {len(mntz_selezionati)} elementi.').classes('text-orange-300 mb-6')

                        # --- NUOVO: Menu a tendina per lo Stato ---
                        opzioni_stato = ['Operativo', 'In Manutenzione', 'Guasto', 'Smarrito', 'Dismesso']
                        # Se selezionano 1 solo elemento, mostriamo il suo stato attuale, altrimenti vuoto
                        stato_iniziale = mntz_selezionati[0].get('stato') if len(mntz_selezionati) == 1 else None
                        
                        nuovo_stato = ui.select(opzioni_stato, value=stato_iniziale, label='Cambia Stato Attrezzo').classes('w-full mb-4').props('dark outlined clearable')

                        # Date Manutenzione
                        with ui.input('Data Ultima Manutenzione').classes('w-full mb-4').props('dark outlined clearable') as data_ultima:
                            with ui.menu().props('no-parent-event') as menu_ultima:
                                with ui.date().bind_value(data_ultima):
                                    pass
                            with data_ultima.add_slot('append'):
                                ui.icon('calendar_today').on('click', menu_ultima.open).classes('cursor-pointer text-white')

                        with ui.input('Data Prossima Manutenzione').classes('w-full mb-6').props('dark outlined clearable') as data_prossima:
                            with ui.menu().props('no-parent-event') as menu_prossima:
                                with ui.date().bind_value(data_prossima):
                                    pass
                            with data_prossima.add_slot('append'):
                                ui.icon('calendar_today').on('click', menu_prossima.open).classes('cursor-pointer text-white')

                        def conferma_manutenzione():
                            # Prepariamo il pacchetto di dati da aggiornare
                            aggiornamenti = {}
                            if nuovo_stato.value:
                                aggiornamenti['stato'] = nuovo_stato.value
                            if data_ultima.value: 
                                aggiornamenti['ultima_manutenzione'] = data_ultima.value
                            if data_prossima.value: 
                                aggiornamenti['prossima_manutenzione'] = data_prossima.value
                            
                            if not aggiornamenti:
                                ui.notify('Non hai inserito nessuna modifica!', type='warning')
                                return

                            try:
                                for asset in mntz_selezionati:
                                    supabase.table('inventario').update(aggiornamenti).eq('id', asset['id']).execute()
                                
                                ui.notify('✅ Dati aggiornati con successo!', type='positive')
                                dialog.close()
                                tabella.selected.clear()
                                carica_dati()
                                
                            except Exception as e:
                                ui.notify(f'❌ Errore: {e}', type='negative')

                        # Bottoni
                        with ui.row().classes('w-full justify-end gap-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Aggiorna Dati', on_click=conferma_manutenzione).classes('bg-orange-500 text-white font-bold px-4')

                    dialog.open()

                #pulsante aggiungi attrezzo, con form completo in dialog
                def aggiungi_asset(tool_selezionati=None):
                        # Apriamo la finestra di dialogo grande
                        with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-3xl p-6 rounded-lg border border-gray-600 text-white'):
                            ui.label('➕ Aggiungi Nuovo Elemento').classes('text-2xl font-bold mb-6')
                            
                            # Scarichiamo i luoghi per il menu a tendina
                            try:
                                res_luoghi = supabase.table('luoghi').select('id,ragione_sociale').execute()
                                opzioni_luoghi = {l['id']: l['ragione_sociale'] for l in res_luoghi.data}
                            except Exception as e:
                                opzioni_luoghi = {}
                                ui.notify(f'Impossibile caricare i luoghi: {e}', type='warning')

                            # GRIGLIA DEL FORM (2 Colonne)
                            with ui.grid(columns=2).classes('w-full gap-4'):
                                # Colonna 1
                                val_id = ui.input('ID Interno (es. A-020)').classes('w-full').props('dark outlined')
                                val_tipo = ui.select(['attrezzo', 'cassa'], label='Tipo', value='attrezzo').classes('w-full').props('dark outlined')
                                val_nome = ui.input('Nome / Modello').classes('w-full').props('dark outlined')
                                val_peso = ui.input('Peso (es. 5 kg)').classes('w-full').props('dark outlined')
                                val_dim = ui.input('Dimensioni (es. 30x40 cm)').classes('w-full').props('dark outlined')
                                
                                # Colonna 2
                                val_sn = ui.input('Numero Seriale Produttore').classes('w-full').props('dark outlined')
                                val_stato = ui.select(['Operativo', 'In Manutenzione', 'Guasto', 'Smarrito', 'Dismesso'], label='Stato Iniziale', value='Operativo').classes('w-full').props('dark outlined')
                                val_luogo = ui.select(opzioni_luoghi, label='Assegna a Cantiere/Luogo').classes('w-full').props('dark outlined clearable')
                                val_cassa = ui.input('Contenuto in (ID Cassa, opzionale)').classes('w-full').props('dark outlined')
                                val_desc = ui.textarea('Descrizione').classes('w-full').props('dark outlined rows=1')

                            def salva_nuovo():
                                # 1. Validazione base
                                if not val_id.value or not val_nome.value:
                                    ui.notify('I campi ID Interno e Nome sono obbligatori!', type='warning')
                                    return
                                
                                # 2. Creazione pacchetto dati
                                nuovo_asset = {
                                    'id': val_id.value.strip(),
                                    'nome': val_nome.value.strip(),
                                    'tipo': val_tipo.value,
                                    'stato': val_stato.value,
                                    'numero_seriale': val_sn.value,
                                    'posizione_attuale': val_luogo.value,
                                    'contenuto_in': val_cassa.value.strip() if val_cassa.value else None,
                                    'peso': val_peso.value,
                                    'dimensioni': val_dim.value,
                                    'descrizione': val_desc.value,
                                }
                                
                                # Pulizia: Rimuoviamo i campi lasciati vuoti per non dare fastidio al Database
                                nuovo_asset = {k: v for k, v in nuovo_asset.items() if v}

                                # 3. Salvataggio su Supabase
                                try:
                                    supabase.table('inventario').insert(nuovo_asset).execute()
                                    ui.notify('✅ Nuovo elemento registrato con successo!', type='positive')
                                    dialog.close()
                                    carica_dati() # Aggiorna la tabella all'istante
                                except Exception as e:
                                    errore_str = str(e)
                                    if "duplicate key" in errore_str:
                                        ui.notify('❌ Errore: Esiste già un elemento con questo ID!', type='negative')
                                    else:
                                        ui.notify(f'❌ Errore di salvataggio: {e}', type='negative')

                            # Pulsantiera inferiore
                            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                                ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                                ui.button('Salva Nuovo', on_click=salva_nuovo).classes('bg-green-600 text-white font-bold px-6')

                        dialog.open()


                def elimina_asset(tool_selezionati):
                        if not tool_selezionati:
                            ui.notify('Seleziona almeno un elemento da eliminare dalla tabella!', type='warning')
                            return

                        # Finestra di emergenza (Card con bordi rossi)
                        with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-md p-6 rounded-lg border-2 border-red-500 text-white'):
                            
                            with ui.row().classes('items-center gap-3 mb-4'):
                                ui.icon('warning', size='2rem').classes('text-red-500')
                                ui.label('Conferma Eliminazione').classes('text-2xl font-bold text-red-500')
                            
                            ui.label(f'Stai per eliminare DEFINITIVAMENTE {len(tool_selezionati)} elementi dal database.').classes('text-lg mb-2')
                            ui.label('Questa operazione non può essere annullata. Vuoi procedere?').classes('text-sm text-gray-300 mb-6')

                            def conferma_eliminazione():
                                try:
                                    # Esegue l'eliminazione riga per riga
                                    for asset in tool_selezionati:
                                        supabase.table('inventario').delete().eq('id', asset['id']).execute()
                                    
                                    ui.notify(f'✅ {len(tool_selezionati)} elementi eliminati.', type='positive')
                                    dialog.close()
                                    tabella.selected.clear() # Svuota i tick dalla tabella
                                    carica_dati() # Ricarica per farli sparire
                                    
                                except Exception as e:
                                    ui.notify(f'❌ Errore durante l\'eliminazione: {e}', type='negative')

                            # Pulsantiera
                            with ui.row().classes('w-full justify-between mt-4'):
                                ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                                ui.button('Sì, Elimina', on_click=conferma_eliminazione).classes('bg-red-600 text-white font-bold')

                
                # Il trucco magico: ritardiamo il download pesante di un millesimo di secondo, 
                # così l'interfaccia ha il tempo di cambiare pagina all'istante!
                ui.timer(0.1, carica_dati, once=True)





            elif scelta == "Spostamenti / DDT":
                import datetime
                import uuid

                container = ui.column().classes('w-full min-w-0')
                
                # 1. VARIABILI GLOBALI UNIVOCHE PER QUESTA PAGINA
                global tabella_spostamenti
                tabella_spostamenti = None

                stato = {
                    'luoghi_dict': {},
                    'inventario_dict': {},
                    'ddt_raw': [],
                    'movimenti_raw': [],
                    'ddt_righe': [],
                    'nuovo_ddt_scansioni': [] 
                }

                # 2. FUNZIONE DI CARICAMENTO DATI RINOMINATA
                def carica_dati_spostamenti():
                    global tabella_spostamenti
                    try:
                        def estrai(res):
                            if isinstance(res, list): return res
                            if isinstance(res, dict): return res.get('data', [])
                            if hasattr(res, 'data'): return res.data or []
                            return []

                        # Carichiamo anagrafiche base
                        res_l = supabase.table('luoghi').select('id, ragione_sociale').execute()
                        stato['luoghi_dict'] = {l['id']: l['ragione_sociale'] for l in estrai(res_l)}
                        
                        res_i = supabase.table('inventario').select('*').execute()
                        stato['inventario_dict'] = {i['id']: i for i in estrai(res_i)}

                        # Carichiamo i DDT
                        res_ddt = supabase.table('ddt').select('*').order('data_emissione', desc=True).execute()
                        stato['ddt_raw'] = estrai(res_ddt)

                        # Carichiamo movimenti
                        res_mov = supabase.table('movimenti').select('*').execute()
                        stato['movimenti_raw'] = estrai(res_mov)
                        
                        righe = []

                        # Inseriamo i DDT formali
                        for d in stato['ddt_raw']:
                            righe.append({
                                'id': d['id'],
                                'is_ddt': True,
                                'numero': d.get('numero', '-'),
                                'data': datetime.datetime.strptime(str(d.get('data_emissione'))[:10], '%Y-%m-%d').strftime('%d/%m/%Y') if d.get('data_emissione') else '-',
                                'partenza': stato['luoghi_dict'].get(d.get('luogo_partenza'), 'Sconosciuto'),
                                'arrivo': stato['luoghi_dict'].get(d.get('luogo_arrivo'), 'Sconosciuto'),
                                'vettore': d.get('vettore') or d.get('utente_nome') or '-',
                                'causale': d.get('causale', ''),
                                'note': d.get('note', '')
                            })

                        # Inseriamo gli Spostamenti Diretti
                        untracked_moves = [m for m in stato['movimenti_raw'] if not m.get('ddt_id')]
                        for m in untracked_moves:
                            inv = stato['inventario_dict'].get(m.get('asset_id'), {})
                            nome_attr = inv.get('articolo') or inv.get('nome') or inv.get('descrizione') or f"Articolo {m.get('asset_id')}"
                            
                            righe.append({
                                'id': m['id'],
                                'is_ddt': False,
                                'numero': f"📦 DIRETTO: {nome_attr}",
                                'data': datetime.datetime.strptime(str(m.get('data_move'))[:10], '%Y-%m-%d').strftime('%d/%m/%Y') if m.get('data_move') else '-',
                                'partenza': stato['luoghi_dict'].get(m.get('da_luogo'), 'Sconosciuto'),
                                'arrivo': stato['luoghi_dict'].get(m.get('a_luogo'), 'Sconosciuto'),
                                'vettore': m.get('utente_nome') or '-',
                                'causale': 'Spostamento Rapido',
                                'note': m.get('note', '')
                            })
                        
                        stato['ddt_righe'] = righe
                        
                        # --- IL TRUCCO DELL'AGGIORNAMENTO MORBIDO ---
                        if tabella_spostamenti is not None:
                            try:
                                tabella_spostamenti.rows = righe
                                tabella_spostamenti.update()
                            except Exception:
                                pass
                        else:
                            # Se la tabella non esiste, disegniamo la grafica
                            renderizza_interfaccia_spostamenti()

                    except Exception as e:
                        ui.notify(f"Errore caricamento dati: {e}", type="negative")

                # --- FUNZIONI DI SUPPORTO (aggiornate con la nuova variabile) ---
                def filtra_tabella():
                    termine = barra_ricerca.value.lower() if barra_ricerca.value else ""
                    if not termine:
                        tabella_spostamenti.rows = stato['ddt_righe']
                    else:
                        tabella_spostamenti.rows = [
                            r for r in stato['ddt_righe']
                            if termine in str(r['numero']).lower() or
                               termine in str(r['partenza']).lower() or
                               termine in str(r['arrivo']).lower() or
                               termine in str(r['vettore']).lower() or
                               termine in str(r['causale']).lower()
                        ]
                    tabella_spostamenti.update()

                def apri_modifica(riga):
                    if riga['is_ddt']:
                        ddt_dati = next((d for d in stato['ddt_raw'] if d['id'] == riga['id']), None)
                        if not ddt_dati: return
                        
                        with ui.dialog() as dialog_edit, ui.card().classes('min-w-[500px] bg-gray-900 border border-gray-700'):
                            ui.label(f"Modifica DDT: {ddt_dati.get('numero')}").classes('text-xl font-bold text-white mb-4')
                            num_input = ui.input('Numero DDT', value=ddt_dati.get('numero')).classes('w-full mb-2').props('dark')
                            data_input = ui.input('Data Emissione', value=ddt_dati.get('data_emissione')).classes('w-full mb-2').props('type="date" dark')
                            partenza_input = ui.select(stato['luoghi_dict'], label='Partenza', value=ddt_dati.get('luogo_partenza')).classes('w-full mb-2').props('dark')
                            arrivo_input = ui.select(stato['luoghi_dict'], label='Destinazione', value=ddt_dati.get('luogo_arrivo')).classes('w-full mb-2').props('dark')
                            vettore_input = ui.input('Vettore', value=ddt_dati.get('vettore')).classes('w-full mb-2').props('dark')
                            causale_input = ui.select(['Vendita', 'Noleggio', 'Reso da Noleggio', 'Trasferimento Attrezzatura', 'Riparazione'], value=ddt_dati.get('causale'), label='Causale').classes('w-full mb-4').props('dark')                            
                            
                            def salva_modifiche_ddt():
                                supabase.table('ddt').update({
                                    'numero': num_input.value, 'data_emissione': data_input.value,
                                    'luogo_partenza': partenza_input.value, 'luogo_arrivo': arrivo_input.value,
                                    'vettore': vettore_input.value, 'causale': causale_input.value
                                }).eq('id', riga['id']).execute()
                                ui.notify('DDT aggiornato!', type='positive')
                                dialog_edit.close()
                                carica_dati_spostamenti() # Chiamata aggiornata
                                
                            with ui.row().classes('w-full justify-end gap-3'):
                                ui.button('Annulla', on_click=dialog_edit.close).props('outline color="white"')
                                ui.button('Salva', on_click=salva_modifiche_ddt, color='green-600').classes('font-bold')
                        dialog_edit.open()
                    else:
                        mov_dati = next((m for m in stato['movimenti_raw'] if m['id'] == riga['id']), None)
                        if not mov_dati: return
                        
                        with ui.dialog() as dialog_edit, ui.card().classes('min-w-[500px] bg-gray-900 border border-gray-700'):
                            ui.label("Modifica Spostamento Diretto").classes('text-xl font-bold text-white mb-4')
                            data_input = ui.input('Data Spostamento', value=mov_dati.get('data_move')).classes('w-full mb-2').props('type="date" dark')
                            partenza_input = ui.select(stato['luoghi_dict'], label='Partenza', value=mov_dati.get('da_luogo')).classes('w-full mb-2').props('dark')
                            arrivo_input = ui.select(stato['luoghi_dict'], label='Destinazione', value=mov_dati.get('a_luogo')).classes('w-full mb-2').props('dark')
                            vettore_input = ui.input('Operatore', value=mov_dati.get('utente_nome')).classes('w-full mb-2').props('dark')
                            note_input = ui.textarea('Note', value=mov_dati.get('note')).classes('w-full mb-4').props('dark')
                            
                            def salva_modifiche_mov():
                                supabase.table('movimenti').update({
                                    'data_move': data_input.value, 'da_luogo': partenza_input.value,
                                    'a_luogo': arrivo_input.value, 'utente_nome': vettore_input.value, 'note': note_input.value
                                }).eq('id', riga['id']).execute()
                                
                                supabase.table('inventario').update({'posizione_attuale': arrivo_input.value}).eq('id', mov_dati['asset_id']).execute()
                                ui.notify('Spostamento aggiornato!', type='positive')
                                dialog_edit.close()
                                carica_dati_spostamenti() # Chiamata aggiornata
                                
                            with ui.row().classes('w-full justify-end gap-3'):
                                ui.button('Annulla', on_click=dialog_edit.close).props('outline color="white"')
                                ui.button('Salva', on_click=salva_modifiche_mov, color='green-600').classes('font-bold')
                        dialog_edit.open()

                def stampa_selezionato():
                    if not tabella_spostamenti.selected:
                        ui.notify('Seleziona una riga con il checkbox prima di premere Stampa!', type='warning')
                        return
                    riga = tabella_spostamenti.selected[0]
                    
                    if riga['is_ddt']:
                        res_items = supabase.table('movimenti').eq('ddt_id', riga['id']).execute()
                        items_mov = res_items.data if hasattr(res_items, 'data') else []
                        
                        with ui.dialog() as diag_print, ui.card().classes('bg-white w-full max-w-4xl p-6 rounded-lg text-black printable-sheet'):
                            with ui.row().classes('w-full justify-between items-end border-b-4 border-black pb-4 mb-4'):
                                ui.label('DSV LOGISTICS').classes('text-2xl font-black tracking-wider text-black')
                                ui.label(f"DOCUMENTO DI TRASPORTO").classes('text-xl font-bold text-black')
                            
                            with ui.grid(columns=2).classes('w-full gap-4 mb-6 text-sm text-black'):
                                with ui.column():
                                    ui.label(f"Numero documento: {riga['numero']}").classes('font-bold')
                                    ui.label(f"Data emissione: {riga['data']}")
                                    ui.label(f"Causale: {riga['causale']}")
                                with ui.column():
                                    ui.label(f"Da: {riga['partenza']}")
                                    ui.label(f"A: {riga['arrivo']}")
                                    ui.label(f"Vettore: {riga['vettore']}")
                            
                            ui.label('ELENCO MATERIALI TRASPORTATI').classes('font-bold border-b border-black pb-1 mb-2 text-black')
                            with ui.column().classes('w-full gap-1 border border-black p-2'):
                                for idx, it in enumerate(items_mov):
                                    inv_item = stato['inventario_dict'].get(it['asset_id'], {})
                                    nome_art = inv_item.get('articolo') or inv_item.get('nome') or inv_item.get('descrizione') or it['asset_id']
                                    ui.label(f"{idx+1}. [{it['asset_id']}] {nome_art}").classes('text-black text-sm')
                                    
                            with ui.row().classes('w-full justify-end gap-3 mt-6 no-print'):
                                ui.button('Chiudi', on_click=diag_print.close).props('outline color="black"')
                                ui.button('Avvia Stampa', icon='print', on_click=lambda: ui.run_javascript('window.print()')).classes('bg-green-600 text-white font-bold')
                        diag_print.open()
                    else:
                        with ui.dialog() as diag_print, ui.card().classes('bg-white w-full max-w-4xl p-6 rounded-lg text-black printable-sheet'):
                            with ui.row().classes('w-full justify-between items-end border-b-4 border-black pb-4 mb-4'):
                                ui.label('DSV LOGISTICS').classes('text-2xl font-black tracking-wider text-black')
                                ui.label(f"RICEVUTA SPOSTAMENTO DIRETTO").classes('text-xl font-bold text-black')
                            
                            with ui.column().classes('w-full gap-2 text-sm text-black mt-4'):
                                ui.label(f"Oggetto Spostato: {riga['numero']}").classes('text-lg font-bold')
                                ui.label(f"Data Trasferimento: {riga['data']}")
                                ui.label(f"Luogo Partenza: {riga['partenza']}")
                                ui.label(f"Luogo Destinazione: {riga['arrivo']}")
                                ui.label(f"Eseguito da (Operatore): {riga['vettore']}")
                                if riga.get('note'):
                                    ui.label(f"Note: {riga['note']}").classes('italic mt-2 text-gray-700')
                                    
                            with ui.row().classes('w-full justify-end gap-3 mt-6 no-print'):
                                ui.button('Chiudi', on_click=diag_print.close).props('outline color="black"')
                                ui.button('Avvia Stampa', icon='print', on_click=lambda: ui.run_javascript('window.print()')).classes('bg-green-600 text-white font-bold')
                        diag_print.open()

                def apri_wizard_ddt():
                    pass # Mantenuto intatto il corpo del tuo wizard qui sotto...

                # 3. LA NUOVA FUNZIONE PER CREARE L'INTERFACCIA
                def renderizza_interfaccia_spostamenti():
                    global tabella_spostamenti
                    container.clear()
                    
                    with container:
                        with ui.row().classes('w-full justify-between items-center no-wrap mb-4 mt-4'):
                            global barra_ricerca
                            barra_ricerca = ui.input('Cerca DDT...', on_change=filtra_tabella).props('input-style="color: white" outlined clearable rounded dense').classes('custom-input w-full max-w-md')
                            
                            with ui.row().classes('gap-3 items-center no-wrap'):
                                ui.button(icon="print", on_click=stampa_selezionato, color='blue-600').props('round outline color="white"').tooltip('Stampa Elemento Selezionato')
                                ui.button(icon="add", on_click=apri_wizard_ddt, color='green-600').props('round outline color="positive"').tooltip('Crea DDT')

                        colonne_ddt = [
                            {'name': 'edit', 'label': '', 'field': 'edit', 'align': 'center'},
                            {'name': 'numero', 'label': 'Nr. Documento / Tipo', 'field': 'numero', 'sortable': True, 'align': 'left', 'classes': 'font-bold text-base text-white'},
                            {'name': 'data', 'label': 'Data', 'field': 'data', 'sortable': True, 'align': 'left'},
                            {'name': 'partenza', 'label': 'Partenza', 'field': 'partenza', 'sortable': True, 'align': 'left'},
                            {'name': 'arrivo', 'label': 'Destinazione', 'field': 'arrivo', 'sortable': True, 'align': 'left'},
                            {'name': 'vettore', 'label': 'Vettore / Autista', 'field': 'vettore', 'align': 'left'},
                            {'name': 'causale', 'label': 'Causale', 'field': 'causale', 'align': 'left'}
                        ]

                        # Assegniamo la tabella alla variabile globale corretta
                        tabella_spostamenti = ui.table(columns=colonne_ddt, rows=stato['ddt_righe'], row_key='id').classes('bg-transparent data-table text-white w-full min-w-[1000px]').props('dense flat bordered selection="single"')
                        
                        tabella_spostamenti.add_slot('body-cell-edit', '''
                            <q-td :props="props">
                                <q-btn size="sm" round outline color="white" icon="edit" @click="() => $parent.$emit('apri_edit', props.row)" />
                            </q-td>
                        ''')

                        tabella_spostamenti.on('apri_edit', lambda e: apri_modifica(e.args))

                # 4. AVVIO CON CARICAMENTO ASINCRONO E ROTELINA
                with container:
                    ui.spinner('dots', size='3em', color='blue').classes('mx-auto mt-20')
                    
                ui.timer(0.1, carica_dati_spostamenti, once=True)





            elif scelta == "Manutenzioni":
                import datetime
                import uuid

                # --- CONTENITORE PRINCIPALE ---
                container = ui.column().classes('w-full min-w-0')

                # --- VARIABILI GLOBALI UNIVOCHE ---
                global tabella_manutenzioni
                tabella_manutenzioni = None
                global barra_ricerca_manutenzioni
                barra_ricerca_manutenzioni = None
                global filtro_scadenze_manutenzioni
                filtro_scadenze_manutenzioni = None

                # --- MEMORIA DATI ---
                stato = {
                    'mezzi_dict': {},
                    'inventario_dict': {},
                    'luoghi_dict': {},
                    'manutenzioni_raw': [],
                    'righe_tabella_tutte': []
                }

                # --- FUNZIONE DI CARICAMENTO DATI ---
                def carica_dati_manutenzioni():
                    global tabella_manutenzioni
                    try:
                        # 1. Scarico le anagrafiche per i riferimenti
                        res_m = supabase.table('mezzi').select('*').execute()
                        stato['mezzi_dict'] = {m['id']: m for m in (res_m.data if hasattr(res_m, 'data') else [])}
                        
                        res_i = supabase.table('inventario').select('*').execute()
                        stato['inventario_dict'] = {i['id']: i for i in (res_i.data if hasattr(res_i, 'data') else [])}
                        
                        res_l = supabase.table('luoghi').select('id, ragione_sociale').execute()
                        stato['luoghi_dict'] = {l['id']: l['ragione_sociale'] for l in (res_l.data if hasattr(res_l, 'data') else [])}

                        # 2. Scarico le manutenzioni e costruisco le righe per la tabella
                        res_man = supabase.table('manutenzioni').select('*').execute()
                        stato['manutenzioni_raw'] = res_man.data if hasattr(res_man, 'data') else []
                        
                        righe = []
                        oggi = datetime.date.today()

                        for m in stato['manutenzioni_raw']:
                            if m.get('mezzo_id'):
                                mezzo = stato['mezzi_dict'].get(m['mezzo_id'], {})
                                oggetto = mezzo.get('nome_modello', 'Mezzo Sconosciuto')
                                categoria = 'Veicolo / Mezzo'
                            else:
                                inv = stato['inventario_dict'].get(m.get('inventario_id'), {})
                                oggetto = inv.get('articolo') or inv.get('nome') or inv.get('descrizione') or 'Attrezzo Sconosciuto'
                                categoria = 'Attrezzatura'
                            
                            fornitore = stato['luoghi_dict'].get(m.get('fornitore_id'), '-')
                            
                            # Calcolo giorni mancanti alla scadenza per colorare la riga
                            scadenza_str = m.get('data_scadenza')
                            giorni_mancanti = 9999
                            colore_scadenza = 'grey'
                            
                            if scadenza_str:
                                scad = datetime.datetime.strptime(str(scadenza_str)[:10], '%Y-%m-%d').date()
                                giorni_mancanti = (scad - oggi).days
                                if giorni_mancanti < 0:
                                    colore_scadenza = 'red' 
                                elif giorni_mancanti <= 30:
                                    colore_scadenza = 'orange' 
                                elif giorni_mancanti <= 90:
                                    colore_scadenza = 'yellow-9' 
                                else:
                                    colore_scadenza = 'green' 
                            else:
                                scadenza_str = "Nessuna"

                            data_esec = m.get('data_esecuzione')

                            righe.append({
                                'id': m['id'],
                                'oggetto': oggetto,
                                'categoria': categoria,
                                'tipo': m.get('tipo_intervento', ''),
                                'esecuzione': datetime.datetime.strptime(str(data_esec)[:10], '%Y-%m-%d').strftime('%d/%m/%Y') if data_esec else '-',
                                'scadenza_str': datetime.datetime.strptime(str(scadenza_str)[:10], '%Y-%m-%d').strftime('%d/%m/%Y') if scadenza_str != "Nessuna" else '-',
                                'giorni_mancanti': giorni_mancanti,
                                'colore_scadenza': colore_scadenza,
                                'fornitore': fornitore,
                                'note': m.get('note', '')
                            })

                        # Ordiniamo di base per le scadenze più urgenti
                        stato['righe_tabella_tutte'] = sorted(righe, key=lambda x: x['giorni_mancanti'])
                        
                        # --- IL TRUCCO DELL'AGGIORNAMENTO MORBIDO ---
                        if tabella_manutenzioni is not None:
                            try:
                                applica_filtri_manutenzioni()
                            except Exception:
                                pass
                        else:
                            # Se è il primo avvio, disegna l'interfaccia
                            renderizza_interfaccia_manutenzioni()
                        
                    except Exception as e:
                        ui.notify(f"❌ Errore durante la lettura dei dati: {e}", type="negative")
                        print(f"Errore: {e}")

                # --- FUNZIONI DI SUPPORTO ---
                def applica_filtri_manutenzioni(e=None):
                    global tabella_manutenzioni, barra_ricerca_manutenzioni, filtro_scadenze_manutenzioni
                    
                    if not tabella_manutenzioni: return
                    
                    termine = barra_ricerca_manutenzioni.value.lower() if barra_ricerca_manutenzioni and barra_ricerca_manutenzioni.value else ""
                    limite_giorni = filtro_scadenze_manutenzioni.value if filtro_scadenze_manutenzioni else 'tutte'
                    
                    righe_filtrate = []
                    for r in stato['righe_tabella_tutte']:
                        if termine and termine not in str(r['oggetto']).lower() and termine not in str(r['tipo']).lower() and termine not in str(r['note']).lower():
                            continue
                            
                        gg = r['giorni_mancanti']
                        if limite_giorni == 'scadute' and gg >= 0:
                            continue
                        elif limite_giorni == '30' and gg > 30:
                            continue
                        elif limite_giorni == '60' and gg > 60:
                            continue
                        elif limite_giorni == '90' and gg > 90:
                            continue
                            
                        righe_filtrate.append(r)
                        
                    tabella_manutenzioni.rows = righe_filtrate
                    tabella_manutenzioni.update()

                def elimina_manutenzione(riga):
                    try:
                        supabase.table('manutenzioni').delete().eq('id', riga['id']).execute()
                        ui.notify('Intervento eliminato', type='positive')
                        carica_dati_manutenzioni()
                    except Exception as e:
                        ui.notify(f'Errore eliminazione: {e}', type='negative')

                def apri_dialog_mezzo():
                    with ui.dialog() as dialog, ui.card().classes('min-w-[400px] bg-gray-900 border border-gray-700'):
                        ui.label('Immatricola Nuovo Mezzo').classes('text-2xl font-bold text-white mb-4')
                        nome = ui.input('Modello (es. Furgone Ducato)').classes('w-full mb-2').props('dark')
                        targa = ui.input('Targa (opzionale)').classes('w-full mb-2').props('dark')
                        tipo = ui.select(['Auto', 'Furgone', 'Mezzo Pesante', 'Sollevamento', 'Noleggio'], label='Tipologia').classes('w-full mb-4').props('dark')
                        
                        def salva_mezzo():
                            if not nome.value: return
                            supabase.table('mezzi').insert({
                                'id': str(uuid.uuid4()), 'nome_modello': nome.value, 'targa': targa.value, 'tipologia': tipo.value, 'attivo': True
                            }).execute()
                            ui.notify('Mezzo salvato!', type='positive')
                            dialog.close()
                            carica_dati_manutenzioni()
                            
                        with ui.row().classes('w-full justify-end gap-3'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Salva', on_click=salva_mezzo, color='primary').classes('font-bold')
                    dialog.open()

                def apri_dialog_manutenzione():
                    with ui.dialog() as dialog, ui.card().classes('min-w-[500px] bg-gray-900 border border-gray-700'):
                        ui.label('Registra Intervento o Guasto').classes('text-2xl font-bold text-white mb-4')
                        
                        categoria = ui.select({'mezzo': '🚗 Veicolo / Parco Mezzi', 'inventario': '🧰 Attrezzatura (Inventario)'}, value='mezzo', label='Su cosa devi intervenire?').classes('w-full mb-3').props('dark')
                        tendina_oggetto = ui.select({}, label='Seleziona Oggetto', with_input=True).classes('w-full mb-3').props('dark')
                        
                        def aggiorna_tendina_oggetti(e):
                            tendina_oggetto.value = None
                            if e.value == 'mezzo':
                                tendina_oggetto.options = {m_id: m_dati.get('nome_modello') for m_id, m_dati in stato['mezzi_dict'].items()}
                            else:
                                tendina_oggetto.options = {i_id: (i_dati.get('articolo') or i_dati.get('nome') or i_dati.get('descrizione')) for i_id, i_dati in stato['inventario_dict'].items()}
                            tendina_oggetto.update()
                        
                        categoria.on_change(aggiorna_tendina_oggetti)
                        aggiorna_tendina_oggetti(categoria)

                        tipo_int = ui.input('Tipo (es. Tagliando, Riparazione Guasto, ecc.)').classes('w-full mb-3').props('dark')
                        
                        with ui.row().classes('w-full gap-4 mb-3'):
                            data_esec = ui.input('Data Esecuzione').classes('w-1/2').props('type="date" dark')
                            data_scad = ui.input('Data Prossima Scadenza').classes('w-1/2').props('type="date" dark')
                        
                        fornitore = ui.select(stato['luoghi_dict'], label='Officina / Fornitore (Dai Luoghi)', clearable=True).classes('w-full mb-3').props('dark')
                        note = ui.textarea('Note').classes('w-full mb-4').props('dark')
                        
                        def salva_manutenzione():
                            if not tendina_oggetto.value or not tipo_int.value:
                                ui.notify('Compila Oggetto e Tipo Intervento', type='warning')
                                return
                                
                            nuovo_record = {
                                'id': str(uuid.uuid4()),
                                'tipo_intervento': tipo_int.value,
                                'data_esecuzione': data_esec.value if data_esec.value else None,
                                'data_scadenza': data_scad.value if data_scad.value else None,
                                'fornitore_id': fornitore.value,
                                'note': note.value,
                            }
                            
                            if categoria.value == 'mezzo':
                                nuovo_record['mezzo_id'] = tendina_oggetto.value
                            else:
                                nuovo_record['inventario_id'] = tendina_oggetto.value
                                
                            supabase.table('manutenzioni').insert(nuovo_record).execute()
                            ui.notify('Registrato con successo!', type='positive')
                            dialog.close()
                            carica_dati_manutenzioni()

                        with ui.row().classes('w-full justify-end gap-3'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Salva Dati', on_click=salva_manutenzione, color='green-600').classes('font-bold shadow-lg')
                    dialog.open()

                # --- LA NUOVA FUNZIONE PER CREARE L'INTERFACCIA ---
                def renderizza_interfaccia_manutenzioni():
                    global tabella_manutenzioni, barra_ricerca_manutenzioni, filtro_scadenze_manutenzioni
                    container.clear()
                    
                    with container:
                        with ui.row().classes('w-full items-center no-wrap gap-4 mb-4 mt-4'):
                            
                            barra_ricerca_manutenzioni = ui.input('Cerca mezzo o guasto...', on_change=applica_filtri_manutenzioni) \
                                .props('input-style="color: white" outlined clearable rounded dense') \
                                .classes('custom-input min-w-[200px] w-64') 
                            
                            filtro_scadenze_manutenzioni = ui.select(
                                {'tutte': 'Tutte le scadenze', 'scadute': '🔴 Solo Scadute', '30': '🟡 Entro 30 giorni', '60': 'Entro 60 giorni', '90': 'Entro 90 giorni'},
                                label='Seleziona scadenza...', value='tutte', on_change=applica_filtri_manutenzioni
                            ).props('input-style="color: white" outlined clearable rounded dense').classes('custom-input min-w-[200px] w-64')
                            
                            ui.space()
                            
                            ui.button(icon="local_shipping", on_click=apri_dialog_mezzo, color='blue-700') \
                                .props('round outline color="white"').tooltip('Crea Mezzo')
                            ui.button(icon="build", on_click=apri_dialog_manutenzione, color='green-600') \
                                .props('round outline color="positive"').tooltip('Crea Intervento')

                        colonne = [
                            {'name': 'oggetto', 'label': 'Oggetto', 'field': 'oggetto', 'sortable': True, 'align': 'left', 'classes': 'font-bold text-base text-white'},
                            {'name': 'categoria', 'label': 'Categoria', 'field': 'categoria', 'sortable': True, 'align': 'left'},
                            {'name': 'tipo', 'label': 'Stato / Intervento', 'field': 'tipo', 'sortable': True, 'align': 'left', 'classes': 'text-gray-300'},
                            {'name': 'esecuzione', 'label': 'Data Esecuz.', 'field': 'esecuzione', 'sortable': True, 'align': 'center'},
                            {'name': 'scadenza', 'label': 'Prossima Scadenza', 'field': 'scadenza_str', 'sortable': True, 'align': 'center'},
                            {'name': 'fornitore', 'label': 'Fornitore', 'field': 'fornitore', 'align': 'left'},
                            {'name': 'azioni', 'label': '', 'field': 'azioni', 'align': 'right'}
                        ]
                        
                        tabella_manutenzioni = ui.table(columns=colonne, rows=[], row_key='id').classes('bg-transparent data-table text-white w-full min-w-[1000px]').props('dense flat bordered')
                        
                        tabella_manutenzioni.add_slot('body-cell-scadenza', '''
                            <q-td :props="props">
                                <q-badge :color="props.row.colore_scadenza" class="text-sm font-bold p-1">
                                    {{ props.value }}
                                </q-badge>
                            </q-td>
                        ''')
                        
                        tabella_manutenzioni.add_slot('body-cell-azioni', '''
                            <q-td :props="props">
                                <q-btn flat round color="red" icon="delete" size="sm" @click="() => $parent.$emit('elimina', props.row)" />
                            </q-td>
                        ''')
                        tabella_manutenzioni.on('elimina', lambda e: elimina_manutenzione(e.args))
                        
                        # Popoliamo la tabella appena creata richiamando i filtri (che ora sono collegati correttamente alle globali)
                        applica_filtri_manutenzioni()

                # --- AVVIO CON CARICAMENTO ASINCRONO ---
                with container:
                    ui.spinner('dots', size='3em', color='green').classes('mx-auto mt-20')
                
                ui.timer(0.1, carica_dati_manutenzioni, once=True)



            elif scelta == "Luoghi":
                import uuid
                import urllib.parse

                luoghi_container = ui.column().classes('w-full min-w-0')
                
                # --- VARIABILI GLOBALI UNIVOCHE ---
                global tutti_i_luoghi, tabella_luoghi, barra_ricerca_luoghi
                tutti_i_luoghi = []
                tabella_luoghi = None
                barra_ricerca_luoghi = None

                # --- CARICAMENTO DATI ---
                def carica_luoghi():
                    global tutti_i_luoghi, tabella_luoghi
                    try:
                        # Scarichiamo tutti i dati della tabella luoghi
                        res = supabase.table('luoghi').select('*').execute()
                        tutti_i_luoghi = res.data if hasattr(res, 'data') else []
                        
                        # --- IL TRUCCO DELL'AGGIORNAMENTO MORBIDO ---
                        if tabella_luoghi is not None:
                            try:
                                applica_filtri_luoghi()
                            except Exception:
                                pass
                        else:
                            # Se è il primo avvio, disegniamo la grafica
                            renderizza_interfaccia_luoghi()
                            
                    except Exception as e:
                        ui.notify(f"Errore caricamento luoghi: {e}", type='negative')

                # --- FUNZIONE DI RICERCA ---
                def applica_filtri_luoghi(e=None):
                    global tabella_luoghi, barra_ricerca_luoghi
                    if not tabella_luoghi: return
                    
                    termine = barra_ricerca_luoghi.value.lower().strip() if barra_ricerca_luoghi and barra_ricerca_luoghi.value else ""
                    
                    if not termine:
                        tabella_luoghi.rows = tutti_i_luoghi
                    else:
                        tabella_luoghi.rows = [
                            riga for riga in tutti_i_luoghi
                            if termine in str(riga.get('ragione_sociale', '')).lower() 
                            or termine in str(riga.get('indirizzo_sede', '')).lower()
                            or termine in str(riga.get('riferimento', '')).lower()
                        ]
                    tabella_luoghi.update()

                # --- FUNZIONI DEI PULSANTI ---
                def aggiungi_luogo():
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-3xl p-6 rounded-lg border border-gray-600 text-white'):
                        ui.label('🏗️ Nuovo Luogo / Cantiere').classes('text-2xl font-bold mb-4')
                        
                        opzioni_tipo_luogo = ['deposito', 'cantiere', 'ufficio', 'fornitore', 'laboratorio', 'altro']

                        with ui.grid(columns=2).classes('w-full gap-4'):
                            val_rs = ui.input('Ragione Sociale *').classes('w-full').props('dark outlined')
                            val_tipo = ui.select(opzioni_tipo_luogo, label='Tipo *', value='cantiere').classes('w-full').props('dark outlined')                            
                            val_ind_sede = ui.input('Indirizzo Sede').classes('w-full').props('dark outlined')
                            val_piva = ui.input('Partita IVA / C.F.').classes('w-full').props('dark outlined')
                            val_tel = ui.input('Telefono').classes('w-full').props('dark outlined')
                            
                            val_rif = ui.input('Ns. Riferimento (Contatto)').classes('w-full').props('dark outlined')
                            val_mail = ui.input('Email').classes('w-full').props('dark outlined')
                            val_ind_cons = ui.input('Indirizzo Consegna (se diverso)').classes('w-full').props('dark outlined')
                            val_note = ui.textarea('Note').classes('w-full').props('dark outlined rows=3')
                        
                        def salva():
                            if not val_rs.value:
                                ui.notify('La Ragione Sociale è obbligatoria!', type='warning')
                                return
                            
                            nuovo_dato = {
                                'id': str(uuid.uuid4()), 
                                'ragione_sociale': val_rs.value.strip(),
                                'tipo': val_tipo.value.strip() if val_tipo.value else 'cantiere',
                                'indirizzo_sede': val_ind_sede.value.strip() if val_ind_sede.value else None,
                                'indirizzo_consegna': val_ind_cons.value.strip() if val_ind_cons.value else None,
                                'piva': val_piva.value.strip() if val_piva.value else None,
                                'riferimento': val_rif.value.strip() if val_rif.value else None,
                                'telefono': val_tel.value.strip() if val_tel.value else None,
                                'mail': val_mail.value.strip() if val_mail.value else None,
                                'note': val_note.value.strip() if val_note.value else None
                            }
                            
                            try:
                                supabase.table('luoghi').insert(nuovo_dato).execute()
                                ui.notify('✅ Luogo aggiunto con successo!', type='positive')
                                dialog.close()
                                carica_luoghi()
                            except Exception as e:
                                errore_str = str(e)
                                if "duplicate key" in errore_str or "unique constraint" in errore_str.lower():
                                    ui.notify('❌ Errore: Esiste già un luogo con questa Ragione Sociale!', type='negative')
                                else:
                                    ui.notify(f'❌ Errore: {e}', type='negative')

                        with ui.row().classes('w-full justify-end gap-4 mt-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Salva Nuovo', on_click=salva).classes('bg-green-600 text-white font-bold px-6')
                    
                    dialog.open()

                def modifica_luogo(riga):
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-3xl p-6 rounded-lg border border-gray-600 text-white'):
                        ui.label('✏️ Modifica Luogo').classes('text-2xl font-bold mb-4')
                        
                        opzioni_tipo_luogo = ['deposito', 'cantiere', 'ufficio', 'fornitore', 'laboratorio', 'altro']

                        with ui.grid(columns=2).classes('w-full gap-4'):
                            val_rs = ui.input('Ragione Sociale *', value=riga.get('ragione_sociale')).classes('w-full').props('dark outlined')
                            val_tipo = ui.select(opzioni_tipo_luogo, label='Tipo *', value=riga.get('tipo', 'cantiere')).classes('w-full').props('dark outlined')
                            val_ind_sede = ui.input('Indirizzo Sede', value=riga.get('indirizzo_sede')).classes('w-full').props('dark outlined')
                            val_piva = ui.input('Partita IVA / C.F.', value=riga.get('piva')).classes('w-full').props('dark outlined')
                            val_tel = ui.input('Telefono', value=riga.get('telefono')).classes('w-full').props('dark outlined')
                            val_rif = ui.input('Ns. Riferimento (Contatto)', value=riga.get('riferimento')).classes('w-full').props('dark outlined')
                            val_mail = ui.input('Email', value=riga.get('mail')).classes('w-full').props('dark outlined')
                            val_ind_cons = ui.input('Indirizzo Consegna', value=riga.get('indirizzo_consegna')).classes('w-full').props('dark outlined')
                            val_note = ui.textarea('Note', value=riga.get('note')).classes('w-full').props('dark outlined rows=3')

                        def aggiorna():
                            if not val_rs.value:
                                ui.notify('La Ragione Sociale non può essere vuota!', type='warning')
                                return
                                
                            aggiornamenti = {
                                'ragione_sociale': val_rs.value.strip(),
                                'tipo': val_tipo.value.strip() if val_tipo.value else None,
                                'indirizzo_sede': val_ind_sede.value.strip() if val_ind_sede.value else None,
                                'indirizzo_consegna': val_ind_cons.value.strip() if val_ind_cons.value else None,
                                'piva': val_piva.value.strip() if val_piva.value else None,
                                'riferimento': val_rif.value.strip() if val_rif.value else None,
                                'telefono': val_tel.value.strip() if val_tel.value else None,
                                'mail': val_mail.value.strip() if val_mail.value else None,
                                'note': val_note.value.strip() if val_note.value else None
                            }
                            
                            try:
                                supabase.table('luoghi').update(aggiornamenti).eq('id', riga['id']).execute()
                                ui.notify('✅ Luogo aggiornato!', type='positive')
                                dialog.close()
                                carica_luoghi()
                            except Exception as e:
                                ui.notify(f'❌ Errore durante l\'aggiornamento: {e}', type='negative')

                        with ui.row().classes('w-full justify-end gap-4 mt-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Aggiorna Dati', on_click=aggiorna).classes('bg-blue-600 text-white font-bold px-6')
                    dialog.open()                    
                      
                def elimina_luoghi(selezionati):
                    if not selezionati:
                        ui.notify('Seleziona almeno un luogo da eliminare!', type='warning')
                        return

                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-md p-6 rounded-lg border-2 border-red-500 text-white'):
                        ui.label('Conferma Eliminazione').classes('text-2xl font-bold text-red-500 mb-2')
                        ui.label('Stai eliminando dei luoghi. ATTENZIONE: Se un attrezzo si trova attualmente in questo cantiere, l\'operazione verrà bloccata dal database.').classes('mb-4')
                        
                        def conferma():
                            try:
                                for luogo in selezionati:
                                    supabase.table('luoghi').delete().eq('id', luogo['id']).execute()
                                ui.notify(f'✅ {len(selezionati)} luoghi eliminati.', type='positive')
                                dialog.close()
                                
                                # Svuotiamo le spunte in modo sicuro
                                try:
                                    tabella_luoghi.selected.clear()
                                except:
                                    pass
                                    
                                carica_luoghi()
                            except Exception as e:
                                errore = str(e).lower()
                                if "foreign key" in errore or "violates" in errore:
                                    ui.notify('❌ Impossibile eliminare: ci sono degli attrezzi attualmente assegnati a questo luogo!', type='negative', position='top')
                                else:
                                    ui.notify(f'❌ Errore: {e}', type='negative')

                        with ui.row().classes('w-full justify-between mt-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Sì, Elimina', on_click=conferma).classes('bg-red-600 text-white font-bold')
                    dialog.open()

                def stampa_luoghi(selezionati):
                    if not selezionati:
                        ui.notify('Seleziona almeno un luogo da stampare!', type='warning')
                        return

                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-5xl p-6 rounded-lg border border-gray-600 printable-sheet'):
                        with ui.row().classes('w-full justify-between items-center mb-6 no-print'):
                            with ui.column():
                                ui.label('🖨️ Stampa Elenco Luoghi').classes('text-2xl font-bold text-white')
                                ui.label(f'{len(selezionati)} contatti pronti per la stampa.').classes('text-blue-300')
                            with ui.row().classes('gap-3'):
                                ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                                ui.button('Avvia Stampa', icon='print', on_click=lambda: ui.run_javascript('window.print()')).classes('bg-green-600 text-white font-bold px-6')

                        with ui.element('div').classes('bg-white p-8 rounded border border-gray-300 w-full text-black'):
                            with ui.row().classes('w-full justify-between items-end border-b-4 border-black pb-4 mb-6'):
                                ui.image('dsv-print-logo.png').classes('w-48 h-12').props('fit=contain')
                                ui.label('RUBRICA CANTIERI E FORNITORI').classes('text-xl font-extrabold text-black tracking-widest')

                            for luogo in selezionati:
                                with ui.row().classes('w-full border-b border-gray-300 py-4 items-start no-wrap'):
                                    with ui.column().classes('w-2/5 pr-4 gap-0'):
                                        ui.label(luogo.get('ragione_sociale', '')).classes('text-lg font-bold text-black leading-tight')
                                        ui.label(str(luogo.get('tipo', '')).upper()).classes('text-[11px] font-bold text-gray-500 tracking-wider mt-1')
                                        if luogo.get('piva'):
                                            ui.label(f"P.IVA: {luogo.get('piva')}").classes('text-xs text-gray-700 mt-2')

                                    with ui.column().classes('w-1/4 px-4 border-l-2 border-gray-200 gap-0'):
                                        ui.label('SEDE OPERATIVA:').classes('text-[10px] font-bold text-gray-400')
                                        ui.label(luogo.get('indirizzo_sede', '-') or '-').classes('text-sm text-black leading-tight mb-2 line-clamp-2')
                                        
                                        if luogo.get('indirizzo_consegna'):
                                            ui.label('CONSEGNA:').classes('text-[10px] font-bold text-gray-400')
                                            ui.label(luogo.get('indirizzo_consegna')).classes('text-sm text-black leading-tight line-clamp-2')

                                    with ui.column().classes('w-1/3 pl-4 border-l-2 border-gray-200 gap-1'):
                                        if luogo.get('riferimento'):
                                            with ui.row().classes('items-center gap-2 no-wrap w-full'):
                                                ui.icon('person', size='16px').classes('text-gray-500')
                                                ui.label(luogo.get('riferimento')).classes('text-sm text-black truncate')
                                        
                                        if luogo.get('telefono'):
                                            with ui.row().classes('items-center gap-2 no-wrap w-full'):
                                                ui.icon('phone', size='16px').classes('text-gray-500')
                                                ui.label(luogo.get('telefono')).classes('text-sm text-black font-mono')
                                                
                                        if luogo.get('mail'):
                                            with ui.row().classes('items-center gap-2 no-wrap w-full'):
                                                ui.icon('mail', size='16px').classes('text-gray-500')
                                                ui.label(luogo.get('mail')).classes('text-sm text-black truncate')
                    dialog.open()

                def apri_mappa(selezionati):
                    if not selezionati or len(selezionati) > 1:
                        ui.notify('Seleziona ESATTAMENTE UN luogo per aprirlo in mappa!', type='warning')
                        return
                    
                    luogo = selezionati[0]
                    indirizzo_completo = f"{luogo.get('indirizzo_sede', '')} {luogo.get('ragione_sociale', '')}".strip()
                    
                    if not indirizzo_completo:
                        ui.notify('Non ci sono dati sufficienti per cercare su Maps.', type='warning')
                        return
                        
                    # Mappa corretta per una ricerca universale
                    url_maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(indirizzo_completo)}"
                    ui.run_javascript(f"window.open('{url_maps}', '_blank');")

                # --- RENDERIZZAZIONE INTERFACCIA ---
                def renderizza_interfaccia_luoghi():
                    global tabella_luoghi, barra_ricerca_luoghi
                    luoghi_container.clear()
                    
                    with luoghi_container:
                        with ui.row().classes('w-full justify-between items-center no-wrap mb-4 mt-4') as header_row:
                            
                            barra_ricerca_luoghi = ui.input(placeholder='Cerca cantiere o città...', on_change=applica_filtri_luoghi).props('input-style="color: white" outlined clearable rounded dense').classes('custom-input w-full max-w-md')
                            with barra_ricerca_luoghi.add_slot('prepend'):
                                ui.icon('search').classes('text-white')

                            with ui.row().classes('gap-3 items-center no-wrap'):
                                ui.button(icon='add', on_click=aggiungi_luogo).props('round outline color="positive"').tooltip('Aggiungi Cantiere')
                                ui.button(icon='delete', on_click=lambda: elimina_luoghi(tabella_luoghi.selected)).props('round outline color="negative"').tooltip('Elimina')
                                ui.button(icon='print', on_click=lambda: stampa_luoghi(tabella_luoghi.selected)).props('round outline color="white"').tooltip('Stampa Elenco')
                                ui.button(icon='map', on_click=lambda: apri_mappa(tabella_luoghi.selected)).props('round outline color="info"').tooltip('Apri in Google Maps')

                        colonne = [
                            {'name': 'azioni', 'label': '', 'field': 'azioni', 'align': 'center'},
                            {'name': 'ragione_sociale', 'label': 'Ragione Sociale / Cantiere', 'field': 'ragione_sociale', 'sortable': True, 'align': 'left'},
                            {'name': 'indirizzo', 'label': 'Indirizzo', 'field': 'indirizzo_sede', 'align': 'left'},
                            {'name': 'riferimento', 'label': 'Ns. Riferimento', 'field': 'riferimento', 'sortable': True, 'align': 'left'},
                            {'name': 'telefono', 'label': 'Telefono', 'field': 'telefono', 'sortable': True, 'align': 'left'},
                            {'name': 'mail', 'label': 'Mail', 'field': 'mail', 'sortable': True, 'align': 'left'},
                        ]

                        with ui.element('div').classes('w-full overflow-x-auto rounded-lg border border-gray-700'):
                            tabella_luoghi = ui.table(
                                columns=colonne, 
                                rows=[],
                                row_key='id',
                                selection='multiple'  
                            ).classes('bg-transparent data-table text-white w-full min-w-[1000px]').props('dense flat bordered')
                            
                            tabella_luoghi.add_slot('body-cell-azioni', '''
                                <q-td :props="props">
                                    <q-btn size="sm" round outline color="white" icon="edit" @click="() => $parent.$emit('modifica', props.row)" />
                                </q-td>
                            ''')

                        tabella_luoghi.on('modifica', lambda e: modifica_luogo(e.args))
                        
                        # Inizializziamo i dati nella tabella appena disegnata
                        applica_filtri_luoghi()

                # --- AVVIO CON CARICAMENTO ASINCRONO ---
                with luoghi_container:
                    ui.spinner('dots', size='3em', color='purple').classes('mx-auto mt-20')
                
                ui.timer(0.1, carica_luoghi, once=True)





            elif scelta == "Personale":
                import uuid
                import json
                import datetime

                personale_container = ui.column().classes('w-full min-w-0')
                
                # --- VARIABILI GLOBALI UNIVOCHE ---
                global tutte_le_persone, tabella_persone, barra_ricerca_persone
                tutte_le_persone = []
                tabella_persone = None
                barra_ricerca_persone = None

                # --- CARICAMENTO DATI ---
                def carica_persone():
                    global tutte_le_persone, tabella_persone
                    try:
                        # Scarichiamo i dati ordinandoli per nome
                        res = supabase.table('persone').select('*').order('nome').execute()
                        dati_raw = res.data if hasattr(res, 'data') else []
                        
                        # --- PRE-ELABORAZIONE STATI SCADENZE E DOCUMENTI ---
                        oggi_dt = datetime.date.today()
                        for riga in dati_raw:
                            # 1. Verifica presenza documenti
                            docs = riga.get('documenti')
                            has_doc = False
                            if docs:
                                try:
                                    lista_docs = json.loads(docs) if isinstance(docs, str) else docs
                                    has_doc = bool(lista_docs and len(lista_docs) > 0)
                                except:
                                    has_doc = bool(docs)
                            riga['_ha_doc'] = has_doc
                            
                            # 2. Calcolo lo stato della scadenza imminente (sotto i 15 giorni) o superata
                            scad = riga.get('scadenze')
                            riga['_stato_scadenza'] = 'nessuno'
                            if scad:
                                try:
                                    scad_dt = datetime.datetime.strptime(str(scad)[:10], '%Y-%m-%d').date()
                                    if scad_dt < oggi_dt:
                                        riga['_stato_scadenza'] = 'scaduta'
                                    elif (scad_dt - oggi_dt).days <= 15:
                                        riga['_stato_scadenza'] = 'imminente'
                                    else:
                                        riga['_stato_scadenza'] = 'regolare'
                                except:
                                    pass
                        
                        tutte_le_persone = dati_raw
                        
                        # --- AGGIORNAMENTO MORBIDO ---
                        if tabella_persone is not None:
                            try:
                                applica_filtri_persone()
                            except Exception:
                                pass
                        else:
                            renderizza_interfaccia_persone()
                    except Exception as e:
                        ui.notify(f"Errore caricamento personale: {e}", type='negative')

                # --- FUNZIONE DI RICERCA ---
                def applica_filtri_persone(e=None):
                    global tabella_persone, barra_ricerca_persone
                    if not tabella_persone: return

                    termine = barra_ricerca_persone.value.lower().strip() if barra_ricerca_persone and barra_ricerca_persone.value else ""
                    
                    if not termine:
                        tabella_persone.rows = tutte_le_persone
                    else:
                        tabella_persone.rows = [
                            riga for riga in tutte_le_persone
                            if termine in str(riga.get('nome', '')).lower() 
                            or termine in str(riga.get('mansione', '')).lower()
                        ]
                    tabella_persone.update()

                # --- FUNZIONI DEI PULSANTI ---
                def aggiungi_persona():
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-4xl p-6 rounded-lg border border-gray-600 text-white'):
                        ui.label('👷 Nuovo Operatore').classes('text-2xl font-bold mb-4')
                        
                        documenti_locali = [] # Memoria locale temporanea per i file della scheda corrente
                        
                        with ui.row().classes('w-full gap-6 no-wrap items-stretch'):
                            # Sezione Sinistra: Campi Anagrafici
                            with ui.column().classes('flex-1 gap-2'):
                                val_nome = ui.input('Nome e Cognome *').classes('w-full').props('dark outlined')
                                val_mansione = ui.input('Mansione (es. Operaio, Autista)').classes('w-full').props('dark outlined')
                                val_tel = ui.input('Telefono').classes('w-full').props('dark outlined')
                                val_email = ui.input('Email').classes('w-full').props('dark outlined')
                                val_attivo = ui.checkbox('In Forza (Attivo)', value=True).classes('text-white font-bold mt-2')
                            
                            # Sezione Destra: Gestione Scadenze e Archivio File
                            with ui.column().classes('flex-1 gap-2 border-l border-gray-700 pl-6'):
                                ui.label('📅 Scadenze e Documentazione').classes('text-lg font-bold text-blue-400 mb-1')
                                val_scadenza = ui.input('Data Prossima Scadenza (Visita/Attestati)').props('type=date dark outlined').classes('w-full')
                                
                                ui.label('📁 Cartella File Allegati').classes('text-sm font-bold text-gray-300 mt-2')
                                lista_doc_container = ui.column().classes('w-full bg-gray-950 p-3 rounded-lg min-h-[100px] max-h-[140px] overflow-y-auto border border-gray-800')
                                
                                def aggiorna_lista_doc_ui():
                                    lista_doc_container.clear()
                                    with lista_doc_container:
                                        if not documenti_locali:
                                            ui.label('Nessun documento presente').classes('text-gray-500 italic text-xs')
                                        for doc in documenti_locali:
                                            with ui.row().classes('w-full items-center justify-between bg-gray-800 px-3 py-1 rounded mb-1 no-wrap'):
                                                ui.label(doc).classes('text-xs truncate max-w-[200px]')
                                                ui.button(icon='delete', on_click=lambda d=doc: rimuovi_doc(d)).props('flat round dense color="negative" size="sm"')

                                def rimuovi_doc(nome_doc):
                                    if nome_doc in documenti_locali:
                                        documenti_locali.remove(nome_doc)
                                        aggiorna_lista_doc_ui()

                                def gestisci_upload(e):
                                    if e.name not in documenti_locali:
                                        documenti_locali.append(e.name)
                                        aggiorna_lista_doc_ui()
                                        ui.notify(f"Aggiunto: {e.name}", type='positive')

                                ui.upload(label='Rilascia o seleziona un file', on_upload=gestisci_upload, multiple=True).props('dark flat bordered dense hide-upload-btn').classes('w-full text-xs mt-2')
                                aggiorna_lista_doc_ui()
                        
                        def salva():
                            if not val_nome.value:
                                ui.notify('Il Nome è obbligatorio!', type='warning')
                                return
                            
                            nuovo_dato = {
                                'id': str(uuid.uuid4()),
                                'nome': val_nome.value.strip(),
                                'mansione': val_mansione.value.strip() if val_mansione.value else None,
                                'telefono': val_tel.value.strip() if val_tel.value else None,
                                'email': val_email.value.strip() if val_email.value else None,
                                'attivo': val_attivo.value,
                                'scadenze': val_scadenza.value if val_scadenza.value else None,
                                'documenti': json.dumps(documenti_locali)
                            }
                            
                            try:
                                supabase.table('persone').insert(nuovo_dato).execute()
                                ui.notify('✅ Persona aggiunta!', type='positive')
                                dialog.close()
                                carica_persone()
                            except Exception as e:
                                ui.notify(f'❌ Errore: {e}', type='negative')

                        with ui.row().classes('w-full justify-end gap-4 mt-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Salva', on_click=salva).classes('bg-green-600 text-white font-bold px-6')
                    dialog.open()

                def modifica_persona(riga):
                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-4xl p-6 rounded-lg border border-gray-600 text-white'):
                        ui.label('✏️ Modifica Scheda e Cartella Documenti').classes('text-2xl font-bold mb-4')
                        
                        # Carichiamo i documenti salvati nel DB
                        docs_db = riga.get('documenti') or '[]'
                        try:
                            documenti_locali = json.loads(docs_db) if isinstance(docs_db, str) else (docs_db or [])
                            if not isinstance(documenti_locali, list): documenti_locali = []
                        except:
                            documenti_locali = []
                        
                        with ui.row().classes('w-full gap-6 no-wrap items-stretch'):
                            # Sezione Sinistra: Modifica Anagrafica
                            with ui.column().classes('flex-1 gap-2'):
                                val_nome = ui.input('Nome e Cognome *', value=riga.get('nome')).classes('w-full').props('dark outlined')
                                val_mansione = ui.input('Mansione', value=riga.get('mansione')).classes('w-full').props('dark outlined')
                                val_tel = ui.input('Telefono', value=riga.get('telefono')).classes('w-full').props('dark outlined')
                                val_email = ui.input('Email', value=riga.get('email')).classes('w-full').props('dark outlined')
                                val_attivo = ui.checkbox('In Forza (Attivo)', value=riga.get('attivo')).classes('text-white font-bold mt-2')
                            
                            # Sezione Destra: Modifica Scadenze e Cartella Documenti
                            with ui.column().classes('flex-1 gap-2 border-l border-gray-700 pl-6'):
                                ui.label('📅 Scadenze e Documentazione').classes('text-lg font-bold text-blue-400 mb-1')
                                format_scad = str(riga.get('scadenze') or '')[:10] if riga.get('scadenze') else ''
                                val_scadenza = ui.input('Data Prossima Scadenza', value=format_scad).props('type=date dark outlined').classes('w-full')
                                
                                ui.label('📁 Cartella File Allegati').classes('text-sm font-bold text-gray-300 mt-2')
                                lista_doc_container = ui.column().classes('w-full bg-gray-950 p-3 rounded-lg min-h-[100px] max-h-[140px] overflow-y-auto border border-gray-800')
                                
                                def aggiorna_lista_doc_ui():
                                    lista_doc_container.clear()
                                    with lista_doc_container:
                                        if not documenti_locali:
                                            ui.label('Nessun documento in cartella').classes('text-gray-500 italic text-xs')
                                        for doc in documenti_locali:
                                            with ui.row().classes('w-full items-center justify-between bg-gray-800 px-3 py-1 rounded mb-1 no-wrap'):
                                                ui.label(doc).classes('text-xs truncate max-w-[200px]')
                                                ui.button(icon='delete', on_click=lambda d=doc: rimuovi_doc(d)).props('flat round dense color="negative" size="sm"')

                                def rimuovi_doc(nome_doc):
                                    if nome_doc in documenti_locali:
                                        documenti_locali.remove(nome_doc)
                                        aggiorna_lista_doc_ui()

                                def gestisci_upload(e):
                                    if e.name not in documenti_locali:
                                        documenti_locali.append(e.name)
                                        aggiorna_lista_doc_ui()
                                        ui.notify(f"Aggiunto alla cartella: {e.name}", type='positive')

                                ui.upload(label='Trascina qui altri file da aggiungere', on_upload=gestisci_upload, multiple=True).props('dark flat bordered dense hide-upload-btn').classes('w-full text-xs mt-2')
                                aggiorna_lista_doc_ui()

                        def aggiorna():
                            if not val_nome.value:
                                ui.notify('Il Nome è obbligatorio!', type='warning')
                                return
                                
                            aggiornamenti = {
                                'nome': val_nome.value.strip(),
                                'mansione': val_mansione.value.strip() if val_mansione.value else None,
                                'telefono': val_tel.value.strip() if val_tel.value else None,
                                'email': val_email.value.strip() if val_email.value else None,
                                'attivo': val_attivo.value,
                                'scadenze': val_scadenza.value if val_scadenza.value else None,
                                'documenti': json.dumps(documenti_locali)
                            }
                            
                            try:
                                supabase.table('persone').update(aggiornamenti).eq('id', riga['id']).execute()
                                ui.notify('✅ Anagrafica e documenti aggiornati!', type='positive')
                                dialog.close()
                                carica_persone()
                            except Exception as e:
                                ui.notify(f'❌ Errore: {e}', type='negative')

                        with ui.row().classes('w-full justify-end gap-4 mt-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Aggiorna', on_click=aggiorna).classes('bg-blue-600 text-white font-bold px-6')
                    dialog.open()

                def elimina_persone(selezionati):
                    if not selezionati:
                        ui.notify('Seleziona almeno una persona da eliminare!', type='warning')
                        return

                    with ui.dialog() as dialog, ui.card().classes('bg-blue-900 w-full max-w-md p-6 rounded-lg border-2 border-red-500 text-white'):
                        ui.label('Conferma Eliminazione').classes('text-2xl font-bold text-red-500 mb-2')
                        ui.label('Stai per eliminare queste anagrafiche.').classes('mb-4')
                        
                        def conferma():
                            try:
                                for persona in selezionati:
                                    supabase.table('persone').delete().eq('id', persona['id']).execute()
                                ui.notify(f'✅ {len(selezionati)} persone eliminate.', type='positive')
                                dialog.close()
                                try:
                                    tabella_persone.selected.clear()
                                except: pass
                                carica_persone()
                            except Exception as e:
                                errore = str(e).lower()
                                if "foreign key" in errore or "violates" in errore:
                                    ui.notify('❌ Impossibile eliminare: questa persona ha dei turni o documenti collegati! Usa il tasto Modifica e togli la spunta "In Forza".', type='negative', position='top', timeout=5000)
                                else:
                                    ui.notify(f'❌ Errore: {e}', type='negative')

                        with ui.row().classes('w-full justify-between mt-4'):
                            ui.button('Annulla', on_click=dialog.close).props('outline color="white"')
                            ui.button('Sì, Elimina', on_click=conferma).classes('bg-red-600 text-white font-bold')
                    dialog.open()

                # --- RENDERIZZAZIONE INTERFACCIA ---
                def renderizza_interfaccia_persone():
                    global tabella_persone, barra_ricerca_persone
                    personale_container.clear()
                    
                    with personale_container:
                        with ui.row().classes('w-full justify-between items-center no-wrap mb-4 mt-4') as header_row:
                            
                            barra_ricerca_persone = ui.input(placeholder='Cerca nome o mansione...', on_change=applica_filtri_persone).props('input-style="color: white" outlined clearable rounded dense').classes('custom-input w-full max-w-md')
                            with barra_ricerca_persone.add_slot('prepend'):
                                ui.icon('search').classes('text-white')

                            with ui.row().classes('gap-3 items-center no-wrap'):
                                ui.button(icon='add', on_click=aggiungi_persona).props('round outline color="positive"').tooltip('Aggiungi Persona')
                                ui.button(icon='delete', on_click=lambda: elimina_persone(tabella_persone.selected)).props('round outline color="negative"').tooltip('Elimina')

                        colonne = [
                            {'name': 'nome', 'label': 'Nome e Cognome', 'field': 'nome', 'sortable': True, 'align': 'left'},
                            {'name': 'mansione', 'label': 'Mansione', 'field': 'mansione', 'sortable': True, 'align': 'left'},
                            {'name': 'telefono', 'label': 'Telefono', 'field': 'telefono', 'align': 'left'},
                            {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
                            {'name': 'scadenze_doc', 'label': 'Scadenze / Doc', 'field': 'scadenze_doc', 'align': 'center'}, # <--- COLONNA STATO VISIVO
                            {'name': 'attivo', 'label': 'In Forza', 'field': 'attivo', 'sortable': True, 'align': 'center'},
                            {'name': 'azioni', 'label': 'Modifica', 'field': 'azioni', 'align': 'center'},
                        ]

                        with ui.element('div').classes('w-full overflow-x-auto rounded-lg border border-gray-700'):
                            tabella_persone = ui.table(
                                columns=colonne, 
                                rows=[],
                                row_key='id',
                                selection='multiple'  
                            ).classes('bg-transparent data-table text-white w-full min-w-[1000px]').props('dense flat bordered')
                            
                            # Customizzazione Colonna "Scadenze / Doc" (Mostra icone dinamiche con Tooltip descrittivi)
                            tabella_persone.add_slot('body-cell-scadenze_doc', '''
                                <q-td :props="props" class="text-center">
                                    <div class="row items-center justify-center gap-2 no-wrap">
                                        <q-icon v-if="props.row._ha_doc" name="folder" color="cyan-4" size="sm">
                                            <q-tooltip>Documenti presenti in archivio</q-tooltip>
                                        </q-icon>
                                        <q-icon v-if="props.row._stato_scadenza == 'scaduta'" name="error" color="red-5" size="sm">
                                            <q-tooltip>ATTENZIONE: Certificato o Visita SCADUTA!</q-tooltip>
                                        </q-icon>
                                        <q-icon v-if="props.row._stato_scadenza == 'imminente'" name="warning" color="orange-5" size="sm">
                                            <q-tooltip>Scadenza imminente (meno di 15 giorni!)</q-tooltip>
                                        </q-icon>
                                        <q-icon v-if="props.row._stato_scadenza == 'regolare'" name="check_circle" color="green-5" size="sm">
                                            <q-tooltip>Scadenze in regola</q-tooltip>
                                        </q-icon>
                                    </div>
                                </q-td>
                            ''')

                            tabella_persone.add_slot('body-cell-attivo', '''
                                <q-td :props="props" class="text-center">
                                    <q-icon v-if="props.row.attivo" name="check_circle" color="positive" size="sm" />
                                    <q-icon v-else name="cancel" color="negative" size="sm" />
                                </q-td>
                            ''')

							#PER PULSANTE MODIFICA SU RIGHE TABELLA
							# Aggiungiamo l'icona della matita per modificare la riga direttamente cliccandoci
                            tabella_persone.add_slot('body-cell-azioni', '''
                                <q-td :props="props">
                                    <q-btn size="sm" round outline color="white" icon="edit" @click="() => $parent.$emit('modifica', props.row)" />
                                </q-td>
                            ''')


                        tabella_persone.on('modifica', lambda e: modifica_persona(e.args))
                        applica_filtri_persone()

                # --- AVVIO CON CARICAMENTO ASINCRONO ---
                with personale_container:
                    ui.spinner('dots', size='3em', color='teal').classes('mx-auto mt-20')
                
                ui.timer(0.1, carica_persone, once=True)



            elif scelta == "Pianificazione": 
                import datetime
                import uuid

                turni_container = ui.column().classes('w-full min-w-0')

                # Variabile globale per ricordare la settimana visualizzata quando cambiamo pagina
                global data_corrente_pianificazione
                data_corrente_pianificazione = datetime.date.today()

                # --- 1. FUNZIONE PONTE (Mostra il caricamento istantaneo) ---
                def naviga_matrice(nuova_data=None):
                    global data_corrente_pianificazione
                    if nuova_data is not None:
                        data_corrente_pianificazione = nuova_data
                        
                    turni_container.clear()
                    with turni_container:
                        ui.spinner('dots', size='3em', color='yellow').classes('mx-auto mt-20')
                        
                    # Lancia il lavoro pesante con un micro-ritardo per non bloccare la grafica
                    ui.timer(0.1, renderizza_matrice, once=True)

                # --- 2. FUNZIONE PRINCIPALE (Scarica dati e crea la griglia) ---
                def renderizza_matrice():
                    global data_corrente_pianificazione
                    data_rif = data_corrente_pianificazione
                    
                    try:
                        # --- CALCOLO DEI GIORNI ---
                        lunedi = data_rif - datetime.timedelta(days=data_rif.weekday())
                        venerdi = lunedi + datetime.timedelta(days=4)
                        giorni = [(lunedi + datetime.timedelta(days=i)) for i in range(5)]
                        nomi_giorni = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì']

                        # --- SCARICHIAMO I DATI DAL DATABASE ---
                        res_persone = supabase.table('persone').select('id, nome, attivo').order('nome').execute()
                        persone = [p for p in (res_persone.data if hasattr(res_persone, 'data') else []) if p.get('attivo', True)]
                        
                        if not persone:
                            turni_container.clear()
                            with turni_container:
                                ui.notify('Nessun operatore attivo trovato!', type='warning')
                            return

                        res_luoghi = supabase.table('luoghi').select('id, ragione_sociale').order('ragione_sociale').execute()
                        dati_luoghi = res_luoghi.data if hasattr(res_luoghi, 'data') else []
                        
                        opzioni_celle = {l['id']: l['ragione_sociale'] for l in dati_luoghi}
                        opzioni_celle['FERIE'] = 'FERIE'
                        opzioni_celle['MALATTIA'] = 'MALATTIA'
                        opzioni_celle['PERMESSO'] = 'PERMESSO'
                        opzioni_celle['SEDE'] = 'SEDE / MAGAZZINO'

                        nomi_stampa = {l['id']: l['ragione_sociale'] for l in dati_luoghi}
                        nomi_stampa['FERIE'] = 'FERIE'
                        nomi_stampa['MALATTIA'] = 'MALATTIA'
                        nomi_stampa['PERMESSO'] = 'PERMESSO'
                        nomi_stampa['SEDE'] = 'SEDE'

                        # Usiamo un range di date per scaricare SOLO i turni di questa specifica settimana
                        res_turni = supabase.table('turni').select('*').gte('data_turno', lunedi.strftime('%Y-%m-%d')).lte('data_turno', venerdi.strftime('%Y-%m-%d')).execute()
                        dati_turni = res_turni.data if hasattr(res_turni, 'data') else []
                        mappa_turni = {(t['persona_id'], t['data_turno']): t for t in dati_turni}

                        # --- FUNZIONI DI SUPPORTO (Nidificate per mantenere l'accesso ai dati della settimana corrente) ---
                        def stampa_settimana():
                            with ui.dialog() as dialog, ui.card().classes('bg-white w-full max-w-6xl p-6 rounded-lg border border-gray-300 printable-sheet text-black'):
                                
                                # Intestazione Foglio
                                with ui.row().classes('w-full justify-between items-end border-b-4 border-black pb-4 mb-4'):
                                    ui.image('dsv-print-logo.png').classes('w-48 h-12').props('fit=contain')
                                    ui.label(f"PROGRAMMA SETTIMANALE DAL {lunedi.strftime('%d/%m/%Y')} AL {venerdi.strftime('%d/%m/%Y')}").classes('text-xl font-extrabold text-black tracking-widest')
                                
                                # Griglia di Stampa
                                with ui.column().classes('w-full gap-0 border-t border-l border-black'):
                                    # Riga Intestazione (Giorni)
                                    with ui.grid(columns=6).classes('w-full bg-gray-200 font-bold text-center'):
                                        ui.label('OPERATORE').classes('p-2 border-b border-r border-black text-left')
                                        for i, g in enumerate(giorni):
                                            ui.label(f"{nomi_giorni[i]} {g.strftime('%d/%m')}").classes('p-2 border-b border-r border-black text-sm')
                                    
                                    # Righe Operatori
                                    for p in persone:
                                        with ui.grid(columns=6).classes('w-full items-center text-center'):
                                            ui.label(p['nome']).classes('p-2 border-b border-r border-black font-bold text-sm text-left truncate')
                                            for g in giorni:
                                                data_str = g.strftime('%Y-%m-%d')
                                                turno = mappa_turni.get((p['id'], data_str))
                                                valore = ""
                                                if turno:
                                                    key = turno.get('luogo_id') or turno.get('stato_speciale')
                                                    valore = nomi_stampa.get(key, "")
                                                ui.label(valore).classes('p-2 border-b border-r border-black text-xs uppercase line-clamp-2 leading-tight h-full content-center')

                                # Pulsanti (Non visibili in stampa)
                                with ui.row().classes('w-full justify-end gap-3 mt-4 no-print'):
                                    ui.button('Chiudi', on_click=dialog.close).props('outline color="black"')
                                    ui.button('Avvia Stampa', icon='print', on_click=lambda: ui.run_javascript('window.print()')).classes('bg-green-600 text-white font-bold')
                            dialog.open()

                        def aggiorna_turno(persona_id, data_ogg, nuovo_valore):
                            data_str = data_ogg.strftime('%Y-%m-%d')
                            turno_esistente = mappa_turni.get((persona_id, data_str))

                            is_uuid = '-' in str(nuovo_valore) and len(str(nuovo_valore)) == 36
                            val_luogo = nuovo_valore if is_uuid else None
                            val_stato = None if is_uuid else nuovo_valore
                            
                            if not nuovo_valore:
                                if turno_esistente:
                                    supabase.table('turni').delete().eq('id', turno_esistente['id']).execute()
                                    del mappa_turni[(persona_id, data_str)]
                                return

                            if turno_esistente:
                                supabase.table('turni').update({
                                    'luogo_id': val_luogo,
                                    'stato_speciale': val_stato
                                }).eq('id', turno_esistente['id']).execute()
                                turno_esistente['luogo_id'] = val_luogo
                                turno_esistente['stato_speciale'] = val_stato
                            else:
                                nuovo_record = {
                                    'id': str(uuid.uuid4()),
                                    'persona_id': persona_id,
                                    'data_turno': data_str,
                                    'luogo_id': val_luogo,
                                    'stato_speciale': val_stato
                                }
                                supabase.table('turni').insert(nuovo_record).execute()
                                mappa_turni[(persona_id, data_str)] = nuovo_record
                            
                            ui.notify('✅ Salvato', type='positive', position='bottom-right')

                        # --- COSTRUZIONE DELLA GRIGLIA VISIVA ---
                        turni_container.clear() # Togliamo la rotellina
                        
                        with turni_container:
                            # Titolo ed Estetica
                            with ui.row().classes('w-full justify-end items-center no-wrap mb-4 mt-4'):
                                
                                # Navigazione nel tempo
                                with ui.row().classes('items-center gap-4 bg-transparent').props('round outline color="white"'):
                                    ui.button(icon='chevron_left', on_click=lambda: naviga_matrice(lunedi - datetime.timedelta(days=7))).props('round outline color="white" size="sm"').tooltip('Settimana Precedente')
                                    
                                    with ui.column().classes('items-center gap-0 min-w-[200px]'):
                                        ui.label('SCEGLI LA SETTIMANA').classes('text-[10px] font-bold text-blue-400 tracking-widest')
                                        ui.label(f"Dal {lunedi.strftime('%d/%m')} al {venerdi.strftime('%d/%m')}").classes('text-xl font-bold text-white').props('round outline color="white"')
                                    
                                    ui.button(icon='chevron_right', on_click=lambda: naviga_matrice(lunedi + datetime.timedelta(days=7))).props('round outline color="white" size="sm"').tooltip('Settimana Successiva')

                                # Tasti Azione Rapida
                                with ui.row().classes('gap-3'):
                                    ui.button(icon='today', on_click=lambda: naviga_matrice(datetime.date.today())).props('round outline color="white"').tooltip('Torna a Oggi')
                                    ui.button(icon='refresh', on_click=lambda: naviga_matrice(data_rif)).props('round outline color="white"').tooltip('Ricarica Dati')
                                    ui.button(icon='print', on_click=stampa_settimana).props('round outline color="white"').tooltip('Stampa Settimana')

                            # Struttura Tabellare
                            with ui.element('div').classes('w-full min-w-0'):
                                # Intestazione
                                with ui.grid(columns=6).classes('w-full min-w-0'):
                                    ui.label('Operatore').classes('text-white text-lg tracking-wider')
                                    for i, giorno in enumerate(giorni):
                                        with ui.column().classes('items-center w-full gap-0'):
                                            ui.label(nomi_giorni[i].upper()).classes('text-white text-sm')
                                            ui.label(giorno.strftime('%d/%m')).classes('text-white text-lg')

                                # Righe
                                for persona in persone:
                                    with ui.grid(columns=6).classes('w-full min-w-0 flex-nowrap'):
                                        ui.label(persona['nome']).classes('text-white text-base truncate')
                                        
                                        for giorno in giorni:
                                            data_str = giorno.strftime('%Y-%m-%d')
                                            turno = mappa_turni.get((persona['id'], data_str))
                                            
                                            valore_attuale = None
                                            if turno:
                                                valore_attuale = turno.get('luogo_id') or turno.get('stato_speciale')

                                            ui.select(
                                                opzioni_celle, 
                                                value=valore_attuale, 
                                                on_change=lambda e, p=persona['id'], d=giorno: aggiorna_turno(p, d, e.value)
                                            ).props('input-style="color: white" outlined clearable rounded dense').classes('whitespace-nowrap h-fit custom-input max-w-[200px] ellipsis mb-2')

                    except Exception as e:
                        turni_container.clear()
                        with turni_container:
                            ui.notify(f"❌ Errore critico matrice: {e}", type='negative')

                # Kickstart: avvia il primissimo caricamento appena si clicca sul menù
                naviga_matrice()


    
    nav.on_value_change(lambda e: update_content(e.value))
    update_content("Pannello di Controllo")

with ui.dialog() as chat_radu, ui.card().props('backdrop-filter="blur(100px, color=white) brightness(40%)"').classes('justify-between bg-gray-800 p-3 border-b border-gray-600 shadow-md'):
    with ui.row().classes('justify-between bg-gray-800 p-3 border-b border-gray-600 shadow-md'):
        #ui.label('Chiedi a RADU!').classes('text-white text-lg font-bold')
        ui.button(icon='close', on_click=chat_radu.close).props('outline color="white" size="sm"').classes('justify-right-0')
  

    with ui.column().classes('h-[350px] w-[350px]'):    
                # AREA MESSAGGI
        area_messaggi = ui.column().classes('justify-right-0 flex-1 order-l-4 border-blue-500 items-right-0 p-4')
        with area_messaggi:
                ui.chat_message(
                    'Che c\'è adesso? Spero sia una cosa veloce, che ho un bilico in piazzale da scaricare ...',
                    name='', stamp='Adesso', avatar='static/radu-chat2.png' 
                ).props('dense flat bordered rounded text-color="black"').classes('justify-right-0 text-black image-size-40')

        # BARRA DI INPUT sulla chat
        with ui.row().classes('justify-right-0 flex-1 bg-gray-800 border-l-4 border-blue-500 items-right p-4'):
            input_chat = ui.input(placeholder='Chiedi qualcosa a Radu...').classes('flex-grow').props('dark outlined dense rounded')


            async def invia_messaggio():
                testo = input_chat.value
                if not testo: return
                
                with area_messaggi:
                    ui.chat_message(testo, name='', sent=True).props('text-color="black"').classes('text-black')
                input_chat.value = ''
                
                messaggio_attesa = ui.chat_message('Radu sta sbuffando...', name='', avatar='static/radu-chat2.png')
                
                try:
                    # --- RICERCA NEI DOCUMENTI (RAG) ---
                    contesto_extra = ""
                    if db_conoscenza_radu:
                        # 1. Fa la ricerca e pesca i 5 paragrafi migliori
                        docs_trovati = db_conoscenza_radu.similarity_search(testo, k=5)
                        
                        # 2. TRUCCO DI DEBUG: Stampiamo nel terminale cosa ha trovato
                        print("--- ECCO COSA STA LEGGENDO RADU IN SEGRETO ---")
                        for d in docs_trovati:
                            print(d.page_content)
                            print("------------------------------------------")
                            
                        # 3. Unisce i paragrafi per passarli a Groq (Questo pezzo mancava!)
                        contesto_extra = "\n\nInformazioni estratte dai documenti aziendali:\n" + \
                                            "\n".join([d.page_content for d in docs_trovati])

                    # 4. Prepariamo il prompt con il contesto extra (Allineato con l'if, non dentro)
                    prompt_rag = f"{testo}{contesto_extra}\n\nRicorda: usa queste informazioni se utili, ma rispondi sempre con il tuo stile scontroso."
                    
                    memoria_radu.append({"role": "user", "content": prompt_rag})                    
                    chat_completion = await groq_client.chat.completions.create(
                        messages=memoria_radu,
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                    )
                    risposta = chat_completion.choices[0].message.content
                    memoria_radu.append({"role": "assistant", "content": risposta})
                    
                    area_messaggi.remove(messaggio_attesa)
                    with area_messaggi:
                        msg = ui.chat_message(name='', avatar='static/radu-chat2.png').props('text-color="black"')
                        with msg:
                            ui.markdown(risposta)
                # ... resto del blocco try-except ...
                except Exception as e:
                    area_messaggi.remove(messaggio_attesa)
                    with area_messaggi:
                        ui.chat_message(f"Errore: {str(e)}", name='Sistema').props('bg-color="red-8"')     

                ui.run_javascript('document.querySelector(".q-message-container:last-child").scrollIntoView({behavior: "smooth"})')
            input_chat.on('keydown.enter', invia_messaggio).props('flat dense round color="white"').classes('text-white')
            ui.button(icon='send', on_click=invia_messaggio).props('flat dense round color="white"')


# --- 2. POI CREIAMO LA BARRA LATERALE E IL SUO PULSANTE ---
with ui.right_drawer().props("width=180").classes('bg-blue-900 items-center'):
    ui.separator().props('color="blue"')
    ui.image('logo_radu.png').classes('w-36')
    ui.separator().props('color="blue"')
    ui.image('radu_avatar.png').classes('w-28')
    

    ui.button('Scrivi...', icon='chat', on_click=chat_radu.open) \
    .props('outline rounded color="white" text-color="white" w-28') \
    .classes('justify-center hover:scale-110 transition-transform') \
    .tooltip('Disturba Radu')  



            
    #ui.label('Chiedi a RADU').classes('text-white mt-2 font-bold')
layout_principale()
ui.run(favicon='logo-dsv-w.png')

