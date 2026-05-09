class ElevationMap:
    def __init__(self, dem_matrix):
        """
        dem_matrix er en 2D-liste/array der hver celle inneholder høyden i meter.
        """
        self.grid = dem_matrix

    def get_height(self, x, y):
        """Henter høyden i meter for et gitt (x, y) koordinat."""
        # I et ekte program vil du bruke biblioteker som rasterio eller numpy 
        # for å lese ekte .tif (GeoTIFF) filer med høydedata her.
        try:
            return self.grid[int(y)][int(x)]
        except IndexError:
            return 0 # Utenfor kartet