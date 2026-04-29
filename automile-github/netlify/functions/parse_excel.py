import openpyxl
import json
import base64
import io

def handler(event, context):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Content-Type": "application/json"
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": cors, "body": ""}

    try:
        body = event.get("body", "")
        if event.get("isBase64Encoded"):
            file_bytes = base64.b64decode(body)
        else:
            file_bytes = base64.b64decode(body)

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active

        # Find header row (contains 'Startadress')
        header_row_idx = None
        all_rows = list(ws.iter_rows(values_only=True))
        for i, row in enumerate(all_rows):
            if any(str(v or '').lower() == 'startadress' for v in row):
                header_row_idx = i
                break

        if header_row_idx is None:
            return {
                "statusCode": 400,
                "headers": cors,
                "body": json.dumps({"error": "Hittade ingen rubrikrad med 'Startadress'"})
            }

        headers = [str(v or '').strip() for v in all_rows[header_row_idx]]
        
        def col(names):
            for n in names:
                for i, h in enumerate(headers):
                    if n.lower() in h.lower():
                        return i
            return -1

        ci = {
            'date':   col(['Startat', 'Datum']),
            'from':   col(['Startadress']),
            'to':     col(['Slutadress']),
            'km':     col(['Körsträcka', 'Sträcka', 'Km']),
            'type':   col(['Restyp', 'Typ']),
            'note':   col(['Anteckningar', 'Anteckning']),
            'driver': col(['Förare']),
        }

        trips = []
        for row in all_rows[header_row_idx + 1:]:
            if not row or all(v is None or v == '' for v in row):
                continue
            
            def g(key):
                i = ci[key]
                return str(row[i] or '').strip() if i >= 0 and i < len(row) else ''

            frm = g('from')
            to  = g('to')
            if not frm and not to:
                continue

            # Parse date
            date_val = row[ci['date']] if ci['date'] >= 0 and ci['date'] < len(row) else None
            if hasattr(date_val, 'isoformat'):
                date_str = date_val.isoformat()
            else:
                date_str = str(date_val or '').split(' - ')[0].strip()

            # Parse km
            km_raw = row[ci['km']] if ci['km'] >= 0 and ci['km'] < len(row) else 0
            try:
                km = float(str(km_raw).replace(',', '.').replace(' ', '').split()[0])
            except:
                km = 0.0

            # Parse type
            type_raw = g('type').lower()
            if 'tjänst' in type_raw or 'business' in type_raw:
                imported_type = 'business'
            elif 'privat' in type_raw or 'private' in type_raw:
                imported_type = 'private'
            else:
                imported_type = None

            trips.append({
                'date': date_str,
                'from': frm,
                'to': to,
                'km': round(km, 2),
                'importedType': imported_type,
                'note': g('note'),
                'driver': g('driver'),
            })

        return {
            "statusCode": 200,
            "headers": cors,
            "body": json.dumps({"trips": trips, "count": len(trips)})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors,
            "body": json.dumps({"error": str(e)})
        }
