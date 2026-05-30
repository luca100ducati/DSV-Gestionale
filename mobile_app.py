import os
from datetime import datetime
from nicegui import app, ui

# 1. Prepariamo la cartella per i guasti
CARTELLA_FOTO = 'foto_guasti'
os.makedirs(CARTELLA_FOTO, exist_ok=True)
app.add_static_files('/foto_guasti', CARTELLA_FOTO)

# ----------------------------------------------------
# IMPOSTAZIONI GLOBALI DEI COMPONENTI (Fuori dalla pagina: perfette qui)
# ----------------------------------------------------
ui.input.default_props('input-style="color: white" outlined clearable rounded dense')
ui.input.default_classes('w-full max-w-md')

ui.button.default_props('outline round dense color="cyan"')
ui.button.default_classes('w-full my-2 font-bold')

ui.icon.default_props('color="cyan" size="sm"')

ui.table.default_props('dense flat bordered')
ui.table.default_classes('bg-transparent data-table text-white w-full')


# ----------------------------------------------------
# LA PAGINA MOBILE
# ----------------------------------------------------
@ui.page('/mobile')
def mobile_ui():
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">')
    
    # IMPORTANTE: Il tema del body va DENTRO la funzione della pagina!
    ui.query('body').style('background-color: #0d1b2a; color: #e0e1dd;')
    
    # Diciamo a Quasar di usare il tema scuro nativo per menu a tendina e calendari
    ui.dark_mode(True)

    def gestisci_foto(e):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        estensione = e.name.split('.')[-1]
        nome_file = f"guasto_{timestamp}.{estensione}"
        percorso_salvataggio = os.path.join(CARTELLA_FOTO, nome_file)

        with open(percorso_salvataggio, 'wb') as f:
            f.write(e.content.read())

        # Finestra di dialogo in stile Dark
        with ui.dialog() as dialog, ui.card().style('background-color: #1b2a40; border: 1px solid #00bcd4;').classes('w-full max-w-sm m-4 p-4 text-white'):
            ui.label('Dettagli Guasto').classes('text-xl font-bold text-cyan-400 mb-2')
            ui.image(f'/foto_guasti/{nome_file}').classes('w-full h-48 object-cover rounded-lg border border-cyan-700 mb-4')
            
            asset_id = ui.input('ID Attrezzo (es. TRP01)')
            note = ui.textarea('Cos\'è successo?').props('outline dark color="cyan"').classes('w-full mb-4')
            
            def invia_segnalazione():
                if not asset_id.value:
                    ui.notify("Inserisci l'ID dell'attrezzo!", type='warning', position='top')
                    return
                print(f"🚨 GUASTO: {asset_id.value} - {note.value}")
                ui.notify('Segnalazione inviata!', type='positive', position='top')
                dialog.close()

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Annulla', on_click=dialog.close).props('flat text-color="gray"')
                ui.button('Invia Segnalazione', on_click=invia_segnalazione).classes('bg-cyan-700 text-white')

        dialog.open()

    # --- LAYOUT INTERFACCIA MOBILE (Addio bg-gray-100, benvenuto tema scuro) ---
    # Nota che ho rimosso bg-gray-100 in modo che il body blu scuro si veda!
    with ui.column().classes('w-full min-h-screen items-center p-4 gap-4 no-wrap'):
        
        # Header - Sfondo blu leggermente più chiaro del body
        with ui.row().style('background-color: #1b2a40;').classes('w-full justify-between items-center p-4 rounded-lg shadow-md mb-2'):
            ui.image('/static/logo-dsv-w.png').classes('h-20')
            ui.label('DSV Mobile').classes('text-xl font-black text-white tracking-wider')
            ui.icon('account_circle', color='white')

        # Sezione Ricerca
        with ui.card().style('background-color: #112236;').classes('w-full p-4 justify-between'):
            with ui.row().classes('w-full justify-between no-wrap'):
                input_ricerca = ui.input('Cerca ID o Nome...').classes('w-full')
                ui.button(icon='search', on_click=lambda: ui.notify('Cerco...')).props('round')

        ui.separator().classes('w-full my-2 bg-cyan-900')

        # Azioni Rapide
        with ui.row().classes('w-full gap-4 no-wrap'):
            with ui.card().style('background-color: #112236;').classes('flex-1 p-3 shadow-sm items-center cursor-pointer'):
                with ui.button(on_click=lambda: ui.notify('Raggi-X')).classes('w-full h-24 bg-cyan-800 text-white rounded-xl mb-4 border-none'):
                    ui.icon('help_center', size='3rem', color='white')
                    ui.label('Raggi X').classes('font-bold text-sm mt-2 text-center text-cyan-100')
            with ui.card().style('background-color: #112236;').classes('flex-1 p-3 shadow-sm items-center cursor-pointer'):
                with ui.button(on_click=lambda: ui.notify('DDT Rapido')).classes('w-full h-24 bg-cyan-800 text-white rounded-xl mb-4 border-none'):
                    ui.icon('local_shipping', size='3rem', color='white')
                    ui.label('DDT Rapido').classes('font-bold text-sm mt-2 text-center text-cyan-100')
            with ui.card().style('background-color: #112236;').classes('flex-1 p-3 shadow-sm items-center cursor-pointer'):
                with ui.button(on_click=lambda: ui.notify('Scanner...')).classes('w-full h-24 bg-cyan-800 text-white rounded-xl mb-4 border-none'):
                    ui.icon('qr_code_scanner', size='3rem', color='white')
                    ui.label('Scanner QR').classes('font-bold text-sm mt-2 text-center text-cyan-100')

        ui.separator().classes('w-full my-2 bg-cyan-900')

        # Segnalazione Guasti
        with ui.card().style('background-color: #1a0f14; border: 1px solid #ff4d4d;').classes('w-full p-4 shadow-sm items-center'):
            with ui.row().classes('w-full justify-center items-center mb-2'):
                ui.icon('build', size='1.5rem', color='red-500')
                ui.label('SEGNALAZIONE GUASTO').classes('font-bold text-red-500 ml-2')
            ui.label('Scatta una foto al danno per aprire un ticket.').classes('text-xs text-gray-400 mb-3 text-center')
            
            ui.upload(
                label='📸 SCATTA FOTO', 
                auto_upload=True, 
                on_upload=gestisci_foto
            ).props('accept="image/*" capture="environment" color="red" flat bordered dark').classes('w-full text-center font-bold text-red-400')