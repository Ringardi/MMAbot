"""Prueba si BestFightOdds y el JSON de Kambi (Unibet) responden desde este servidor.

Correr en Railway: python3 scripts/test_cuotas.py
Sin dependencias: solo librería estándar.
"""
import json
import re
import sys
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BFO = "https://www.bestfightodds.com"
KAMBI = ("https://eu-offering-api.kambicdn.com/offering/v2018/ubuk/listView/"
         "mma.json?lang=en_GB&market=GB")
ORGS = ("oktagon", "cage-warriors")
CASAS = ("Pinnacle", "Betway", "Unibet", "Caesars", "DraftKings", "FanDuel",
         "BetMGM", "bet365", "Bet365", "BetOnline", "Bovada", "Bet105",
         "Circa", "Cloudbet", "BetRivers", "Jazz", "SX Bet", "Polymarket")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, str(e)


def bloqueado(html):
    return any(s in html for s in ("Just a moment", "cf-chl", "Attention Required",
                                   "Access denied"))


def probar_bfo():
    print("=== BestFightOdds ===")
    status, html = get(BFO + "/")
    print(f"Home: HTTP {status}, {len(html)} bytes")
    if status != 200 or bloqueado(html):
        print("RESULTADO: BLOQUEADO o caido -> usar plan B (Kambi)")
        return False

    eventos = sorted(set(re.findall(r'href="(/events/(?:%s)-[^"]+)"' % "|".join(ORGS), html)))
    if not eventos:
        print("No hay eventos de Oktagon ni Cage Warriors en la home ahora mismo.")
        print("RESULTADO: BFO responde, pero sin eventos de estas orgs hoy para probar las cuotas.")
        return True

    ok = True
    for path in eventos:
        status, page = get(BFO + path)
        if status != 200 or bloqueado(page):
            print(f"{path}: HTTP {status} BLOQUEADO")
            ok = False
            continue
        peleadores = len(set(re.findall(r'href="/fighters/[^"]+"', page)))
        casas = [c for c in CASAS if c in page]
        cuotas = len(re.findall(r">\s*[+-]\d{3,4}\s*<", page))
        print(f"{path}: HTTP 200 | peleadores: {peleadores} | "
              f"cuotas: {cuotas} | casas: {', '.join(casas) or 'ninguna detectada'}")
        if cuotas == 0:
            ok = False
    print("RESULTADO:", "FUNCIONA" if ok else "responde pero sin cuotas legibles en algun evento")
    return ok


def probar_kambi():
    print("\n=== Kambi / Unibet (plan B) ===")
    status, body = get(KAMBI)
    print(f"HTTP {status}, {len(body)} bytes")
    if status != 200:
        print("RESULTADO: no responde")
        return False
    try:
        data = json.loads(body)
    except ValueError:
        print("RESULTADO: no devolvio JSON")
        return False
    grupos = {}
    for ev in data.get("events", []):
        nombre = " / ".join(p.get("name", "") for p in ev.get("event", {}).get("path", []))
        con_precio = any(o.get("odds") for bo in ev.get("betOffers", [])
                         for o in bo.get("outcomes", []))
        g = grupos.setdefault(nombre, [0, 0])
        g[0] += 1
        g[1] += con_precio
    for nombre, (n, p) in sorted(grupos.items()):
        print(f"{nombre}: {n} peleas, {p} con cuota")
    hay = any(o in n.lower().replace(" ", "-") for n in grupos for o in ORGS)
    print("RESULTADO:", "FUNCIONA con Oktagon/CW" if hay else "responde, pero hoy sin Oktagon ni CW")
    return hay


if __name__ == "__main__":
    bfo = probar_bfo()
    kambi = probar_kambi()
    sys.exit(0 if (bfo or kambi) else 1)
