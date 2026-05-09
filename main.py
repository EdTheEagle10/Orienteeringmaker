import tkinter as tk
from tkinter import filedialog, ttk
import cv2 
import numpy as np
import os
from map_analyzer import MapAnalyzer
from course_generator import CourseGenerator
from renderer import MapRenderer

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
        self.root.geometry("400x600")
        self.root.attributes('-topmost', True)
        self.resultat = None

        # Meny-oversettelser
        self.T = {
            "NO": {"cfg": "KONFIGURASJON", "file": "Kartfil:", "nofile": "Ingen fil valgt...", "btnfile": "Velg Kart-bilde", "fmt": "Loepsformat:", "cls": "Klasse:", "eq": "Ekvidistanse (m):", "btnstart": "NESTE: VELG OMRAADE", "lang": "Spraak:"},
            "EN": {"cfg": "CONFIGURATION", "file": "Map file:", "nofile": "No file selected...", "btnfile": "Select Map Image", "fmt": "Event Format:", "cls": "Class:", "eq": "Contour Interval (m):", "btnstart": "NEXT: SELECT AREA", "lang": "Language:"},
            "SV": {"cfg": "KONFIGURATION", "file": "Kartfil:", "nofile": "Ingen fil vald...", "btnfile": "Välj kartbild", "fmt": "Tävlingsformat:", "cls": "Klass:", "eq": "Ekvidistans (m):", "btnstart": "NÄSTA: VÄLJ OMRÅDE", "lang": "Språk:"},
            "DE": {"cfg": "KONFIGURATION", "file": "Kartendatei:", "nofile": "Keine Datei ausgewählt...", "btnfile": "Kartenbild wählen", "fmt": "Wettkampfformat:", "cls": "Kategorie:", "eq": "Äquidistanz (m):", "btnstart": "WEITER: BEREICH WÄHLEN", "lang": "Sprache:"}
        }

        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.lbl_cfg = ttk.Label(main_frame, text=self.T["NO"]["cfg"], font=("Segoe UI", 14, "bold"))
        self.lbl_cfg.pack(pady=10)

        self.lbl_lang = ttk.Label(main_frame, text=self.T["NO"]["lang"])
        self.lbl_lang.pack(anchor=tk.W)
        self.lang_var = tk.StringVar(value="NO")
        lang_cb = ttk.Combobox(main_frame, textvariable=self.lang_var, values=["NO", "EN", "SV", "DE"], state="readonly")
        lang_cb.pack(fill=tk.X, pady=5)
        lang_cb.bind("<<ComboboxSelected>>", self.oppdater_tekster)

        self.lbl_file = ttk.Label(main_frame, text=self.T["NO"]["file"])
        self.lbl_file.pack(anchor=tk.W, pady=(10,0))
        self.fil_var = tk.StringVar(value=self.T["NO"]["nofile"])
        ttk.Entry(main_frame, textvariable=self.fil_var, state='readonly').pack(fill=tk.X, pady=5)
        self.btn_file = ttk.Button(main_frame, text=self.T["NO"]["btnfile"], command=self.velg_fil)
        self.btn_file.pack(fill=tk.X, pady=5)

        self.lbl_fmt = ttk.Label(main_frame, text=self.T["NO"]["fmt"])
        self.lbl_fmt.pack(anchor=tk.W, pady=(10,0))
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
        self.btn_start.pack(fill=tk.X, pady=30)

    def oppdater_tekster(self, event=None):
        l = self.lang_var.get()
        self.lbl_cfg.config(text=self.T[l]["cfg"])
        self.lbl_lang.config(text=self.T[l]["lang"])
        self.lbl_file.config(text=self.T[l]["file"])
        if "Ingen fil" in self.fil_var.get() or "No file" in self.fil_var.get() or "Keine" in self.fil_var.get():
            self.fil_var.set(self.T[l]["nofile"])
        self.btn_file.config(text=self.T[l]["btnfile"])
        self.lbl_fmt.config(text=self.T[l]["fmt"])
        self.lbl_cls.config(text=self.T[l]["cls"])
        self.lbl_eq.config(text=self.T[l]["eq"])
        self.btn_start.config(text=self.T[l]["btnstart"])

    def velg_fil(self):
        fil = filedialog.askopenfilename(filetypes=[("Bilde-filer", "*.png *.jpg *.jpeg")])
        if fil: self.fil_var.set(fil)

    def bekreft(self):
        if not os.path.exists(self.fil_var.get()): return
        self.resultat = {
            "fil": self.fil_var.get(),
            "format": self.format_var.get(),
            "klasse": self.klasse_var.get(),
            "ekvidistanse": self.ekvi_var.get(),
            "spraak": self.lang_var.get()
        }
        self.root.quit()

    def kjor(self):
        self.root.mainloop()
        self.root.destroy()
        return self.resultat

class KartUI:
    def __init__(self, bilde, modus, spraak="NO", tittel="Kart"):
        self.bilde = bilde
        self.modus = modus 
        self.spraak = spraak
        self.h, self.w = bilde.shape[:2]
        self.skala = min(1200 / self.w, 800 / self.h) 
        self.x_offset = int((1200 - self.w * self.skala) / 2)
        self.y_offset = int((800 - self.h * self.skala) / 2)
        self.drar_kart, self.drar_boks = False, False
        self.mus_x, self.mus_y = 0, 0
        self.vindu = tittel
        self.punkter = []
        self.boks_start, self.boks_slutt = None, None

        self.T = {
            "NO": {"t1_1": "TRINN 1: Hold venstre musknapp og dra en boks.", "t1_2": "Trykk ENTER naar du er ferdig.", "t2": "TRINN 2: Klikk for Start og Maal. Trykk ENTER."},
            "EN": {"t1_1": "STEP 1: Hold left click and drag to select area.", "t1_2": "Press ENTER when finished.", "t2": "STEP 2: Click to set Start and Finish. Press ENTER."},
            "SV": {"t1_1": "STEG 1: Haall vaenster musknapp och dra en ruta.", "t1_2": "Tryck ENTER naer du aer klar.", "t2": "STEG 2: Klicka foer Start och Maal. Tryck ENTER."},
            "DE": {"t1_1": "SCHRITT 1: Linksklick halten und Bereich markieren.", "t1_2": "Zum Bestaetigen ENTER druecken.", "t2": "SCHRITT 2: Klicken fuer Start und Ziel. ENTER druecken."}
        }

        cv2.namedWindow(self.vindu, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.vindu, 1200, 800)
        cv2.setMouseCallback(self.vindu, self.mus_hendelse)
        cv2.setWindowProperty(self.vindu, cv2.WND_PROP_TOPMOST, 1)

    def mus_hendelse(self, event, x, y, flags, param):
        kx, ky = (x - self.x_offset) / self.skala, (y - self.y_offset) / self.skala
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.modus == "PUNKTER":
                if len(self.punkter) < 2: self.punkter.append((int(kx), int(ky)))
            elif self.modus == "OMRAADE":
                self.boks_start = self.boks_slutt = (int(kx), int(ky))
                self.drar_boks = True
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drar_boks: self.boks_slutt = (int(kx), int(ky))
            if self.drar_kart:
                self.x_offset += (x - self.mus_x); self.y_offset += (y - self.mus_y)
                self.mus_x, self.mus_y = x, y
            self.oppdater_skjerm()
        elif event == cv2.EVENT_LBUTTONUP: self.drar_boks = False
        elif event == cv2.EVENT_RBUTTONDOWN: self.drar_kart = True; self.mus_x, self.mus_y = x, y
        elif event == cv2.EVENT_RBUTTONUP: self.drar_kart = False
        elif event == cv2.EVENT_MOUSEWHEEL: self.zoom(1.1 if flags > 0 else 0.9, x, y)

    def zoom(self, f, x, y):
        kx, ky = (x - self.x_offset) / self.skala, (y - self.y_offset) / self.skala
        self.skala *= f
        self.x_offset, self.y_offset = int(x - kx * self.skala), int(y - ky * self.skala)
        self.oppdater_skjerm()

    def oppdater_skjerm(self):
        M = np.float32([[self.skala, 0, self.x_offset], [0, self.skala, self.y_offset]])
        visning = cv2.warpAffine(self.bilde, M, (1200, 800), flags=cv2.INTER_LINEAR)
        cv2.rectangle(visning, (0, 0), (750, 100), (255, 255, 255), -1)
        t = self.T[self.spraak]
        
        if self.modus == "OMRAADE":
            cv2.putText(visning, t["t1_1"], (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1)
            cv2.putText(visning, t["t1_2"], (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,120,0), 2)
            if self.boks_start and self.boks_slutt:
                p1 = (int(self.boks_start[0]*self.skala+self.x_offset), int(self.boks_start[1]*self.skala+self.y_offset))
                p2 = (int(self.boks_slutt[0]*self.skala+self.x_offset), int(self.boks_slutt[1]*self.skala+self.y_offset))
                cv2.rectangle(visning, p1, p2, (0, 0, 255), 3)
        else:
            cv2.putText(visning, t["t2"], (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (143,0,200), 2)
            for p in self.punkter:
                px, py = int(p[0]*self.skala+self.x_offset), int(p[1]*self.skala+self.y_offset)
                cv2.circle(visning, (px, py), 12, (143, 0, 200), -1)

        cv2.imshow(self.vindu, visning)

    def kjor(self):
        self.oppdater_skjerm()
        res = None
        while True:
            k = cv2.waitKey(20) & 0xFF
            if k == 13: 
                if self.modus == "OMRAADE" and self.boks_start:
                    x1, x2 = sorted([self.boks_start[0], self.boks_slutt[0]])
                    y1, y2 = sorted([self.boks_start[1], self.boks_slutt[1]])
                    res = (int(x1), int(y1), int(x2), int(y2)); break
                elif self.modus == "PUNKTER" and len(self.punkter) == 2:
                    res = self.punkter; break
            elif k == 27: break
        cv2.destroyWindow(self.vindu)
        return res

def main():
    meny = LoeypeMeny()
    config = meny.kjor()
    if not config: return

    fullt_bilde = les_bilde_norsk(config["fil"])
    if fullt_bilde is None: return

    omrade_ui = KartUI(fullt_bilde, modus="OMRAADE", spraak=config["spraak"])
    boks = omrade_ui.kjor()
    if not boks: return
    x1, y1, x2, y2 = boks
    beskjaert = fullt_bilde[max(0,y1):min(fullt_bilde.shape[0],y2), max(0,x1):min(fullt_bilde.shape[1],x2)]

    print(f"[{config['spraak']}] Analyserer...")
    analyzer = MapAnalyzer(beskjaert, spraak=config["spraak"])
    punkt_ui = KartUI(analyzer.bilde, modus="PUNKTER", spraak=config["spraak"])
    valgte = punkt_ui.kjor()
    if not valgte: return
    
    print(f"[{config['spraak']}] AI designer loeypa...")
    MAALESTOKK = 4000 if config["format"] == "SPRINT" else 5000
    ANTALL = 12 if config["klasse"] == "A-LANG" else 8 if config["klasse"] == "A-KORT" else 5
    generator = CourseGenerator(MAALESTOKK, 300)
    loype = generator.generer_perfekt_loype(analyzer.lovlige_detaljer, analyzer.avstand_til_sti, analyzer.cost_map, config["klasse"], config["format"], ANTALL, valgte[0], valgte[1])
    
    if loype:
        postkoder = generator.generer_postkoder(len(loype) - 2)
        lengde = generator.beregn_loypelengde(loype)
        stigning = generator.beregn_stigning(loype, analyzer.mask_kurver, ekvidistanse=config["ekvidistanse"])
        
        renderer = MapRenderer(analyzer.bilde, spraak=config["spraak"])
        renderer.tegn_loype(loype, koder=postkoder, cost_map=analyzer.cost_map)
        renderer.tegn_postbeskrivelse(loype, postkoder, analyzer.detalj_typer, lengde/1000, stigning)
        
        fn = f"loeype_{config['spraak']}_{config['format']}.png"
        renderer.lagre(fn)
        print(f"Ferdig! Lagret som {fn}")
        os.startfile(fn) if hasattr(os, 'startfile') else None

if __name__ == "__main__":
    main()