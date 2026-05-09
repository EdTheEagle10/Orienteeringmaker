import cv2
import numpy as np
import random 

class MapAnalyzer:
    def __init__(self, bilde, spraak="NO"):
        self.bilde = bilde
        self.spraak = spraak
        self.hsv = cv2.cvtColor(self.bilde, cv2.COLOR_BGR2HSV)
        self.cost_map = None
        self.lovlige_detaljer = [] 
        self.detalj_typer = {} 
        self.avstand_til_sti = None 
        self.mask_kurver = None 
        self._analyser_kart()

    def _finn_detaljer_i_maske(self, maske, forbudt_sone, min_areal, max_areal, sirkel_krav=0.0):
        funn = []
        konturer, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for k in konturer:
            areal = cv2.contourArea(k)
            if min_areal < areal < max_areal:
                M = cv2.moments(k)
                if M['m00'] != 0:
                    x, y = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
                    if forbudt_sone[y, x] == 0:
                        if sirkel_krav > 0:
                            omkrets = cv2.arcLength(k, True)
                            if omkrets > 0:
                                sirkularitet = (4 * np.pi * areal) / (omkrets * omkrets)
                                if sirkularitet >= sirkel_krav:
                                    funn.append((x, y))
                        else:
                            funn.append((x, y))
        return funn

    def _analyser_kart(self):
        h, w = self.bilde.shape[:2]
        self.cost_map = np.full((h, w), 5000.0, dtype=np.float32)
        
        graatone = cv2.cvtColor(self.bilde, cv2.COLOR_BGR2GRAY)
        kart_maske = cv2.threshold(graatone, 250, 255, cv2.THRESH_BINARY_INV)[1]
        self.cost_map[kart_maske > 0] = 1.0
        
        mask_svart = cv2.inRange(self.hsv, np.array([0, 0, 0]), np.array([180, 255, 75]))
        self.cost_map[mask_svart > 0] = 0.5 
        
        mask_gronn = cv2.inRange(self.hsv, np.array([35, 50, 50]), np.array([85, 255, 200]))
        self.cost_map[mask_gronn > 0] = 4.0 
        
        mask_blaa = cv2.inRange(self.hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
        self.cost_map[mask_blaa > 0] = 1000.0 
        
        mask_oliven = cv2.inRange(self.hsv, np.array([20, 100, 100]), np.array([35, 255, 200]))
        self.cost_map[mask_oliven > 0] = 5000.0 
        
        mask_brun = cv2.inRange(self.hsv, np.array([10, 100, 50]), np.array([25, 255, 200]))
        self.cost_map[mask_brun > 0] += 5.0 # Vanlig kurvekryssing koster litt

        # --- NYTT: ANTI-BRATT FJELLSIDE (TETTHET AV HØYDEKURVER) ---
        # Vi legger en enorm uskarphet over kurvene. Tette kurver smelter sammen til store flekker.
        tetthet_kurver = cv2.GaussianBlur(mask_brun, (21, 21), 0)
        
        # Der kurvene smelter sammen (høy tetthet), lager vi en "bratt-maske"
        mask_bratt = cv2.threshold(tetthet_kurver, 40, 255, cv2.THRESH_BINARY)[1]
        
        # Vi gir bratte områder en enorm straff (f.eks. +150 i kostnad per piksel)
        # Dette tvinger stifinneren til å velge slakere veier rundt fjellet!
        self.cost_map[mask_bratt > 0] += 150.0 
        # ------------------------------------------------------------

        self.mask_kurver = mask_brun.copy()

        kernel = np.ones((2,2), np.uint8)
        mask_svart = cv2.morphologyEx(mask_svart, cv2.MORPH_OPEN, kernel)
        mask_brun = cv2.morphologyEx(mask_brun, cv2.MORPH_OPEN, kernel)
        kernel_tekst = np.ones((3,3), np.uint8)
        mask_svart_detaljer = cv2.morphologyEx(mask_svart, cv2.MORPH_OPEN, kernel_tekst)
        mask_brun_detaljer = cv2.morphologyEx(mask_brun, cv2.MORPH_OPEN, kernel_tekst)

        konturer_vann, _ = cv2.findContours(mask_blaa, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask_hav = np.zeros_like(mask_blaa)
        for k in konturer_vann:
            if cv2.contourArea(k) > 300: 
                cv2.drawContours(mask_hav, [k], -1, 255, -1)

        mask_forbudt = cv2.bitwise_or(mask_oliven, mask_hav)
        forbudt_sone_poster = cv2.dilate(mask_forbudt, np.ones((40,40), np.uint8), iterations=1)

        steiner = self._finn_detaljer_i_maske(mask_svart_detaljer, forbudt_sone_poster, 4, 100, 0.6)
        skrenter = self._finn_detaljer_i_maske(mask_svart_detaljer, forbudt_sone_poster, 15, 200, 0.0)
        brune_detaljer = self._finn_detaljer_i_maske(mask_brun_detaljer, forbudt_sone_poster, 4, 100, 0.3)
        blaa_detaljer = self._finn_detaljer_i_maske(mask_blaa, forbudt_sone_poster, 4, 80, 0.4)

        mask_stier = mask_svart.copy()
        for x, y in steiner + skrenter:
            cv2.circle(mask_stier, (x, y), 8, 0, -1)
            
        kryss_punkter = cv2.goodFeaturesToTrack(mask_stier, maxCorners=150, qualityLevel=0.1, minDistance=30)
        stikryss = []
        if kryss_punkter is not None:
            for pt in kryss_punkter:
                x, y = int(pt[0][0]), int(pt[0][1])
                if forbudt_sone_poster[y, x] == 0:
                    stikryss.append((x, y))

        trans = {
            "NO": {"stein": "Stein", "skrent": "Skrent", "grop": "Grop", "vann": "Vannhull", "kryss": "Stikryss", "y": "Y-kryss",
                   "n": "Nordre", "s": "Søndre", "e": "Østre", "w": "Vestre", "nw": "Nordvestre", "ne": "Nordøstre", "sw": "Sørvestre", "se": "Sørøstre",
                   "side": "side", "fot": "Foten", "ovre": "Øvre kant", "kant": "kant", "ikryss": "I krysset"},
            "EN": {"stein": "Boulder", "skrent": "Earth bank", "grop": "Pit", "vann": "Waterhole", "kryss": "Path crossing", "y": "Path junction",
                   "n": "Northern", "s": "Southern", "e": "Eastern", "w": "Western", "nw": "North-Western", "ne": "North-Eastern", "sw": "South-Western", "se": "South-Eastern",
                   "side": "side", "fot": "Foot", "ovre": "Upper part", "kant": "edge", "ikryss": "In junction"},
            "SV": {"stein": "Sten", "skrent": "Brant", "grop": "Grop", "vann": "Vattenhål", "kryss": "Stigkorsning", "y": "Stigförgrening",
                   "n": "Norra", "s": "Södra", "e": "Östra", "w": "Västra", "nw": "Nordvästra", "ne": "Nordöstra", "sw": "Sydvästra", "se": "Sydöstra",
                   "side": "sida", "fot": "Foten", "ovre": "Övre kanten", "kant": "kant", "ikryss": "I korsningen"},
            "DE": {"stein": "Felsblock", "skrent": "Böschung", "grop": "Senke", "vann": "Wasserloch", "kryss": "Wegekreuzung", "y": "Wegabzweigung",
                   "n": "Nord", "s": "Süd", "e": "Ost", "w": "West", "nw": "Nordwest", "ne": "Nordost", "sw": "Südwest", "se": "Südost",
                   "side": "Seite", "fot": "Fuß", "ovre": "Oberer Teil", "kant": "Rand", "ikryss": "An der Kreuzung"}
        }
        t = trans.get(self.spraak, trans["NO"])
        retninger = ["n", "s", "e", "w", "nw", "ne", "sw", "se"]

        self.detalj_typer = {}
        for p in steiner:
            r = random.choice(retninger)
            self.detalj_typer[p] = {"sym": "stein", "ret": r.upper(), "tekst": f"{t['stein']}, {t[r]} {t['side']}"}
        for p in skrenter:
            r = random.choice(["fot", "ovre"])
            self.detalj_typer[p] = {"sym": "skrent", "ret": r, "tekst": f"{t['skrent']}, {t[r]}"}
        for p in brune_detaljer:
            r = random.choice(retninger)
            self.detalj_typer[p] = {"sym": "grop", "ret": r.upper(), "tekst": f"{t['grop']}, {t[r]} {t['kant']}"}
        for p in blaa_detaljer:
            r = random.choice(retninger)
            self.detalj_typer[p] = {"sym": "vann", "ret": r.upper(), "tekst": f"{t['vann']}, {t[r]} {t['kant']}"}
        for p in stikryss:
            sym = random.choice(["kryss", "y"])
            self.detalj_typer[p] = {"sym": sym, "ret": "ikryss", "tekst": f"{t[sym]}, {t['ikryss']}"}

        self.lovlige_detaljer = list(self.detalj_typer.keys())
        ledelinjer = cv2.bitwise_or(mask_svart, mask_blaa) 
        for x, y in self.lovlige_detaljer: cv2.circle(ledelinjer, (x, y), 5, 0, -1) 
        invertert = cv2.bitwise_not(ledelinjer)
        self.avstand_til_sti = cv2.distanceTransform(invertert, cv2.DIST_L2, 5)