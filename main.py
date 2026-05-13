import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import cv2 
import numpy as np
import os
import math
from map_analyzer import MapAnalyzer
from course_generator import CourseGenerator
from renderer import MapRenderer
from elevation_data import ElevationManager







def les_bilde_norsk(kart_fil):
    try:
        with open(kart_fil, "rb") as f: chunk = f.read()
        return cv2.imdecode(np.frombuffer(chunk, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    except Exception as e:
        print(f"Feil: {e}")
        return None

class LoeypeMeny:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Loeypelegger")
        self.root.geometry("450x700")
        # Removed topmost true to fix Alt+Tab functionality!
        self.resultat = None

        self.T = {
            "NO": {
                "cfg": "KONFIGURASJON", "file": "Kartfil:", "nofile": "Ingen fil valgt...", 
                "btnfile": "Velg Kart-bilde", "fmt": "Loepsformat:", "cls": "Klasse:", 
                "eq": "Ekvidistanse (m):", "btnstart": "NESTE: VELG OMRAADE", "lang": "Spraak:",
                "adv": "Avansert: Bruk nøyaktig høydemodell (DEM)", "btndem": "Velg DEM (GeoTIFF)",
                "g_tittel": "Slik skaffer du høydedata",
                "g_tekst": "1. Gå til hoydedata.no\n2. Zoom inn til kartet ditt og bruk markeringsverktøyet.\n3. Pass på at boksen du tegner dekker AKKURAT samme utsnitt som kartbildet ditt!\n4. Last ned produktet 'DTM' i formatet '.tif' (GeoTIFF)."
            }
        }
        for l in ["EN", "SV", "DE"]: self.T[l] = self.T["NO"]

        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.lbl_cfg = ttk.Label(main_frame, text=self.T["NO"]["cfg"], font=("Segoe UI", 14, "bold"))
        self.lbl_cfg.pack(pady=10)

        self.lbl_file = ttk.Label(main_frame, text=self.T["NO"]["file"])
        self.lbl_file.pack(anchor=tk.W, pady=(10,0))
        self.fil_var = tk.StringVar(value=self.T["NO"]["nofile"])
        ttk.Entry(main_frame, textvariable=self.fil_var, state='readonly').pack(fill=tk.X, pady=5)
        self.btn_file = ttk.Button(main_frame, text=self.T["NO"]["btnfile"], command=self.velg_fil)
        self.btn_file.pack(fill=tk.X, pady=2)

        self.bruk_dem_var = tk.BooleanVar(value=False)
        self.cb_adv = ttk.Checkbutton(main_frame, text=self.T["NO"]["adv"], variable=self.bruk_dem_var, command=self.toggle_dem)
        self.cb_adv.pack(anchor=tk.W, pady=(15, 0))

        self.dem_frame = ttk.Frame(main_frame)
        self.dem_var = tk.StringVar(value=self.T["NO"]["nofile"])
        ttk.Entry(self.dem_frame, textvariable=self.dem_var, state='readonly').pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(self.dem_frame)
        btn_frame.pack(fill=tk.X)
        self.btn_dem = ttk.Button(btn_frame, text=self.T["NO"]["btndem"], command=self.velg_dem)
        self.btn_dem.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.btn_guide = ttk.Button(btn_frame, text="?", width=3, command=self.vis_guide)
        self.btn_guide.pack(side=tk.RIGHT)

        self.lbl_fmt = ttk.Label(main_frame, text=self.T["NO"]["fmt"])
        self.lbl_fmt.pack(anchor=tk.W, pady=(15,0))
        self.format_var = tk.StringVar(value="MELLOM")
        ttk.Combobox(main_frame, textvariable=self.format_var, values=["SPRINT", "MELLOM", "LANG"], state="readonly").pack(fill=tk.X, pady=5)

        self.lbl_cls = ttk.Label(main_frame, text=self.T["NO"]["cls"])
        self.lbl_cls.pack(anchor=tk.W, pady=(10,0))
        self.klasse_var = tk.StringVar(value="A-KORT")
        ttk.Combobox(main_frame, textvariable=self.klasse_var, values=["NYBEGYNNER", "C-LETT", "A-KORT", "A-LANG"], state="readonly").pack(fill=tk.X, pady=5)

        self.lbl_eq = ttk.Label(main_frame, text=self.T["NO"]["eq"])
        self.lbl_eq.pack(anchor=tk.W, pady=(10,0))
        self.ekvi_var = tk.DoubleVar(value=5.0)
        tk.Scale(main_frame, from_=2.0, to=10.0, variable=self.ekvi_var, orient=tk.HORIZONTAL, resolution=0.5).pack(fill=tk.X)

        self.btn_start = ttk.Button(main_frame, text=self.T["NO"]["btnstart"], command=self.bekreft)
        self.btn_start.pack(fill=tk.X, pady=25)

    def toggle_dem(self):
        if self.bruk_dem_var.get():
            self.dem_frame.pack(fill=tk.X, after=self.cb_adv)
        else:
            self.dem_frame.pack_forget()

    def vis_guide(self):
        messagebox.showinfo(self.T["NO"]["g_tittel"], self.T["NO"]["g_tekst"])

    def velg_fil(self):
        fil = filedialog.askopenfilename(filetypes=[("Bilde-filer", "*.png *.jpg *.jpeg")])
        if fil: self.fil_var.set(fil)

    def velg_dem(self):
        fil = filedialog.askopenfilename(filetypes=[("Høydedata", "*.png *.jpg *.tif *.tiff")])
        if fil: self.dem_var.set(fil)

    def bekreft(self):
        if not os.path.exists(self.fil_var.get()): return
        dem_sti = self.dem_var.get()
        if not self.bruk_dem_var.get() or not os.path.exists(dem_sti):
            dem_sti = None
        self.resultat = {
            "fil": self.fil_var.get(),
            "dem_fil": dem_sti,
            "format": self.format_var.get(),
            "klasse": self.klasse_var.get(),
            "ekvidistanse": self.ekvi_var.get(),
            "spraak": "NO"
        }
        self.root.quit()

    def kjor(self):
        self.root.mainloop()
        self.root.destroy()
        return self.resultat

class KartUI:
    def __init__(self, bilde, modus, spraak="NO", tittel="Kart", loype=None, blokk_maske=None):
        self.bilde = bilde
        self.modus = modus 
        self.spraak = spraak
        self.loype = loype if loype else []
        
        self.h, self.w = bilde.shape[:2]
        self.skala = min(1200 / self.w, 800 / self.h) 
        self.x_offset = int((1200 - self.w * self.skala) / 2)
        self.y_offset = int((800 - self.h * self.skala) / 2)
        self.drar_kart = False
        self.mus_x, self.mus_y = 0, 0
        self.vindu = tittel
        self.punkter = [] # For OMRAADE og PUNKTER
        
        # Tools
        self.valgt_post_indeks = -1
        self.drar_post = False
        self.hover_kx, self.hover_ky = 0, 0 
        
        # Blocking tool
        self.blokk_maske = blokk_maske if blokk_maske is not None else np.zeros((self.h, self.w), dtype=np.uint8)
        self.drar_pensel = False
        self.pensel_str = max(5, int(20 / self.skala))

        # Undo / Redo History
        self.historikk = []
        self.historikk_idx = -1
        if self.modus == "REDIGER" and self.loype:
            self.lagre_historikk()

        self.T = {
            "NO": {
                "t1_1": "TRINN 1: Klikk rundt for aa tegne polygon. Trykk ENTER.", 
                "t_blokk1": "TRINN 2: Mal roedt (hold venstreklikk) for aa blokkere veier/vann.",
                "t_blokk2": "Trykk ENTER for aa bekrefte blokkeringen.",
                "t2": "TRINN 3: Klikk for Start og Maal. Trykk ENTER.",
                "t3_1": "TRINN 4: Dra poster for aa flytte. 'A' for aa legge til, 'D' for aa slette.",
                "t3_2": "Trykk 'Z' for Angre (Undo) og 'Y' for Gjenopprett (Redo).",
                "t3_3": "Trykk ENTER for aa lagre PDF!"
            },
        }

        cv2.namedWindow(self.vindu, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.vindu, 1200, 800)
        cv2.setMouseCallback(self.vindu, self.mus_hendelse)
        # Removed WND_PROP_TOPMOST so you can Alt+Tab!

    def lagre_historikk(self):
        # Truncate future history if we alter the timeline
        self.historikk = self.historikk[:self.historikk_idx + 1]
        self.historikk.append(self.loype.copy())
        self.historikk_idx += 1

    def skisser_tekst(self, img, tekst, pos, farge=(0, 255, 0)):
        # Replaces the ugly white box with a sleek drop shadow text
        cv2.putText(img, tekst, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
        cv2.putText(img, tekst, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, farge, 2)

    def mus_hendelse(self, event, x, y, flags, param):
        kx, ky = (x - self.x_offset) / self.skala, (y - self.y_offset) / self.skala
        kx = max(0, min(kx, self.w - 1))
        ky = max(0, min(ky, self.h - 1))
        self.hover_kx, self.hover_ky = kx, ky 

        if event == cv2.EVENT_LBUTTONDOWN:
            if self.modus == "OMRAADE":
                self.punkter.append((int(kx), int(ky)))
            elif self.modus == "PUNKTER":
                if len(self.punkter) < 2: self.punkter.append((int(kx), int(ky)))
            elif self.modus == "BLOKKER":
                self.drar_pensel = True
                cv2.circle(self.blokk_maske, (int(kx), int(ky)), self.pensel_str, 255, -1)
            elif self.modus == "REDIGER":
                min_dist = float('inf')
                for i, p in enumerate(self.loype):
                    dist = math.hypot(kx - p[0], ky - p[1])
                    if dist < 25 / self.skala: 
                        if dist < min_dist:
                            min_dist = dist
                            self.valgt_post_indeks = i
                if self.valgt_post_indeks != -1:
                    self.drar_post = True

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.modus == "BLOKKER" and self.drar_pensel:
                cv2.circle(self.blokk_maske, (int(kx), int(ky)), self.pensel_str, 255, -1)
            elif self.drar_post and self.valgt_post_indeks != -1:
                self.loype[self.valgt_post_indeks] = (int(kx), int(ky))
                
            if self.drar_kart:
                self.x_offset += (x - self.mus_x); self.y_offset += (y - self.mus_y)
                self.mus_x, self.mus_y = x, y
            self.oppdater_skjerm()

        elif event == cv2.EVENT_LBUTTONUP: 
            if self.modus == "BLOKKER": self.drar_pensel = False
            if self.drar_post:
                self.drar_post = False
                self.valgt_post_indeks = -1
                self.lagre_historikk() # Save state after moving point
                
        elif event == cv2.EVENT_RBUTTONDOWN: self.drar_kart = True; self.mus_x, self.mus_y = x, y
        elif event == cv2.EVENT_RBUTTONUP: self.drar_kart = False
        elif event == cv2.EVENT_MOUSEWHEEL: self.zoom(1.1 if flags > 0 else 0.9, x, y)

    def zoom(self, f, x, y):
        kx, ky = (x - self.x_offset) / self.skala, (y - self.y_offset) / self.skala
        self.skala *= f
        self.x_offset, self.y_offset = int(x - kx * self.skala), int(y - ky * self.skala)
        self.pensel_str = max(5, int(20 / self.skala))
        self.oppdater_skjerm()

    def oppdater_skjerm(self):
        temp_bilde = self.bilde.copy()

        # Render tools overlay
        if self.modus == "OMRAADE" and len(self.punkter) > 0:
            for i in range(len(self.punkter) - 1):
                cv2.line(temp_bilde, self.punkter[i], self.punkter[i+1], (0, 0, 255), 3)
            # Preview line to mouse
            cv2.line(temp_bilde, self.punkter[-1], (int(self.hover_kx), int(self.hover_ky)), (0, 150, 255), 2)
            cv2.circle(temp_bilde, self.punkter[0], 8, (0, 255, 0), -1)

        elif self.modus == "BLOKKER":
            # Show red overlay where user painted
            red_overlay = np.zeros_like(temp_bilde)
            red_overlay[:,:] = (0, 0, 255)
            mask_idx = self.blokk_maske > 0
            temp_bilde[mask_idx] = cv2.addWeighted(temp_bilde[mask_idx], 0.4, red_overlay[mask_idx], 0.6, 0)
            # Draw brush cursor
            cv2.circle(temp_bilde, (int(self.hover_kx), int(self.hover_ky)), self.pensel_str, (0,0,255), 2)

        elif self.modus == "PUNKTER":
            for p in self.punkter:
                cv2.circle(temp_bilde, p, 12, (143, 0, 200), -1)

        elif self.modus == "REDIGER" and len(self.loype) > 0:
            o_farge = (143, 0, 200)
            for i in range(len(self.loype) - 1):
                cv2.line(temp_bilde, self.loype[i], self.loype[i+1], o_farge, 3)
            s_cx, s_cy = self.loype[0]
            pts = np.array([[s_cx, s_cy-22], [s_cx-20, s_cy+15], [s_cx+20, s_cy+15]], np.int32)
            cv2.polylines(temp_bilde, [pts], True, o_farge, 4)
            for p in self.loype[1:-1]:
                cv2.circle(temp_bilde, p, 20, o_farge, 4)
            maal = self.loype[-1]
            cv2.circle(temp_bilde, maal, 15, o_farge, 4)
            cv2.circle(temp_bilde, maal, 25, o_farge, 4)

        M = np.float32([[self.skala, 0, self.x_offset], [0, self.skala, self.y_offset]])
        visning = cv2.warpAffine(temp_bilde, M, (1200, 800), flags=cv2.INTER_LINEAR)
        t = self.T["NO"]
        
        # Draw sleek shadowed text (Removed white box!)
        if self.modus == "OMRAADE":
            self.skisser_tekst(visning, t["t1_1"], (20, 40), (200, 200, 200))
        elif self.modus == "BLOKKER":
            self.skisser_tekst(visning, t["t_blokk1"], (20, 40), (0, 0, 255))
            self.skisser_tekst(visning, t["t_blokk2"], (20, 70), (0, 255, 0))
        elif self.modus == "PUNKTER":
            self.skisser_tekst(visning, t["t2"], (20, 40), (143, 0, 200))
        elif self.modus == "REDIGER":
            self.skisser_tekst(visning, t["t3_1"], (20, 30), (200, 200, 200))
            self.skisser_tekst(visning, t["t3_2"], (20, 60), (0, 255, 255))
            self.skisser_tekst(visning, t["t3_3"], (20, 90), (0, 255, 0))

        cv2.imshow(self.vindu, visning)

    def kjor(self):
        self.oppdater_skjerm()
        res = None
        while True:
            k = cv2.waitKey(20) & 0xFF
            if k == 13: # ENTER
                if self.modus == "OMRAADE" and len(self.punkter) >= 3:
                    res = self.punkter; break
                elif self.modus == "BLOKKER":
                    res = self.blokk_maske; break
                elif self.modus == "PUNKTER" and len(self.punkter) == 2:
                    res = self.punkter; break
                elif self.modus == "REDIGER":
                    res = self.loype; break
                    
            elif k in [ord('a'), ord('A')] and self.modus == "REDIGER":
                if len(self.loype) >= 2:
                    best_index, min_added = 1, float('inf')
                    hx, hy = self.hover_kx, self.hover_ky
                    for i in range(len(self.loype) - 1):
                        p1, p2 = self.loype[i], self.loype[i+1]
                        old_dist = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
                        new_dist = math.hypot(hx-p1[0], hy-p1[1]) + math.hypot(p2[0]-hx, p2[1]-hy)
                        if new_dist - old_dist < min_added:
                            min_added = new_dist - old_dist
                            best_index = i + 1
                    self.loype.insert(best_index, (int(hx), int(hy)))
                    self.lagre_historikk() # UNDO save
                    self.oppdater_skjerm()
                    
            elif k in [ord('d'), ord('D')] and self.modus == "REDIGER":
                for i in range(1, len(self.loype) - 1):
                    if math.hypot(self.hover_kx - self.loype[i][0], self.hover_ky - self.loype[i][1]) < 25 / self.skala:
                        self.loype.pop(i)
                        self.lagre_historikk() # UNDO save
                        self.oppdater_skjerm()
                        break
            
            # --- NYTT: UNDO (Z) & REDO (Y) ---
            elif k in [ord('z'), ord('Z'), 26] and self.modus == "REDIGER":
                if self.historikk_idx > 0:
                    self.historikk_idx -= 1
                    self.loype = self.historikk[self.historikk_idx].copy()
                    self.oppdater_skjerm()
            elif k in [ord('y'), ord('Y'), 25] and self.modus == "REDIGER":
                if self.historikk_idx < len(self.historikk) - 1:
                    self.historikk_idx += 1
                    self.loype = self.historikk[self.historikk_idx].copy()
                    self.oppdater_skjerm()
                        
            elif k == 27: break # ESC
        cv2.destroyWindow(self.vindu)
        return res

def main():
    meny = LoeypeMeny()
    config = meny.kjor()
    if not config: return

    fullt_bilde = les_bilde_norsk(config["fil"])
    if fullt_bilde is None: return

    # --- STEP 1: POLYGON SELECTION ---
    omrade_ui = KartUI(fullt_bilde, modus="OMRAADE", spraak=config["spraak"])
    polygon = omrade_ui.kjor()
    if not polygon or len(polygon) < 3: return

    x_coords = [p[0] for p in polygon]
    y_coords = [p[1] for p in polygon]
    x1, y1 = max(0, min(x_coords)), max(0, min(y_coords))
    x2, y2 = min(fullt_bilde.shape[1], max(x_coords)), min(fullt_bilde.shape[0], max(y_coords))

    beskjaert = fullt_bilde[y1:y2, x1:x2].copy()
    kart_hoyde, kart_bredde = beskjaert.shape[:2]

    # Create a mask covering everything OUTSIDE the user's polygon
    poly_mask = np.zeros((kart_hoyde, kart_bredde), dtype=np.uint8)
    shifted_poly = np.array([[(p[0]-x1, p[1]-y1) for p in polygon]], dtype=np.int32)
    cv2.fillPoly(poly_mask, shifted_poly, 255)
    
    # Visually fade out the outside to look cool
    beskjaert[poly_mask == 0] = cv2.addWeighted(beskjaert, 0.4, np.full_like(beskjaert, 255), 0.6, 0)[poly_mask == 0]

    # We tell the AI that outside is "blocked"
    blokk_maske_global = np.full((kart_hoyde, kart_bredde), 255, dtype=np.uint8)
    cv2.fillPoly(blokk_maske_global, shifted_poly, 0)

    # --- STEP 2: PAINT BLOCKER TOOL ---
    print("\n[Trinn 2] Åpner blokkeringsverktøy...")
    blokk_ui = KartUI(beskjaert.copy(), modus="BLOKKER", spraak=config["spraak"], blokk_maske=blokk_maske_global)
    oppdatert_blokk_maske = blokk_ui.kjor()
    if oppdatert_blokk_maske is None: return

    hoyde_modell = None
    if config["dem_fil"]:
        print(f"[{config['spraak']}] Laster digital høydemodell (DEM)...")
        hoyde_modell = ElevationManager(config["dem_fil"], kart_bredde, kart_hoyde, min_hoyde=0, maks_hoyde=500)

    print(f"[{config['spraak']}] Analyserer...")
    analyzer = MapAnalyzer(beskjaert, spraak=config["spraak"], blokk_maske=oppdatert_blokk_maske)
    
    # --- STEP 3: START AND FINISH ---
    punkt_ui = KartUI(analyzer.bilde, modus="PUNKTER", spraak=config["spraak"])
    valgte = punkt_ui.kjor()
    if not valgte: return
    
    print(f"[{config['spraak']}] AI designer grunnloeypa...")
    MAALESTOKK = 4000 if config["format"] == "SPRINT" else 5000
    ANTALL = 12 if config["klasse"] == "A-LANG" else 8 if config["klasse"] == "A-KORT" else 5
    generator = CourseGenerator(MAALESTOKK, 300)
    loype = generator.generer_perfekt_loype(analyzer.lovlige_detaljer, analyzer.avstand_til_sti, analyzer.cost_map, config["klasse"], config["format"], ANTALL, valgte[0], valgte[1])
    
    if loype:
        print("\n[Trinn 4] Åpner redigeringsmodus.")
        edit_ui = KartUI(analyzer.bilde.copy(), modus="REDIGER", spraak=config["spraak"], loype=loype.copy())
        redigert_loype = edit_ui.kjor()
        
        if not redigert_loype:
            print("Avbrutt av bruker under redigering.")
            return
            
        loype = redigert_loype
        postkoder = generator.generer_postkoder(len(loype) - 2)
        lengde = generator.beregn_loypelengde(loype)
        
        if hoyde_modell is not None:
            stigning = 0
            for i in range(len(loype) - 1):
                stigning += hoyde_modell.beregn_stigning_mellom_punkter(loype[i], loype[i+1])
        else:
            stigning = generator.beregn_stigning(loype, analyzer.mask_kurver, ekvidistanse=config["ekvidistanse"])
        
        renderer = MapRenderer(analyzer.bilde, spraak=config["spraak"])
        renderer.tegn_loype(loype, koder=postkoder, cost_map=analyzer.cost_map)
        renderer.tegn_postbeskrivelse(loype, postkoder, analyzer.detalj_typer, lengde/1000, stigning)
        
        tittel = f"Orienteringsloeypa - {config['klasse']} ({config['format']})"
        undertekst = "Generert av AI Loeypelegger | Finn postene i terrenget!"
        renderer.fullfoer_design(tittel, undertekst)
        
        pdf_fn = f"loeype_{config['spraak']}_{config['format']}.pdf"
        renderer.lagre_som_pdf(pdf_fn)
        print(f"\n[SUKSESS] Ferdig! Lagret som {pdf_fn}")
        os.startfile(pdf_fn) if hasattr(os, 'startfile') else None
    
    else:
        print("\n[FEIL] AI-en klarte ikke å finne en løype som fulgte IOF-kravene!")
        print("Sørg for at boksen din inneholder minst et par tydelige kartdetaljer.")

if __name__ == "__main__":
    main()
