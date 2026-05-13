import cv2
import numpy as np

class ElevationManager:
    def __init__(self, dem_bilde_sti, kart_bredde, kart_hoyde, min_hoyde=0, maks_hoyde=500):
        """
        dem_bilde_sti: Stien til gråtonebildet fra Kartverket.
        kart_bredde/kart_hoyde: Størrelsen på hovedkartet (så vi kan auto-skalere DEM).
        min_hoyde/maks_hoyde: Meter for svart (0) og hvit (255).
        """
        self.dem_data = cv2.imread(dem_bilde_sti, cv2.IMREAD_GRAYSCALE)
        
        if self.dem_data is None:
            print(f"Advarsel: Kunne ikke laste høydedata fra {dem_bilde_sti}")
            self.h, self.w = 0, 0
        else:
            # --- DEN MAGISKE AUTO-SKALERINGEN ---
            # Vi tvinger høydemodellen til å bli nøyaktig like stor i piksler som o-kartet!
            self.dem_data = cv2.resize(self.dem_data, (kart_bredde, kart_hoyde), interpolation=cv2.INTER_LINEAR)
            self.h, self.w = self.dem_data.shape
            print(f"Høydemodell lastet og auto-skalert til: {self.w}x{self.h} piksler.")

        self.min_hoyde = min_hoyde
        self.maks_hoyde = maks_hoyde

    def get_hoyde(self, x, y):
        if self.dem_data is None: return 0
        x = max(0, min(int(x), self.w - 1))
        y = max(0, min(int(y), self.h - 1))
        
        verdi = self.dem_data[y, x]
        meter = self.min_hoyde + (verdi / 255.0) * (self.maks_hoyde - self.min_hoyde)
        return meter

    def beregn_stigning_mellom_punkter(self, p1, p2):
        h1 = self.get_hoyde(p1[0], p1[1])
        h2 = self.get_hoyde(p2[0], p2[1])
        if h2 > h1:
            return h2 - h1
        return 0
