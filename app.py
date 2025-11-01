from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for
import os
import pandas as pd

app = Flask(__name__)
DATA_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")

CATEGORIES = {
    "Environment": ["Climate", "Weather", "Water","Land Use & Agriculture", "Energy", "Waste & Recycling",
                    "Air Quality",  "Biodiversity & Wildlife"],
    "Education": [],
    "Health": [],
    "Transportation": ["Traffic Flow", "Road Networks", "Public Transit"],
    "Finance & Economics": [],
    "Technology": [],
    "Tourism": [],
    "Demographics": [],
    "World Bank Data": []
}

SUBCATEGORY_DATA = {
    "Weather": ["phnom_penh_history_weather_2015_2025.csv"],
    "Land Use & Agriculture": ["Cambodia_Province_Monthly_NDVI_2021.csv"],
    "Water": ["TonleSap_GSW_2000_2021.zip"],
    "Climate": ["ncsd_data_portal_family_2014_2019.zip", "ncsd_data_portal_vi_2014_2022.zip"]
}

DATASET_INFO = {
    "phnom_penh_history_weather_2015_2025.csv": {
        "title": "Phnom Penh history weather from 2015 to 2025",
        "size": "2.85 MB",
        "source": "Open-Meteo",
        "description": "Historical weather data of Phnom Penh for the past 10 years was collected from Open-Meteo. Each row represents an observation at a specific date and time, containing various meteorological variables.",
        "columns": {
            "time": "timestamp of the observation",
            "temperature_2m": "air temperature measured at 2 meters above ground in °C",
            "relative_humidity_2m": "percentage of moisture in the air at 2 meters",
            "recipitation": "rainfall amount in millimeters per hour",
            "wind_speed_10m": "wind speed measured at 10 meters above ground in meters per second"
        }
    },
    "Cambodia_Province_Monthly_NDVI_2021.csv": {
        "title": "Cambodia Province Monthly NDVI in 2021",
        "size": "43.5 KB",
        "source": "Google Earth Engine",
        "description": "A structured dataset of province-level NDVI statistics for the year 2021, which forms the foundation for subsequent analysis of seasonal vegetation dynamics and spatial variations in land cover.",
        "columns": {
            "system:index": "Internal ID for the feature.",
            "ADM0_CODE": "Country code (44 = Cambodia).",
            "ADM0_NAME": "Country name (Cambodia).",
            "ADM1_CODE": "Province code.",
            "ADM1_NAME": "Province name (e.g., Otdar Meanchey, Siem Reap, Battambang, Pailin).",
            "DISP_AREA": "Display area (here NO).",
            "EXP1_YEAR": "Export year (3000 = placeholder in GAUL dataset).",
            "STATUS": "Country status in GAUL (Member State).",
            "STR1_YEAR": "Start year of administrative unit (e.g., 1995, 1997).",
            "Shape_Area / Shape_Leng": "Polygon geometry's area and perimeter length.",
            "mean": "Mean NDVI (Normalized Difference Vegetation Index) for that province in 2021.",
            "median": "Median NDVI for that province in 2021.",
            "month": "Month of data extraction (1 = January).",
            "stdDev": "Standard deviation of NDVI within the province.",
            "year": "Observation year (2021)."
        }
    },
    "TonleSap_GSW_2000_2021.zip": {
        "title": "TonleSap Global Surface Water from 2000 to 2021",
        "size": "15.3 MB",
        "source": "Google Earth Engine",
        "description": "A time series of 21 raster images (2000-2021) was collected, each representing the yearly water distribution in the Tonlé Sap Lake region. This dataset forms the foundation for analyzing long-term hydrological dynamics, seasonal variability, and potential impacts of climate change and human interventions on Cambodia's largest freshwater lake.",
        "preview_image": "temp_preview/water.png"
    },
    "ncsd_data_portal_vi_2014_2022.zip": {
        "title": "Vulnerability to climate hazards (2014-2022)",
        "size": "14.8 MB",
        "source": "Open Development Cambodia",
        "description": "This dataset presents the percentage and count of provinces and communes classified by their vulnerability index scores. It includes metrics for floods, storms, droughts, and an overall composite vulnerability index, making it an important resource for understanding climate change impacts. It offers valuable insights into regional vulnerability, supporting analysis and planning for climate-related risks.",
        "preview_image": "temp_preview/vulnerable.png"
    },
    "ncsd_data_portal_family_2014_2019.zip": {
        "title": "Families affected by climate hazards (2014-2019)",
        "size": "5.19 MB",
        "source": "Open Development Cambodia",
        "description": "This dataset tracks annual loss and damage from extreme weather in Cambodia by measuring the share of families affected by at least one of three major climate hazards: floods, storms, or droughts. It records the number of families impacted per 1,000 households for each hazard and shows how these figures have changed over time at both provincial and commune levels since 2014.",
        "preview_image": "temp_preview/families_affected.png"
    },
}


# --- ROUTES ---

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES.keys())

@app.route("/category/<category_name>")
def category_page(category_name):
    subcategories = CATEGORIES.get(category_name, [])
    return render_template("category.html", category_name=category_name, subcategories=subcategories)

@app.route("/dataset/<subcategory>")
def dataset_page(subcategory):
    files = SUBCATEGORY_DATA.get(subcategory, [])
    dataset_list = []
    for f in files:
        ext = os.path.splitext(f)[1]
        file_type = ext.replace('.', '').upper() if ext else "FILE"
        dataset_list.append({"name": os.path.splitext(f)[0], "filename": f, "type": file_type})
    return render_template("dataset.html", subcategory=subcategory, datasets=dataset_list)


@app.route("/preview/<filename>")
def preview_dataset(filename):
    info = DATASET_INFO.get(filename, {}).copy()
    ext = os.path.splitext(filename)[1].lower()
    sample_data = []

    try:
        if ext == ".zip":
            preview_path = info.get("preview_image")
            if preview_path:
                image_full_path = os.path.join(app.static_folder, preview_path)
                if os.path.exists(image_full_path):
                    info["preview_image_url"] = url_for("static", filename=preview_path)
                else:
                    info["preview_image_url"] = None
            return jsonify({"info": info, "sample": []})

        elif ext in [".csv", ".xlsx", ".xls", ".json"]:
            file_path = os.path.join(DATA_FOLDER, filename)
            if not os.path.exists(file_path):
                return jsonify({"error": f"File not found: {filename}"}), 404

            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            else:
                df = pd.read_json(file_path)

            sample_data = df.head(5).to_dict(orient="records")
            if not info.get("columns"):
                info["columns"] = {col: "No description available." for col in df.columns.tolist()}

            return jsonify({"info": info, "sample": sample_data})

        else:
            # For unsupported file types
            return jsonify({"info": info, "sample": []})

    except Exception as e:
        print(f"[ERROR] Preview failed for {filename}: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/download/<filename>")
def download_dataset(filename):
    return send_from_directory(DATA_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        print(f"Created data folder: {DATA_FOLDER}")
    app.run(debug=True)
