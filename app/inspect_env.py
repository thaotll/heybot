#!/usr/bin/env python3
import os
import sys

# Detaillierte Ausgabe aller Umgebungsvariablen
print("=== ALLE UMGEBUNGSVARIABLEN (DETAILANSICHT) ===")
for key in os.environ:
    value = os.environ[key]
    # Maskiere Werte mit sensiblen Inhalten
    masked_value = "*****" if "KEY" in key or "TOKEN" in key or "SECRET" in key or "URL" in key else value
    
    # Name der Variable analysieren
    print(f"Variable: '{key}'")
    print(f"  Länge des Namens: {len(key)} Zeichen")
    print(f"  ASCII-Codes des Namens: {[ord(c) for c in key]}")
    
    # Wert der Variable analysieren (wenn nicht maskiert)
    if masked_value != "*****":
        print(f"  Wert: '{value}'")
        print(f"  Länge des Werts: {len(value)} Zeichen")
    else:
        print(f"  Wert: {masked_value}")
        print(f"  Länge des Werts: {len(value)} Zeichen")
    
    # Spezifisch nach Discord-Webhook suchen
    if "DISCORD" in key or "discord" in key or "WEBHOOK" in key or "webhook" in key:
        print(f"  *** DISCORD-VARIABLE GEFUNDEN! ***")
        print(f"  Exakter Name: '{key}'")
        print(f"  Zeichen für Zeichen: {[c for c in key]}")

print("\n=== SPEZIFISCHE SUCHE NACH DISCORD ===")
discord_vars = [key for key in os.environ if "DISCORD" in key or "discord" in key]
if discord_vars:
    print(f"Gefundene Discord-Variablen: {discord_vars}")
else:
    print("Keine Variablen mit 'DISCORD' im Namen gefunden.")

# Versuche direkten Zugriff
print("\n=== DIREKTE ZUGRIFFSTESTS ===")
for access_method in ["DISCORD_WEBHOOK_URL", "discord_webhook_url", " DISCORD_WEBHOOK_URL", "DISCORD_WEBHOOK_URL "]:
    value = os.environ.get(access_method)
    print(f"os.environ.get('{access_method}'): {'Gefunden!' if value else 'Nicht gefunden'}")

# Versuche, alle Variablen zu finden, die "webhook" enthalten könnten
print("\n=== SUCHE NACH TEILSTRINGS ===")
for key in os.environ:
    if ("discord" in key.lower() or "webhook" in key.lower() or "url" in key.lower()):
        print(f"Möglicher Treffer: '{key}'")

print("\n=== BYTE-REPRÄSENTATION VON 'DISCORD_WEBHOOK_URL' ===")
var_name = "DISCORD_WEBHOOK_URL"
print(f"String: '{var_name}'")
print(f"Bytes: {var_name.encode()}")
print(f"Hex: {var_name.encode().hex()}")

# Ausgabe der vollständigen environ als Python-Objekt
print("\n=== VOLLSTÄNDIGES ENVIRON ===")
print(repr(dict(os.environ))) 