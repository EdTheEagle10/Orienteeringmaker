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
            "SPRINT": {"NYBEGYNNER": (1.5, 2.5), "C-LETT": (2.0, 3.0), "A-KORT": (2.0, 3.0), "A-LANG": (2.0, 3.0)},
            "MELLOM": {"NYBEGYNNER": (1.5, 2.5), "C-LETT": (2.0, 3.0), "A-KORT": (3.0, 4.0), "A-LANG": (5.0, 6.0)},
            "LANG": {"NYBEGYNNER": (2.5, 3.5), "C-LETT": (3.0, 4.0), "A-KORT": (4.0, 6.0), "A-LANG": (7.0, 10.0)}
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

    # --- NYTT: Finner nøyaktig HVOR dog-legen er ---
    def finn_dogleg_indeks(self, loype, minimum_vinkel=75):
        for i in range(len(loype) - 2):
            if self.sjekk_vinkel(loype[i], loype[i+1], loype[i+2]) < minimum_vinkel:
                return i + 1 # Returnerer hvilken post som er den spisse vinkelen
        return -1

    def beregn_strekk_lengder(self, loype):
        strekk = []
        for i in range(len(loype) - 1):
            avstand = math.hypot(loype[i+1][0] - loype[i][0], loype[i+1][1] - loype[i][1])
            strekk.append(avstand / self.piksler_per_meter)
        return strekk

    def strek_krysser_forbudt(self, p1, p2, cost_map):
        avstand = int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        if avstand == 0: return False
        x_verdier = np.linspace(p1[0], p2[0], avstand).astype(int)
        y_verdier = np.linspace(p1[1], p2[1], avstand).astype(int)
        h, w = cost_map.shape
        for x, y in zip(x_verdier, y_verdier):
            if 0 <= x < w and 0 <= y < h:
                if cost_map[y, x] >= 5000.0: 
                    return True
        return False

    def generer_perfekt_loype(self, lovlige_detaljer, avstandskart, cost_map, klasse, format_type, antall_poster, start_punkt, maal_punkt):
        nivaa = self._oversett_klasse_til_nivaa(klasse)
        aktuelle_detaljer = []
        min_post_avstand = 15 if format_type == "SPRINT" else 50
        min_km, maks_km = self.krav_matrise[format_type][klasse]
        min_meter, maks_meter = min_km * 1000, maks_km * 1000

        if format_type == "SPRINT" or nivaa == "A":
            aktuelle_detaljer = lovlige_detaljer.copy()
        else:
            for x, y in lovlige_detaljer:
                avstand_meter = avstandskart[y, x] / self.piksler_per_meter
                if nivaa == "N" and avstand_meter <= 20: 
                    aktuelle_detaljer.append((x, y))
                elif nivaa == "C" and 15 < avstand_meter <= 60:
                    aktuelle_detaljer.append((x, y))

        if len(aktuelle_detaljer) < antall_poster:
            print("Feil: Kartet har for få detaljer tilgjengelig.")
            return None

        piksler_per_mm = self.dpi / 25.4
        beste_kandidat = None
        beste_differanse = float('inf')
        noed_kandidat = None
        noed_differanse = float('inf')
        gyldige_kandidater = []

        for forsok in range(20000): 
            mellom_poster = random.sample(aktuelle_detaljer, antall_poster)
            kandidat = [start_punkt] + mellom_poster + [maal_punkt]
            
            # --- LØSNING 2: DYNAMISK KNEKKPOST-FIKSER ---
            # Hvis løypa har en dogleg, smetter AI-en inn en ekstra post for å bøye den!
            for fiks in range(4): # Prøver maks 4 knekkposter per løype
                dl_idx = self.finn_dogleg_indeks(kandidat, minimum_vinkel=75)
                if dl_idx == -1: break # Ingen doglegs = perfekt!
                
                # Finner en tilfeldig ny post og skyter den inn for å knekke vinkelen
                knekkpost = random.choice(aktuelle_detaljer)
                kandidat.insert(dl_idx + 1, knekkpost)
                
            # Hvis den FORTSATT har doglegs etter 4 fikse-forsøk, kaster vi den.
            if self.finn_dogleg_indeks(kandidat, 75) != -1: 
                continue

            # 1. Avstands-sjekk
            avstand_ok = True
            for i in range(len(kandidat)):
                for j in range(i + 1, len(kandidat)):
                    if i == 0 and j == len(kandidat) - 1: continue
                    d_piksler = math.hypot(kandidat[i][0] - kandidat[j][0], kandidat[i][1] - kandidat[j][1])
                    if (((d_piksler / piksler_per_mm) * self.maalestokk) / 1000) < min_post_avstand:
                        avstand_ok = False
                        break
                if not avstand_ok: break
            if not avstand_ok: continue

            # Regn ut lengde
            lengde_meter = self.beregn_loypelengde(kandidat)
            differanse = min(abs(lengde_meter - min_meter), abs(lengde_meter - maks_meter))

            if differanse < noed_differanse:
                noed_differanse = differanse
                noed_kandidat = kandidat

            # 2. Laser-sjekk (Ikke kryss forbudt)
            krysser_forbudt = False
            for i in range(len(kandidat) - 1):
                if self.strek_krysser_forbudt(kandidat[i], kandidat[i+1], cost_map):
                    krysser_forbudt = True
                    break
            if krysser_forbudt: continue

            # --- VI FANT EN PERFEKT LØYPE! ---
            if min_meter <= lengde_meter <= maks_meter:
                strekk_lengder = self.beregn_strekk_lengder(kandidat)
                variasjon_score = np.std(strekk_lengder) 
                gyldige_kandidater.append((variasjon_score, kandidat))
                
                if len(gyldige_kandidater) >= 20:
                    break
                
            if differanse < beste_differanse:
                beste_differanse = differanse
                beste_kandidat = kandidat

        if gyldige_kandidater:
            gyldige_kandidater.sort(key=lambda x: x[0], reverse=True)
            return gyldige_kandidater[0][1]

        if beste_kandidat is not None:
            return beste_kandidat
        if noed_kandidat is not None:
            return noed_kandidat
            
        return None

    def beregn_loypelengde(self, loype):
        total_meter = 0
        for i in range(len(loype) - 1):
            avstand = math.hypot(loype[i+1][0] - loype[i][0], loype[i+1][1] - loype[i][1])
            total_meter += avstand / self.piksler_per_meter
        return total_meter

    def beregn_stigning(self, loype, mask_kurver, ekvidistanse=5):
        kryssinger = 0
        h, w = mask_kurver.shape
        for i in range(len(loype) - 1):
            p1, p2 = loype[i], loype[i+1]
            avstand = int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]))
            if avstand == 0: continue
            x_verdier = np.linspace(p1[0], p2[0], avstand).astype(int)
            y_verdier = np.linspace(p1[1], p2[1], avstand).astype(int)
            paa_kurve = False
            for x, y in zip(x_verdier, y_verdier):
                if 0 <= x < w and 0 <= y < h:
                    if mask_kurver[y, x] > 0:
                        if not paa_kurve:
                            kryssinger += 1
                            paa_kurve = True
                    else:
                        paa_kurve = False
        return (kryssinger * ekvidistanse) / 2

class RouteAnalyzer:
    @staticmethod
    def finn_beste_veivalg(cost_map, start, maal):
        h, w = cost_map.shape
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        retninger = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

        while frontier:
            _, current = heapq.heappop(frontier)
            if math.hypot(current[0] - maal[0], current[1] - maal[1]) < 4:
                maal = current 
                break
            for dx, dy in retninger:
                next_node = (current[0] + dx, current[1] + dy)
                if 0 <= next_node[0] < w and 0 <= next_node[1] < h:
                    step_cost = cost_map[next_node[1], next_node[0]]
                    if dx != 0 and dy != 0: step_cost *= 1.414 
                    if step_cost >= 1000: continue 
                    new_cost = cost_so_far[current] + step_cost
                    if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + math.hypot(maal[0]-next_node[0], maal[1]-next_node[1])
                        heapq.heappush(frontier, (priority, next_node))
                        came_from[next_node] = current
        rute = []
        current = maal
        while current in came_from and current is not None:
            rute.append(current)
            current = came_from[current]
        rute.reverse()
        return rute