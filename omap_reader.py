import xml.etree.ElementTree as ET

class OmapReader:
    def __init__(self, filsti):
        self.filsti = filsti
        print(f"Laster inn vektorkart: {filsti}")
        try:
            self.tree = ET.parse(filsti)
            self.root = self.tree.getroot()
        except Exception as e:
            print(f"Klarte ikke å lese OOM-filen. Feil: {e}")
            self.root = None

        # En liten ordbok over viktige IOF-symboler (ISOM 2017-2)
        # Dette kan utvides etter hvert!
        self.iof_symboler = {
            "201.000": {"navn": "Stein", "type": "punkt", "lopbarhet": 1.0},
            "202.000": {"navn": "Kampestein", "type": "punkt", "lopbarhet": 1.0},
            "104.000": {"navn": "Skrent", "type": "linje", "lopbarhet": 1000.0}, # Upasserbar
            "505.000": {"navn": "Liten sti", "type": "linje", "lopbarhet": 0.5}, # Veldig raskt å løpe
            "502.000": {"navn": "Bred sti", "type": "linje", "lopbarhet": 0.2},  # Enda raskere
            "415.000": {"navn": "Dyrket mark", "type": "flate", "lopbarhet": 5000.0} # Forbudt å løpe
        }

    def finn_alle_objekter(self):
        """Henter ut alle objekter fra kartet som vi har definert i ordboken vår."""
        if self.root is None:
            return []

        funnede_objekter = []

        # OOM lagrer alle tegnede elementer inni <object>-tags
        for obj in self.root.findall('.//object'):
            symbol_id = obj.get('symbol')
            
            if symbol_id in self.iof_symboler:
                coords_tag = obj.find('coords')
                if coords_tag is not None:
                    # Koordinater i OOM lagres som en lang tekststreng: "x1 y1 x2 y2..."
                    koordinater = self._tolk_koordinater(coords_tag.text)
                    
                    info = self.iof_symboler[symbol_id]
                    funnede_objekter.append({
                        "id": symbol_id,
                        "navn": info["navn"],
                        "type": info["type"],
                        "lopbarhet": info["lopbarhet"],
                        "koordinater": koordinater
                    })
        
        return funnede_objekter

    def _tolk_koordinater(self, coord_text):
        """Gjør om en tekststreng med tall til en liste med (x, y)-tupler."""
        if not coord_text:
            return []
        
        # Splitter teksten på mellomrom og gjør om til desimaltall
        tall = [float(x) for x in coord_text.strip().split()]
        
        # Parer dem opp to og to som (x, y)
        punkter = []
        for i in range(0, len(tall), 2):
            if i + 1 < len(tall):
                punkter.append((tall[i], tall[i+1]))
                
        return punkter

# --- TEST-KODE ---
if __name__ == "__main__":
    # Dette kjøres bare hvis du kjører denne filen direkte for å teste
    leser = OmapReader("testkart.omap")
    objekter = leser.finn_alle_objekter()
    
    print(f"\nFant {len(objekter)} kjente objekter i kartet:")
    for obj in objekter:
        print(f"- {obj['navn']} ({obj['type']}): {len(obj['koordinater'])} punkter")