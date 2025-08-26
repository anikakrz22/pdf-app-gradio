import gradio as gr
import pdfplumber
import pandas as pd
import re
import io

# Die gesamte Logik wird in eine Funktion verpackt
def extrahiere_gefahrstoffdaten(uploaded_files):
    """
    Extrahiert Gefahrstoffdaten aus einer Liste von PDF-Dateien.
    """
    if not uploaded_files:
        return "Bitte laden Sie mindestens eine PDF-Datei hoch.", None

    ergebnisse = []

    for uploaded_file in uploaded_files:
        # Initialisiere die Variablen
        handelsname = None
        produktidentifikator = None
        # ... (der Rest Ihrer Initialisierungen bleibt hier unverändert)
        verwendung = None
        ifd_nr = None
        h_codes = set()
        euh_codes = set()
        p_codes = set()
        cas_nummern = set()
        transportklasse = None
        gefahrstoff_info = 'Nein'
        piktogramm_entfaellt_gefunden = False
        umweltgefahr_ja_gefunden = False
        wgk_number = 'Nicht gefunden'
        krebserzeugend_info = 'Nein'
        lagerklasse = 'Nicht gefunden'

        # Lese Dateiname und Inhalt der hochgeladenen Datei
        file_name = uploaded_file.name
        
        # Extrahiere Ifd.Nr. aus Dateinamen
        m = re.search(r'lfd[-_]?Nr[_-]?(\d+)', file_name, re.IGNORECASE)
        if m:
            ifd_nr = m.group(1)
        else:
            ifd_nr = 'Nicht gefunden'
        
        try:
            with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    zeilen = text.splitlines()

                    # --- Der gesamte Extraktionscode (Handelsname, WGK, etc.)
                    # --- wird hier eingefügt, wie in Ihrem Original-Code ---
                    
                    # ... Ihr Code, z.B. die Suche nach Handelsnamen, etc. ...
                    # --- Handelsname ---
                    if not handelsname:
                        match_handelsname = re.search(r'Handelsname[:\s]*([^\n]+)', text, re.IGNORECASE)
                        if match_handelsname:
                            handelsname = match_handelsname.group(1).strip()
                            if handelsname:
                                handelsname = re.sub(r'\s*oder\s*', '', handelsname).strip()

                    # --- Produktidentifikator ---
                    if not handelsname and not produktidentifikator:
                        for i, zeile in enumerate(zeilen):
                            if re.search(r'Produktidentifikator', zeile, re.IGNORECASE):
                                m = re.search(r'Produktidentifikator[:\s]*(.*)', zeile, re.IGNORECASE)
                                if m and m.group(1).strip():
                                    produktidentifikator = m.group(1).strip()
                                    if produktidentifikator:
                                        produktidentifikator = re.sub(r'\s*oder\s*', '', produktidentifikator).strip()
                                    break
                                elif i + 1 < len(zeilen) and zeilen[i + 1].strip():
                                    produktidentifikator = zeilen[i + 1].strip()
                                    if produktidentifikator:
                                        produktidentifikator = re.sub(r'\s*oder\s*', '', produktidentifikator).strip()
                                    break

                    # --- Verwendung ---
                    if not verwendung:
                        m1 = re.search(r'Verwendung des (Stoffs|Gemischs)[:\s]*([^\n]+)', text, re.IGNORECASE)
                        if m1:
                            verwendung = m1.group(2).strip()
                    if not verwendung:
                        for zeile in zeilen:
                            m2 = re.search(r'Verwendung:\s*(.*)', zeile, re.IGNORECASE)
                            if m2 and m2.group(1).strip():
                                verwendung = m2.group(1).strip()
                                break
                    if not verwendung:
                        for i, zeile in enumerate(zeilen):
                            if re.search(r'Relevante\s+identifizierte\s+Verwendungen\s+des\s+(Stoffs|Gemischs)', zeile, re.IGNORECASE):
                                if i + 1 < len(zeilen):
                                    verwendung = zeilen[i + 1].strip()
                                    break
                    if verwendung:
                        verwendung = re.sub(r'(/des Gemischs|\/des|\/Gemischs|\/Des Stoffs)\s*:\s*', '', verwendung).strip()
                        verwendung = re.sub(r'\s*/Gemischs\s*', ' ', verwendung).strip()
                        verwendung = re.sub(r'Relevante\s+identifizierte\s+Verwendungen\s+des\s+Stoffs\s+oder\s+Gemischs:', '', verwendung, flags=re.IGNORECASE).strip()
                        verwendung = re.sub(r'denen\s+abgeraten\s+wird', '', verwendung, flags=re.IGNORECASE).strip()
                        verwendung = re.sub(r'identifizierte', '', verwendung, flags=re.IGNORECASE).strip()
                        verwendung = re.sub(r'abgeratenwird', '', verwendung, flags=re.IGNORECASE).strip()
                    # --- Vereinfachte Suche nach H-, P- und EUH-Sätzen ---
                    found_h_euh = re.findall(r'\b(EUH\d{3}|H\d{3})\b', text, re.IGNORECASE)
                    h_codes.update([c for c in found_h_euh if c.upper().startswith('H')])
                    euh_codes.update([c for c in found_h_euh if c.upper().startswith('EUH')])
                    found_p = re.findall(r'\b(P\d{3}(?:\s+\+\s+P\d{3})?)\b', text, re.IGNORECASE)
                    p_codes.update(found_p)
                    # --- CAS-Nummern aus Tabellen extrahieren ---
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            header_row = table[0] if table else []
                            try:
                                cas_column_index = -1
                                for i, cell in enumerate(header_row):
                                    if cell and re.search(r'CAS-N', cell, re.IGNORECASE):
                                        cas_column_index = i
                                        break
                                if cas_column_index != -1:
                                    for row in table[1:]:
                                        if row and len(row) > cas_column_index and row[cas_column_index]:
                                            found_cas = re.search(r'(\d{2,7}-\d{2}-\d)', row[cas_column_index])
                                            if found_cas:
                                                cas_nummern.add(found_cas.group(1))
                            except IndexError:
                                continue
                    if not cas_nummern:
                        found_cas = re.findall(r'(\d{2,7}-\d{2}-\d)', text)
                        cas_nummern.update(found_cas)
                    # --- Suche nach "Gefahrenpiktogramme" und H351 ---
                    if re.search(r'Gefahrenpiktogramme:\s*entfällt', text, re.IGNORECASE):
                        piktogramm_entfaellt_gefunden = True
                    if re.search(r'Gefahrenpiktogramme', text, re.IGNORECASE) and not piktogramm_entfaellt_gefunden:
                        gefahrstoff_info = 'Ja'
                    if re.search(r'H351', text, re.IGNORECASE):
                        gefahrstoff_info = 'Ja'
                    # --- Suche nach Umweltgefahren ---
                    if not umweltgefahr_ja_gefunden:
                        transport_muster = r'(ADN|ADR|RID|IMDG|IATA)[\s\S]*?:\s*ja|Meeresschadstoff\s*:\s*ja'
                        if re.search(transport_muster, text, re.IGNORECASE):
                            umweltgefahr_ja_gefunden = True
                    # --- Hinzugefügte Suche nach Wassergefährdungsklasse (WGK) ---
                    if wgk_number == 'Nicht gefunden':
                        match_wgk = re.search(r'(?:Wassergefährdungsklasse(?:\s*\(WGK\))?|AwSV\s*WGK)[\s\S]*?(\d+)', text, re.IGNORECASE)
                        if match_wgk:
                            wgk_number = match_wgk.group(1)
                    if wgk_number == 'Nicht gefunden':
                        match_wgk_de = re.search(r'Wassergefährdungsklasse\s*\(Deutschland\):[\s\S]*?(\d+)', text, re.IGNORECASE)
                        if match_wgk_de:
                            wgk_number = match_wgk_de.group(1)
                    # --- Suche nach Transportgefahrenklasse ---
                    if not transportklasse:
                        match_transport = re.search(r'Transportgefahrenklassen[\s\S]*?(ADN|ADR|RID|IMDG|IATA)\s*:\s*([\d\.]+)', text, re.IGNORECASE)
                        if match_transport:
                            transportklasse = match_transport.group(2).strip()
                    # --- Suche nach "kann Krebs erzeugen" und H351 ---
                    h351_gefunden = False
                    kann_krebs_erzeugen_gefunden = False
                    if re.search(r'H351', text, re.IGNORECASE):
                        h351_gefunden = True
                    if re.search(r'kann Krebs erzeugen', text, re.IGNORECASE):
                        kann_krebs_erzeugen_gefunden = True
                    if h351_gefunden:
                        krebserzeugend_info = 'Ja (H351)'
                    elif kann_krebs_erzeugen_gefunden:
                        krebserzeugend_info = 'Ja'
                    # --- Suche nach Lagerklasse ---
                    patterns_lagerklasse = [
                        r'Lagerklasse\s*\(TRGS\s*510\)\s*:\s*([^\n]+)',
                        r'Lagerklasse\s*\(LGK\)\s*:\s*([^\n]+)',
                        r'Lagerklasse nach TRGS\s*510:\s*([^\n]+)',
                        r'Lagerklasse:\s*([^\n]+)',
                        r'Lagerklasse\s+([^\n]+)'
                    ]
                    if lagerklasse == 'Nicht gefunden':
                        for pattern in patterns_lagerklasse:
                            match_lk = re.search(pattern, text, re.IGNORECASE)
                            if match_lk:
                                lagerklasse_wert = match_lk.group(1).strip()
                                if ',' in lagerklasse_wert:
                                    lagerklasse = lagerklasse_wert.split(',')[0].strip()
                                else:
                                    lagerklasse = lagerklasse_wert.strip()
                                break
                    # Abbruch, wenn alle wichtigen Informationen gefunden wurden
                    if (handelsname or produktidentifikator) and gefahrstoff_info == 'Ja' and verwendung and h_codes and p_codes and euh_codes and cas_nummern and transportklasse and umweltgefahr_ja_gefunden and wgk_number != 'Nicht gefunden' and krebserzeugend_info != 'Nein' and lagerklasse != 'Nicht gefunden':
                        break
        except Exception as e:
            ergebnisse.append({
                'Datei': file_name,
                'Fehler': str(e)
            })
            continue

        # --- Bestimme Bezeichnung ---
        bezeichnung = handelsname if handelsname else (produktidentifikator if produktidentifikator else 'Nicht gefunden')

        # --- Ergebnisse sammeln ---
        ergebnisse.append({
            'Datei': file_name,
            'Ifd.Nr.': ifd_nr,
            'Bezeichnung': bezeichnung,
            'Verwendung': verwendung if verwendung else 'Nicht gefunden',
            'Gefahrenhinweise (H)': ', '.join(sorted(list(h_codes))) if h_codes else '-',
            'Gefahrenhinweise (EUH)': ', '.join(sorted(list(euh_codes))) if euh_codes else '-',
            'Sicherheitshinweise (P)': ', '.join(sorted(list(p_codes))) if p_codes else '-',
            'CAS-Nummern': ', '.join(sorted(list(cas_nummern))) if cas_nummern else '-',
            'Gefahrenstoff?': gefahrstoff_info,
            'Transportgefahrenklasse': transportklasse if transportklasse else 'Keine Angabe',
            'Umweltgefahr?': 'Ja' if umweltgefahr_ja_gefunden else 'Nein',
            'WGK': wgk_number,
            'Krebserregend': krebserzeugend_info,
            'Lagerklasse': lagerklasse
        })

    # --- DataFrame erstellen ---
    if not ergebnisse:
        return "Keine Daten extrahiert.", None

    df = pd.DataFrame(ergebnisse)
    
    # Rückgabe des DataFrames und einer Erfolgsmeldung
    return "✅ Daten erfolgreich extrahiert!", df

# Gradio-Interface erstellen
iface = gr.Interface(
    fn=extrahiere_gefahrstoffdaten,
    inputs=gr.File(
        label="Laden Sie Ihre PDF-Dateien hoch",
        file_count="multiple",
        file_types=[".pdf"]
    ),
    outputs=[
        gr.Markdown(label="Status"),
        gr.Dataframe(label="Ergebnisse")
    ],
    title="Gefahrstoffdatenblatt-Extraktor 🧪",
    description="Laden Sie eine oder mehrere PDF-Dateien hoch, um relevante Informationen zu extrahieren. Die Ergebnisse werden in einer Tabelle angezeigt."
)

iface.launch()
