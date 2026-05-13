import cv2
import numpy as np
import math
from PIL import ImageFont, ImageDraw, Image
from course_generator import RouteAnalyzer

class MapRenderer:
    def __init__(self, bilde, spraak="NO"):
        self.bilde = bilde
        self.o_farge = (143, 0, 200) # Lilla IOF-farge
        self.spraak = spraak
        
        self.T = {
            "NO": {"len": "Lengde", "climb": "Stigning", "s": "S", "m": "M"},
            "EN": {"len": "Length", "climb": "Climb", "s": "S", "m": "F"},
            "SV": {"len": "Längd", "climb": "Stigning", "s": "S", "m": "M"},
            "DE": {"len": "Länge", "climb": "Steigung", "s": "S", "m": "Z"}
        }

    def finn_kant_punkt(self, p1, p2, radius1, radius2):
        x1, y1 = p1
        x2, y2 = p2
        avstand = math.hypot(x2 - x1, y2 - y1)
        if avstand == 0: return p1, p2 
        dx, dy = (x2 - x1) / avstand, (y2 - y1) / avstand
        return (int(x1 + dx * (radius1 + 2)), int(y1 + dy * (radius1 + 2))), \
               (int(x2 - dx * (radius2 + 2)), int(y2 - dy * (radius2 + 2)))

    def tegn_stiplet_rute(self, bilde, rute, skala, farge, tykkelse, stipellengde=6):
        for k in range(0, len(rute)-1, stipellengde * 2):
            slutt = min(k + stipellengde, len(rute) - 1)
            for j in range(k, slutt):
                pt1 = (int(rute[j][0]/skala), int(rute[j][1]/skala))
                pt2 = (int(rute[j+1][0]/skala), int(rute[j+1][1]/skala))
                cv2.line(bilde, pt1, pt2, farge, tykkelse)

    def start_tekst_lag(self):
        self.pil_img = Image.fromarray(cv2.cvtColor(self.bilde, cv2.COLOR_BGR2RGB))
        self.draw = ImageDraw.Draw(self.pil_img)

    def tegn_tekst(self, tekst, pos, font_size_cv, farge_bgr, tykkelse=1, halo=False):
        farge_rgb = (farge_bgr[2], farge_bgr[1], farge_bgr[0])
        x, y = pos
        pil_strelse = int(font_size_cv * 32) 
        
        try:
            font = ImageFont.truetype("arial.ttf", pil_strelse)
            font_bold = ImageFont.truetype("arialbd.ttf", pil_strelse)
        except IOError:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", pil_strelse)
                font_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", pil_strelse)
            except IOError:
                font = font_bold = ImageFont.load_default()

        valgt_font = font_bold if tykkelse > 1 else font

        # Hvit outline rundt teksten
        if halo:
            o_range = 2 if tykkelse > 1 else 1
            for dx in range(-o_range, o_range+1):
                for dy in range(-o_range, o_range+1):
                    self.draw.text((x+dx, y+dy), tekst, font=valgt_font, fill=(255,255,255), anchor="ls")

        self.draw.text((x, y), tekst, font=valgt_font, fill=farge_rgb, anchor="ls")

    def bruk_tekst_lag(self):
        nytt_bilde = cv2.cvtColor(np.array(self.pil_img), cv2.COLOR_RGB2BGR)
        np.copyto(self.bilde, nytt_bilde)

    def tegn_loype(self, loype, koder, cost_map, radius=20, skala=0.25):
        overlay = self.bilde.copy()
        lite_map = cv2.resize(cost_map, (0,0), fx=skala, fy=skala, interpolation=cv2.INTER_NEAREST)
        
        for i in range(len(loype) - 1):
            p1 = (int(loype[i][0]*skala), int(loype[i][1]*skala))
            p2 = (int(loype[i+1][0]*skala), int(loype[i+1][1]*skala))
            lokalt_kart = lite_map.copy()
            avstand = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
            
            rute1 = RouteAnalyzer.finn_beste_veivalg(lokalt_kart, p1, p2)
            for j in range(len(rute1)-1):
                pt1 = (int(rute1[j][0]/skala), int(rute1[j][1]/skala))
                pt2 = (int(rute1[j+1][0]/skala), int(rute1[j+1][1]/skala))
                cv2.line(overlay, pt1, pt2, (0, 255, 255), 4)

            if avstand > 30: 
                for pt in rute1: cv2.circle(lokalt_kart, pt, 10, 3000.0, -1)
                rute2 = RouteAnalyzer.finn_beste_veivalg(lokalt_kart, p1, p2)
                if len(rute2) > 0:
                    self.tegn_stiplet_rute(overlay, rute2, skala, (255, 150, 0), 3) 
                    for pt in rute2: cv2.circle(lokalt_kart, pt, 10, 3000.0, -1)
                    rute3 = RouteAnalyzer.finn_beste_veivalg(lokalt_kart, p1, p2)
                    if len(rute3) > 0:
                        self.tegn_stiplet_rute(overlay, rute3, skala, (200, 100, 255), 3) 
                
        cv2.addWeighted(overlay, 0.5, self.bilde, 0.5, 0, self.bilde)

        # --- NYTT: PURPLE PEN HALO-EFFEKT ---
        loype_lag = np.zeros_like(self.bilde)
        halo_lag = np.zeros_like(self.bilde)

        # Tegner hvite bakgrunner først
        for i in range(len(loype) - 1):
            k1, k2 = self.finn_kant_punkt(loype[i], loype[i+1], radius, radius)
            cv2.line(halo_lag, k1, k2, (255,255,255), 9)
            cv2.line(loype_lag, k1, k2, self.o_farge, 3)

        s_cx, s_cy = loype[0]
        pts = np.array([[s_cx, s_cy-22], [s_cx-20, s_cy+15], [s_cx+20, s_cy+15]], np.int32)
        cv2.polylines(halo_lag, [pts], True, (255,255,255), 10)
        cv2.polylines(loype_lag, [pts], True, self.o_farge, 4)

        poster = loype[1:-1]
        for idx, p in enumerate(poster):
            cv2.circle(halo_lag, p, radius, (255,255,255), 10)
            cv2.circle(loype_lag, p, radius, self.o_farge, 4)

        maal = loype[-1]
        cv2.circle(halo_lag, maal, radius-5, (255,255,255), 10)
        cv2.circle(halo_lag, maal, radius+5, (255,255,255), 10)
        cv2.circle(loype_lag, maal, radius-5, self.o_farge, 4)
        cv2.circle(loype_lag, maal, radius+5, self.o_farge, 4)

        # Smelter den hvite haloen inn i kartet
        mask_halo = cv2.cvtColor(halo_lag, cv2.COLOR_BGR2GRAY)
        self.bilde[mask_halo > 0] = halo_lag[mask_halo > 0]

        # Sørger for at lilla ikke dekker over svarte steiner/skrenter
        hsv = cv2.cvtColor(self.bilde, cv2.COLOR_BGR2HSV)
        mask_mork = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 90]))
        halo_kernel = np.ones((4,4), np.uint8)
        mask_klipp = cv2.dilate(mask_mork, halo_kernel, iterations=1)
        loype_lag[mask_klipp > 0] = [0, 0, 0]

        # Legger på selve løypa
        mask_ferdig = cv2.cvtColor(loype_lag, cv2.COLOR_BGR2GRAY)
        self.bilde[mask_ferdig > 0] = loype_lag[mask_ferdig > 0]

        self.start_tekst_lag()
        for idx, p in enumerate(poster):
            kode_tekst = f"{idx+1}-{koder[idx]}"
            self.tegn_tekst(kode_tekst, (p[0]+25, p[1]-15), 0.9, self.o_farge, tykkelse=2, halo=True)
        self.bruk_tekst_lag()

    # --- IOF SYMBOLER ---
    def tegn_iof_stein(self, img, x, y, sc=1.0):
        s = int(8 * sc)
        pts = np.array([[x, y-s], [x-s, y+s], [x+s, y+s]], np.int32)
        cv2.fillPoly(img, [pts], (0,0,0))

    def tegn_iof_skrent(self, img, x, y, sc=1.0):
        s10 = int(10*sc); s5 = int(5*sc); s8 = int(8*sc)
        th3 = max(1, int(3*sc)); th2 = max(1, int(2*sc))
        cv2.line(img, (x-s10, y-s5), (x+s10, y-s5), (0,0,0), th3)
        cv2.line(img, (x-s8, y-s5), (x-s8, y+s5), (0,0,0), th2)
        cv2.line(img, (x, y-s5), (x, y+s5), (0,0,0), th2)
        cv2.line(img, (x+s8, y-s5), (x+s8, y+s5), (0,0,0), th2)

    def tegn_iof_grop(self, img, x, y, sc=1.0):
        s6 = int(6*sc); th = max(1, int(3*sc))
        cv2.line(img, (x-s6, y-s6), (x, y+s6), (0, 75, 150), th)
        cv2.line(img, (x+s6, y-s6), (x, y+s6), (0, 75, 150), th)

    def tegn_iof_vannhull(self, img, x, y, sc=1.0):
        cv2.circle(img, (x, y), max(2, int(6*sc)), (255, 0, 0), -1)

    def tegn_iof_kryss(self, img, x, y, er_y=False, sc=1.0):
        s8 = int(8*sc); s6 = int(6*sc); th = max(1, int(2*sc))
        if er_y:
            cv2.line(img, (x, y), (x, y+s8), (0,0,0), th)
            cv2.line(img, (x, y), (x-s6, y-s6), (0,0,0), th)
            cv2.line(img, (x, y), (x+s6, y-s6), (0,0,0), th)
        else:
            cv2.line(img, (x-s8, y), (x+s8, y), (0,0,0), th)
            cv2.line(img, (x, y-s8), (x, y+s8), (0,0,0), th)

    def tegn_iof_bygning(self, img, x, y, sc=1.0):
        s = int(6 * sc)
        pts = np.array([[x-s, y-s], [x-s, y+s], [x+s, y+s], [x+s, y-s]], np.int32)
        cv2.fillPoly(img, [pts], (0,0,0))

    def tegn_iof_kolle(self, img, x, y, sc=1.0):
        cv2.circle(img, (x, y), max(2, int(4*sc)), (0, 75, 150), -1)

    def tegn_iof_taarn(self, img, x, y, sc=1.0):
        cv2.circle(img, (x, y), max(3, int(6*sc)), (0,0,0), max(1, int(2*sc)))

    def tegn_iof_kunstig(self, img, x, y, sc=1.0):
        s = int(5*sc); th = max(1, int(2*sc))
        cv2.line(img, (x-s, y-s), (x+s, y+s), (0,0,0), th)
        cv2.line(img, (x-s, y+s), (x+s, y-s), (0,0,0), th)

    def tegn_iof_tre(self, img, x, y, sc=1.0):
        s = int(5*sc); th = max(1, int(2*sc))
        pts = np.array([[x, y-s], [x-s, y+s-2], [x+s, y+s-2]], np.int32)
        cv2.polylines(img, [pts], True, (0,0,0), th)
        cv2.line(img, (x, y+s-2), (x, y+s+2), (0,0,0), th)

    def tegn_iof_retning(self, img, x, y, ret_id, sc=1.0):
        dx, dy = 0, 0
        s10 = int(10*sc)
        if "N" in ret_id: dy -= s10
        if "S" in ret_id: dy += s10
        if "E" in ret_id: dx += s10
        if "W" in ret_id: dx -= s10
        if dx != 0 or dy != 0:
            cv2.arrowedLine(img, (x-dx, y-dy), (x+dx, y+dy), (0,0,0), max(1, int(2*sc)), tipLength=0.4)

    def tegn_iof_fot(self, img, x, y, sc=1.0):
        s8 = int(8*sc); s4 = int(4*sc); s2 = int(2*sc)
        cv2.line(img, (x-s8, y+s4), (x+s8, y+s4), (0,0,0), max(1, int(2*sc)))
        cv2.circle(img, (x, y-s2), max(1, s2), (0,0,0), -1)

    def tegn_iof_ovre_kant(self, img, x, y, sc=1.0):
        s8 = int(8*sc); s4 = int(4*sc); s2 = int(2*sc)
        cv2.line(img, (x-s8, y-s4), (x+s8, y-s4), (0,0,0), max(1, int(2*sc)))
        cv2.circle(img, (x, y+s2), max(1, s2), (0,0,0), -1)

    def tegn_postbeskrivelse(self, loype, koder, detalj_typer, lengde_km, stigning_m):
        t = self.T.get(self.spraak, self.T["NO"])
        h, w = self.bilde.shape[:2]
        
        celle_w_base, celle_h_base = 45, 45 
        rader = len(loype) 
        boks_w_base = celle_w_base * 4 + 160 
        boks_h_base = rader * celle_h_base

        cx = sum(p[0] for p in loype) / len(loype)
        cy = sum(p[1] for p in loype) / len(loype)

        marg = 40
        hjorner = {
            "Top-Left": (marg, 80),
            "Top-Right": (w - boks_w_base - marg, 80),
            "Bottom-Left": (marg, h - boks_h_base - marg),
            "Bottom-Right": (w - boks_w_base - marg, h - boks_h_base - marg)
        }

        start_x, start_y = hjorner["Top-Left"]
        max_dist = 0
        for _, (hx, hy) in hjorner.items():
            dist = math.hypot((hx + boks_w_base/2) - cx, (hy + boks_h_base/2) - cy)
            if dist > max_dist:
                max_dist = dist
                start_x, start_y = int(hx), int(hy)

        min_avstand = float('inf')
        for p in loype:
            dx = max(start_x - p[0], 0, p[0] - (start_x + boks_w_base))
            dy = max(start_y - p[1], 0, p[1] - (start_y + boks_h_base))
            min_avstand = min(min_avstand, math.hypot(dx, dy))

        skala = 1.0
        if min_avstand < 80: skala = 0.65 

        celle_w = int(celle_w_base * skala)
        celle_h = int(celle_h_base * skala)
        boks_w = celle_w * 4 + int(160 * skala)
        boks_h = rader * celle_h
        font_skala = 0.7 * skala
        font_liten = 0.5 * skala

        cv2.rectangle(self.bilde, (start_x, start_y), (start_x + boks_w, start_y + boks_h), (255, 255, 255), -1)
        
        for r in range(rader + 1):
            cv2.line(self.bilde, (start_x, start_y + r*celle_h), (start_x + boks_w, start_y + r*celle_h), self.o_farge, max(1, int(2*skala)))
        kolonne_delelinjer = [0, celle_w, celle_w*2, celle_w*3, celle_w*4, boks_w]
        for k_x in kolonne_delelinjer:
            cv2.line(self.bilde, (start_x + k_x, start_y), (start_x + k_x, start_y + boks_h), self.o_farge, max(1, int(2*skala)))

        self.start_tekst_lag()
        overskrift = f"{t['len']}: {lengde_km:.2f} km | {t['climb']}: {int(stigning_m)} m"
        self.tegn_tekst(overskrift, (start_x, start_y - int(10*skala)), 0.8 * skala, self.o_farge, 2)

        for i, punkt in enumerate(loype):
            y_senter = start_y + i * celle_h + int(celle_h/2)
            
            nr_str = t['s'] if i == 0 else t['m'] if i == len(loype)-1 else str(i)
            self.tegn_tekst(nr_str, (start_x + int(15*skala), y_senter + int(8*skala)), font_skala, (0,0,0), 2)

            if 0 < i < len(loype) - 1:
                if (i-1) < len(koder):
                    kode = str(koder[i-1])
                    self.tegn_tekst(kode, (start_x + celle_w + int(5*skala), y_senter + int(8*skala)), font_skala * 0.9, (0,0,0), 2)

                info = detalj_typer.get(punkt, {"sym": "", "ret": "", "tekst": ""})
                tekst = info["tekst"]
                
                beskrivelse = tekst.split(",")[1].strip() if "," in tekst else tekst
                self.tegn_tekst(beskrivelse, (start_x + celle_w * 4 + int(10*skala), y_senter + int(6*skala)), font_liten, (0,0,0), 1)

        self.bruk_tekst_lag()
        
        for i, punkt in enumerate(loype):
            if 0 < i < len(loype) - 1:
                y_senter = start_y + i * celle_h + int(celle_h/2)
                info = detalj_typer.get(punkt, {"sym": "", "ret": "", "tekst": ""})
                sym, ret = info["sym"], info["ret"]
                
                x_sym3 = start_x + celle_w * 2 + int(celle_w/2)
                if sym == "stein": self.tegn_iof_stein(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "skrent": self.tegn_iof_skrent(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "grop": self.tegn_iof_grop(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "kolle": self.tegn_iof_kolle(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "bygning": self.tegn_iof_bygning(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "vann": self.tegn_iof_vannhull(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "y": self.tegn_iof_kryss(self.bilde, x_sym3, y_senter, er_y=True, sc=skala)
                elif sym == "kryss": self.tegn_iof_kryss(self.bilde, x_sym3, y_senter, er_y=False, sc=skala)
                elif sym == "taarn": self.tegn_iof_taarn(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "kunstig": self.tegn_iof_kunstig(self.bilde, x_sym3, y_senter, sc=skala)
                elif sym == "tre": self.tegn_iof_tre(self.bilde, x_sym3, y_senter, sc=skala)

                x_sym4 = start_x + celle_w * 3 + int(celle_w/2)
                if ret == "fot": self.tegn_iof_fot(self.bilde, x_sym4, y_senter, sc=skala)
                elif ret == "ovre": self.tegn_iof_ovre_kant(self.bilde, x_sym4, y_senter, sc=skala)
                elif ret in ["N", "S", "E", "W", "NW", "NE", "SW", "SE"]:
                    self.tegn_iof_retning(self.bilde, x_sym4, y_senter, ret, sc=skala)

    # --- NYTT: Legg til Passepartout (Ramme og Tittel) ---
    def fullfoer_design(self, tittel, undertekst):
        h, w = self.bilde.shape[:2]
        marg_topp = 120
        marg_bunn = 60
        marg_side = 60
        
        # Lag et hvitt lerret som er litt større enn kartet
        lerret = np.full((h + marg_topp + marg_bunn, w + marg_side*2, 3), 255, dtype=np.uint8)
        # Lim inn kartet i midten
        lerret[marg_topp:marg_topp+h, marg_side:marg_side+w] = self.bilde
        
        # Tegn en stilig svart ramme rundt selve kartbildet
        cv2.rectangle(lerret, (marg_side, marg_topp), (marg_side+w, marg_topp+h), (0,0,0), 3)
        self.bilde = lerret
        
        # Bruk PIL for å skrive stilig overskrift
        self.start_tekst_lag()
        self.tegn_tekst(tittel, (marg_side, int(marg_topp * 0.45)), 1.5, (0,0,0), tykkelse=3)
        self.tegn_tekst(undertekst, (marg_side, int(marg_topp * 0.8)), 0.6, (100,100,100), tykkelse=1)
        self.bruk_tekst_lag()

    # --- NYTT: PDF Eksport ---
    def lagre_som_pdf(self, filnavn):
        img_rgb = cv2.cvtColor(self.bilde, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        # Lagrer som PDF i høy oppløsning!
        pil_img.save(filnavn, "PDF", resolution=300.0)
