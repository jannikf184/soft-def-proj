import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature




def plot_germany_weather(data):
    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent([5 , 16, 47, 55])  # grob Deutschland

    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND, edgecolor='black')
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS)

    for entry in data:
        ax.scatter(entry['lon'], entry['lat'], color='red', s=100, alpha=0.7)
        ax.text(entry['lon'] + 0.1, entry['lat'], f"{entry['city']}: {entry['temperature']}°C", fontsize=9)

    plt.title("Temperaturverteilung in Deutschland")
    return fig