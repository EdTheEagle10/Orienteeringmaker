import math
import random
import heapq
import numpy as np 

class CourseGenerator:
    def __init__(self, maalestokk, dpi):
        self.maalestokk = maalestokk
        self.dpi = dpi
        self.piksler_per_meter = (dpi / 25.4 * 1000) / maalestokk

        self.krav_matrise = {
            "SPRINT": {"NYBEGYNNER": (0.8, 1.2), "C-LETT": (1.2, 1.8), "A-KORT": (1.5, 2.2), "A-LANG": (2.5, 3.5)},
            "MELLOM": {"NYBEGYNNER": (1.2, 1.8), "C-LETT": (1.8, 2.5), "A-KORT": (2.2, 3.2), "A-LANG": (3.5, 5.0)},
            "LANG": {"NYBEGYNNER": (1.5, 2.5), "C-LETT": (2.0, 3.0), "A-KORT": (3.5, 4.5), "A-LANG": (5.0, 9.0)}
        }

    def generer_postkoder(self, antall):
        return random.sample(range(31, 200), antall)

    def _oversett_klasse_til_nivaa(self, klasse):
        if klasse == "NYBEGYNNER": return "N"
        if klasse == "C-LETT": return "C"
        return "A" 

    def sjekk_vinkel(self, punkt_a, punkt_b, punkt_c):
        ba = (punkt_a[0] - punkt_b[0], punkt_a[1] - punkt_b[1])
        bc = (punkt_c[0] - punkt_b[0], punkt_c[1] - punkt_b[1])
        prikkprodukt = ba[0] * bc[0] + ba[1] * bc[1]
        lengde_ba = math.hypot(ba[0], ba[1])
        lengde_bc = math.hypot(bc[0], bc[1])
        if lengde_ba == 0 or lengde_bc == 0: return 0
        cos_theta = max(-1.0, min(1.0, prikkprodukt / (lengde_ba * lengde_bc)))
        return math.degrees(math.acos(cos_theta))

    def strek_krysser_forbudt(self, p1, p2, cost_map):
        avstand = int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        if avstand < 2: return False
        x_verdier = np.linspace(p1[0], p2[0], avstand).astype(int)
        y_verdier = np.linspace(p1[1], p2[1], avstand).astype(int)
        h, w = cost_map.shape
        for x, y in zip(x_verdier, y_verdier):
            if 0 <= x < w and 0 <= y < h:
                if cost_map[y, x] >= 5000.0: return True
        return False

    def smart_reparasjon(self, loype, aktuelle_detaljer, maks_strekk_px):
        ny_loype = [loype[0]]
        for i in range(1, len(loype)):
            p1, p2 = ny_loype[-1], loype[i]
            avstand = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
            if avstand > maks_strekk_px:
                antall_ekstra = int(avstand // maks_strekk_px)
                for step in range(1, antall_ekstra + 1):
                    fraksjon = step / (antall_ekstra + 1)
                    mx, my = p1[0] + (p2[0]-p1[0])*fraksjon, p1[1] + (p2[1]-p1[1])*fraksjon
                    beste = min(aktuelle_detaljer, key=lambda p: math.hypot(p[0]-mx, p[1]-my))
                    if beste not in ny_loype and beste != p2: ny_loype.append(beste)
            if p2 not in ny_loype: ny_loype.append(p2)
        return ny_loype

    def generer_perfekt_loype(self, lovlige_detaljer, avstandskart, cost_map, klasse, format_type, antall_poster, start_punkt, maal_punkt):
        nivaa = self._oversett_klasse_til_nivaa(klasse)
        
        aktuelle_detaljer = []
        if format_type == "SPRINT" or nivaa == "A":
            aktuelle_detaljer = lovlige_detaljer.copy()
        else:
            for x, y in lovlige_detaljer:
                avstand_meter = avstandskart[y, x] / self.piksler_per_meter
                if nivaa == "N" and avstand_meter <= 25: aktuelle_detaljer.append((x, y))
                elif nivaa == "C" and avstand_meter <= 65: aktuelle_detaljer.append((x, y))

        if len(aktuelle_detaljer) < 3:
            aktuelle_detaljer = lovlige_detaljer.copy()

        if len(aktuelle_detaljer) < 2:
            return None

        min_km, maks_km = self.krav_matrise[format_type][klasse]
        min_m, maks_m = min_km * 1000, maks_km * 1000

        h, w = cost_map.shape
        diagonal_m = math.hypot(w, h) / self.piksler_per_meter
        
        if min_m > diagonal_m * 2.5:
            ny_min = diagonal_m * 1.5
            min_m, maks_m = ny_min * 0.8, ny_min * 1.2

        grense_m = 250 if format_type == "SPRINT" else 400 if format_type == "MELLOM" else 900
        maks_strekk_px = grense_m * self.piksler_per_meter

        beste_kandidat = None
        min_straff = float('inf')

        # Vi kjører flere forsøk nå for å finne den aller fineste formen
        for forsok in range(3000):
            n = random.randint(4, max(5, antall_poster))
            n = min(n, len(aktuelle_detaljer))
            
            mellom = random.sample(aktuelle_detaljer, n)
            
            # --- MAGIEN: Rundløype-sortering ---
            # 1. Finn sentrum av alle valgte poster
            cx = sum(p[0] for p in mellom) / len(mellom)
            cy = sum(p[1] for p in mellom) / len(mellom)
            
            # 2. Sorter postene i en geometrisk sirkel basert på vinkel
            mellom.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
            
            # 3. Finn hvilken av postene i sirkelen som er nærmest Start-punktet
            naermest_idx = 0
            min_avstand_start = float('inf')
            for i, p in enumerate(mellom):
                dist = math.hypot(p[0]-start_punkt[0], p[1]-start_punkt[1])
                if dist < min_avstand_start:
                    min_avstand_start = dist
                    naermest_idx = i
                    
            # 4. "Vri" på sirkelen slik at posten nærmest Start blir post nr 1
            mellom = mellom[naermest_idx:] + mellom[:naermest_idx]
            
            # Av og til løper vi motsatt vei rundt sirkelen for variasjon
            if random.choice([True, False]):
                mellom = mellom[::-1]
            # ------------------------------------
                
            kandidat = [start_punkt] + mellom + [maal_punkt]
            
            # Bruk reparasjonen til å bryte opp kjempelange strekk i sirkelen
            kandidat = self.smart_reparasjon(kandidat, aktuelle_detaljer, maks_strekk_px)
            
            lengde = self.beregn_loypelengde(kandidat)
            
            # Grunnstraff basert på feil lengde
            straff = abs(lengde - (min_m + maks_m)/2)
            
            for i in range(len(kandidat)-1):
                if self.strek_krysser_forbudt(kandidat[i], kandidat[i+1], cost_map):
                    straff += 5000 
            
            # Veldig streng straff for dog-legs og ulogiske kryss i løypa
            for i in range(len(kandidat)-2):
                vinkel = self.sjekk_vinkel(kandidat[i], kandidat[i+1], kandidat[i+2])
                if vinkel < 60:
                    straff += 1500 # AI-en vil nå HATE edderkoppnett og tvinges til å velge runde ruter!
            
            if straff < min_straff:
                min_straff = straff
                beste_kandidat = kandidat.copy()
                if straff < 50: break # Fantastisk løype funnet!

        return beste_kandidat

    def beregn_loypelengde(self, loype):
        total = 0
        for i in range(len(loype) - 1):
            total += math.hypot(loype[i+1][0]-loype[i][0], loype[i+1][1]-loype[i][1])
        return total / self.piksler_per_meter

    def beregn_stigning(self, loype, mask_kurver, ekvidistanse=5):
        kryssinger = 0
        h, w = mask_kurver.shape
        for i in range(len(loype) - 1):
            p1, p2 = loype[i], loype[i+1]
            avstand = int(math.hypot(p2[0]-p1[0], p2[1]-p1[1]))
            if avstand < 2: continue
            x_v, y_v = np.linspace(p1[0], p2[0], avstand).astype(int), np.linspace(p1[1], p2[1], avstand).astype(int)
            paa = False
            for x, y in zip(x_v, y_v):
                if 0 <= x < w and 0 <= y < h:
                    if mask_kurver[y, x] > 0:
                        if not paa: kryssinger += 1; paa = True
                    else: paa = False
        return (kryssinger * ekvidistanse) / 2

class RouteAnalyzer:
    @staticmethod
    def finn_beste_veivalg(cost_map, start, maal):
        h, w = cost_map.shape
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from, cost_so_far = {start: None}, {start: 0}
        while frontier:
            _, curr = heapq.heappop(frontier)
            if math.hypot(curr[0]-maal[0], curr[1]-maal[1]) < 5: maal = curr; break
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]:
                nxt = (curr[0]+dx, curr[1]+dy)
                if 0 <= nxt[0] < w and 0 <= nxt[1] < h:
                    step = cost_map[nxt[1], nxt[0]]
                    if dx!=0 and dy!=0: step *= 1.414
                    if step >= 1000: continue
                    new_c = cost_so_far[curr] + step
                    if nxt not in cost_so_far or new_c < cost_so_far[nxt]:
                        cost_so_far[nxt] = new_c
                        heapq.heappush(frontier, (new_c + math.hypot(maal[0]-nxt[0], maal[1]-nxt[1]), nxt))
                        came_from[nxt] = curr
        rute, curr = [], maal
        while curr in came_from: rute.append(curr); curr = came_from[curr]
        return rute[::-1]
