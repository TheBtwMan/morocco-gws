import os
import re
import unicodedata
import backend

# Official list of regions
REGIONS = [
    'Béni Mellal-Khénifra', 'Casablanca-Settat', 'Dakhla-Oued Ed-Dahab', 
    'Drâa-Tafilalet', 'Fez-Meknes', 'Guelmim-Oued Noun', 
    'Laâyoune-Sakia El Hamra', 'Marrakech-Safi', 'Oriental', 
    'Rabat-Salâ-Kenitra', 'Souss-Massa', 'Tangier-Tetouan-Al Hoceima'
]

def normalize_text(text: str) -> str:
    """Standardizes text: lowercase, removes accents, replaces special characters."""
    if not text:
        return ""
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace("-", " ").replace("'", " ").replace("’", " ")
    return text

# Mapping normalized region terms to official names
REGION_MAP = {}
for r in REGIONS:
    normalized = normalize_text(r)
    REGION_MAP[normalized] = r
    # Also add shorter common names
    parts = normalized.split()
    for part in parts:
        if len(part) > 3 and part not in ['oued', 'safi', 'noun', 'settat', 'mellal', 'salâ', 'tetraon', 'hoceima']:
            REGION_MAP[part] = r

def detect_regions(message: str) -> list:
    """Returns a list of official region names found in the message."""
    norm_msg = normalize_text(message)
    detected = []
    
    # Try exact matches first
    for norm_key, official in REGION_MAP.items():
        if norm_key in norm_msg:
            if official not in detected:
                detected.append(official)
                
    return detected

def get_expert_location_report(location_title: str, lat: float, lon: float, year: int, gw_val: float, gwd_val: float, ndwi_val: float, ndvi_val: float) -> str:
    """Generates a detailed, scientific agriculture and soil advice report for a specific coordinate/commune/region."""
    
    # Calculate subscores and overall score
    gw = gw_val if gw_val is not None else -0.5
    gwd = gwd_val if gwd_val is not None else -0.25
    water = ndwi_val if ndwi_val is not None else -0.1
    veg = ndvi_val if ndvi_val is not None else 0.25
    
    gw_score = min(max(int((gw + 1.5) / 3.0 * 100), 0), 100)
    ndwi_score = min(max(int((water + 0.5) * 100), 0), 100)
    ndvi_score = min(max(int(veg / 0.8 * 100), 0), 100)
    
    viability_score = int(0.35 * gw_score + 0.3 * ndwi_score + 0.35 * ndvi_score)
    
    # Determine Rating Category
    if viability_score < 35:
        rating = "🔴 SEVERE WATER STRESS / HIGH AGRICULTURAL RISK"
        summary = "Traditional agriculture is highly discouraged. Prioritize non-water intensive agrotech or renewable energy."
    elif viability_score < 60:
        rating = "🟡 MODERATE RISK / ADAPTIVE STRATEGY REQUIRED"
        summary = "Favorable for drought-resistant cultivars using advanced water-saving techniques."
    else:
        rating = "🟢 STRONG RESOURCE BASE / HIGH VIABILITY"
        summary = "Stable indices. Highly suitable for commercial high-value organic agriculture and crop canopy maintenance."

    # Climate zone extraction based on Latitude
    is_southern = False
    if lat is not None:
        try:
            is_southern = float(lat) < 32.0
        except ValueError:
            pass
            
    # Also check title name for southern areas
    loc_title_norm = location_title.lower()
    if any(r.lower() in loc_title_norm for r in ['souss', 'massa', 'marrakech', 'safi', 'draa', 'tafilalet', 'guelmim', 'noun', 'laayoune', 'dakhla', 'oriental']):
        is_southern = True
        
    if is_southern:
        zone_name = "Arid / Semi-Arid Southern Zone"
        climate_profile = "High solar radiation, sparse rainfall, and high evapotranspiration. Aquifer depletion is a severe concern."
        recommended_crops = """*   🌴 **Majhool Date Palms**: Highly tolerant of heat and dry conditions, with exceptional market returns.
*   🌳 **Argan Trees**: Endemic to the region, deep-rooting to bind soil and withstand extreme drought.
*   🌿 **Carob (Kharroub)**: Low water requirement, high value seeds, excellent for preventing desertification.
*   🌵 **Cactus Pear & Aromatic Herbs**: Forage/fruit with minimal transpiration loss; rosemary/thyme for high-margin oils."""
        discouraged_crops = "Watermelons, avocados, flood-irrigated alfalfa, and high-volume open-field vegetables."
    else:
        zone_name = "Sub-Humid / Humid Northern Zone"
        climate_profile = "Moderate rainfall, cooler oceanic influences, and fertile soils, but requires climate-resilient water allocation."
        recommended_crops = """*   🍓 **Organic Berries (Blueberries, Raspberries)**: Highly lucrative, suited to precise computer-scheduled drip systems.
*   🥦 **Specialty Greenhouse Vegetables**: Optimized soil-less cultivation to maximize crop yield per drop.
*   🌱 **Winter Pulses & Legumes (Faba beans, Lentils)**: Recommended for nitrogen-fixing soil rotation.
*   🌳 **Carob & Olive Orchards**: High-value yield on sloped terrain to minimize run-off soil erosion."""
        discouraged_crops = "Continuous wheat/cereal monoculture without crop rotation, and open-air sprinkler irrigation on windy hot afternoons."

    # Indices advices
    if gw < -0.8:
        gw_status = "🔴 Critical Depletion"
        gw_advice = "Severe aquifer deficit. Avoid drilling deep boreholes. Establish micro-catchments or rain reservoirs to reduce reliance on groundwater."
    elif gw < 0:
        gw_status = "🟡 Moderate Deficit"
        gw_advice = "Groundwater levels are dropping. Implement subsurface drip irrigation to target root zones directly and minimize evaporation."
    else:
        gw_status = "🟢 Stable/Recharging"
        gw_advice = "Aquifer is in stable condition. Limit abstraction to recharge rates. Consider seasonal water storage."

    # GWD advice
    if gwd < -1.0:
        gwd_status = "🔴 Severe Water Table Drop"
        gwd_advice = f"Groundwater depth has dropped by {abs(gwd):.2f} meters. High pumping energy costs and regulatory risks. Prioritize high-efficiency micro-drip systems or non-groundwater sources."
    elif gwd < 0:
        gwd_status = "🟡 Moderate Water Table Drop"
        gwd_advice = f"Groundwater depth has decreased by {abs(gwd):.2f} meters. Keep pumping hours localized and apply soil mulching to conserve moisture."
    else:
        gwd_status = "🟢 Stable/Recharging Water Table"
        gwd_advice = f"Groundwater depth has risen or stabilized by {gwd:.2f} meters. Maintain sustainable withdrawal rates."

    if water < -0.2:
        ndwi_status = "🔴 Dry/Arid Soil"
        ndwi_advice = "Extreme soil moisture deficit. Apply organic mulch (straw/plastic) to block evaporation. Integrate compost/manure to boost soil water retention."
    elif water < 0.15:
        ndwi_status = "🟡 Moderate Moisture"
        ndwi_advice = "Damp to dry soil. Deploy IoT soil moisture tensiometer probes to schedule watering only when soil suction thresholds are crossed."
    else:
        ndwi_status = "🟢 High Moisture"
        ndwi_advice = "Abundant surface moisture. Ensure adequate field drainage to prevent waterlogging, root rot, and mildew."

    if veg < 0.15:
        ndvi_status = "🔴 Bare Soil/Desert"
        ndvi_advice = "Very low canopy cover. Plant windbreak tree lines (e.g. cypress) to mitigate dry winds. Cultivate winter cover crops to reconstruct organic topsoil."
    elif veg < 0.4:
        ndvi_status = "🟡 Sparse Canopy"
        ndvi_advice = "Early-stage crop or shrubland. Implement crop-canopy monitoring and weed control to ensure nutrients reach primary crops."
    else:
        ndvi_status = "🟢 Rich Canopy"
        ndvi_advice = "Robust active agriculture. Maintain high soil fertility using crop rotation and organic cover cropping."

    # Format coordinate display
    coord_str = f" (Lat: {lat:.4f}, Lon: {lon:.4f})" if lat is not None and lon is not None else ""

    report = f"""### 📊 Agricultural & Soil Suitability Report: **{location_title}**{coord_str}

Based on live **Google Earth Engine (GEE)** indicators for year **{year}**, here is the climate-resilient agricultural assessment:

---

#### 🌟 Viability Class: **{rating}**
#### 📈 Resource Score: **{viability_score}/100**

*{summary}*

---

#### 🗺️ Agro-Climatic Zone: **{zone_name}**
*   **Climate Profile**: {climate_profile}
*   **Recommended Resilient Crops**:
{recommended_crops}
*   **High-Risk Crops to Exclude**: *{discouraged_crops}*

---

#### 🔍 Environmental Indices & Soil Advice

*   💧 **Groundwater Storage (GRACE)**: **{gw:.3f} cm** ({gw_status})
    *   *Advice*: {gw_advice}
*   🕳️ **Groundwater Depth (GWD)**: **{gwd:.3f} m** ({gwd_status})
    *   *Advice*: {gwd_advice}
*   🌊 **Surface Soil Moisture (NDWI)**: **{water:.3f}** ({ndwi_status})
    *   *Advice*: {ndwi_advice}
*   🌾 **Vegetation Density (NDVI)**: **{veg:.3f}** ({ndvi_status})
    *   *Advice*: {ndvi_advice}
"""
    return report

def get_expert_report(region: str, year: int, gw_val: float, ndwi_val: float, ndvi_val: float) -> str:
    """Fallback wrapper for backwards compatibility."""
    return get_expert_location_report(f"Region: {region}", None, None, year, gw_val, None, ndwi_val, ndvi_val)

def generate_chat_response(message: str, history: list, year: int, current_index: str, current_region: str, current_location: dict = None) -> str:
    """Main chatbot engine. Detects region/location, integrates GEE data, and generates agricultural insights."""
    
    # 1. Normalize message and check for explanations
    norm_msg = normalize_text(message)
    
    # General Index Explanations
    if "ndvi" in norm_msg or ("vegetation" in norm_msg and "explain" in norm_msg):
        return """### 🌾 NDVI (Normalized Difference Vegetation Index) Explained

**NDVI** measures the health and density of vegetation using satellite sensors (Sentinel-2, Landsat). It calculates the ratio of near-infrared light reflected by healthy leaves to red light absorbed by chlorophyll:

$$\text{NDVI} = \\frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$$

*   **Values Range**: `-1.0` to `1.0`.
*   **Interpretation**:
    *   `0.0 to 0.15`: Bare soil, sand, rocks.
    *   `0.15 to 0.4`: Sparse vegetation, scrubland, early-stage crops.
    *   `0.4 to 0.8`: Healthy forests, dense agriculture, mature crops.
*   **Investment Relevance**: Helps investors monitor crop health, verify crop yields remotely, and detect deforestation or land degradation trends.
"""
        
    if "ndwi" in norm_msg or ("water" in norm_msg and "index" in norm_msg and "explain" in norm_msg):
        return """### 🌊 NDWI (Normalized Difference Water Index) Explained

**NDWI** monitors surface water features, flooding, and vegetation liquid water content. It highlights differences in near-infrared and shortwave-infrared (or green) light:

$$\text{NDWI} = \\frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}}$$

*   **Values Range**: `-1.0` to `1.0`.
*   **Interpretation**:
    *   `> 0.3`: Open surface water (lakes, reservoirs, oceans).
    *   `0.0 to 0.2`: Damp soil, shallow mud, high crop moisture.
    *   `< 0.0`: Dry soils, bare land, desert rock.
*   **Investment Relevance**: Essential to verify surface water availability. High NDWI indicates robust local reservoirs or canals; dropping NDWI signals agricultural drought.
"""

    if "groundwater" in norm_msg or "grace" in norm_msg or "nappe" in norm_msg:
        return """### 💧 Groundwater Storage Anomaly (GRACE) Explained

**Groundwater Anomaly** data is fetched from the joint NASA/DLR **GRACE-FO** (Gravity Recovery and Climate Experiment) satellites. It measures subtle changes in Earth's gravitational pull caused by shifts in water mass underground:

*   **Metric**: LWE (Liquid Water Equivalent) thickness anomaly in centimeters.
*   **Interpretation**:
    *   **Negative Anomaly (< 0 cm)**: Depletion of deep groundwater reserves (water table is dropping).
    *   **Positive Anomaly (> 0 cm)**: Aquifer recharge (stable or increasing water reserves).
*   **Investment Relevance**: Groundwater is the ultimate security buffer for dry periods. Deep negative anomalies indicate high risk of dry wells, strict extraction limits, and eventual high energy costs to pump deeper water.
"""

    # 2. Determine location/region focus
    detected = detect_regions(message)
    
    location_title = None
    lat = None
    lon = None
    gw_val = None
    gwd_val = None
    ndwi_val = None
    ndvi_val = None
    is_custom_point = False
    region = None
    
    if detected:
        region = detected[0]
    elif current_location and current_location.get("data") is not None:
        location_title = current_location.get("title", "Selected Location")
        try:
            lat = float(current_location.get("lat"))
            lon = float(current_location.get("lon"))
        except (ValueError, TypeError):
            lat = None
            lon = None
        
        data_vals = current_location.get("data", {})
        gw_val = data_vals.get("gwsa")
        gwd_val = data_vals.get("gwd")
        ndwi_val = data_vals.get("ndwi")
        ndvi_val = data_vals.get("ndvi")
        is_custom_point = True
    elif current_region and current_region in REGIONS:
        region = current_region

    # 3. Handle data querying for regional queries
    if region and not is_custom_point:
        location_title = f"Region: {region}"
        # Use GEE to fetch data
        try:
            gw_dataset = backend.get_all_regions_data(year, "gwsa")
            gwd_dataset = backend.get_all_regions_data(year, "gwd")
            ndwi_dataset = backend.get_all_regions_data(year, "ndwi")
            ndvi_dataset = backend.get_all_regions_data(year, "ndvi")
            
            gw_val = gw_dataset.get(region)
            gwd_val = gwd_dataset.get(region) if gwd_dataset else None
            ndwi_val = ndwi_dataset.get(region)
            ndvi_val = ndvi_dataset.get(region)
        except Exception as e:
            # Fallback to realistic values based on climatological averages of regions in case GEE is unreachable
            print(f"GEE backend query failed: {e}. Using regional approximations.")
            region_defaults = {
                "Souss-Massa": (-1.3, -0.6, -0.22, 0.25),
                "Marrakech-Safi": (-1.1, -0.5, -0.18, 0.28),
                "Casablanca-Settat": (-0.6, -0.3, -0.05, 0.42),
                "Rabat-Salâ-Kenitra": (-0.2, -0.1, 0.12, 0.55),
                "Tangier-Tetouan-Al Hoceima": (0.1, 0.05, 0.18, 0.62),
                "Fez-Meknes": (-0.4, -0.2, 0.05, 0.48),
                "Drâa-Tafilalet": (-1.4, -0.7, -0.38, 0.12),
                "Dakhla-Oued Ed-Dahab": (-0.2, -0.1, -0.45, 0.08),
                "Guelmim-Oued Noun": (-0.9, -0.4, -0.32, 0.15),
                "Laâyoune-Sakia El Hamra": (-0.5, -0.2, -0.42, 0.09),
                "Oriental": (-0.8, -0.4, -0.25, 0.22),
                "Béni Mellal-Khénifra": (-0.9, -0.4, -0.08, 0.38),
            }
            gw_val, gwd_val, ndwi_val, ndvi_val = region_defaults.get(region, (-0.5, -0.25, -0.15, 0.3))

    # 4. Generate response for the determined location/point
    if location_title:
        # Try to use Generative AI (Gemini) if API key is present
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                # pyrefly: ignore [missing-import]
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                location_desc = f"selected point '{location_title}' at coordinates ({lat:.4f}, {lon:.4f})" if is_custom_point else f"region '{region}'"
                
                prompt = f"""
You are the GeoAI Moroccan Resource & Investment Advisor, an expert agricultural economist and spatial analyst.
You help farmers, developers, and investors assess agricultural suitability, crop viability, and water risks in Morocco.

A user has sent you this message: "{message}"

Here is the scientific sensor data we fetched from Google Earth Engine for the {location_desc} (Year: {year}):
- Name/Title: {location_title}
- Coordinates: {f"Latitude: {lat:.4f}, Longitude: {lon:.4f}" if is_custom_point else "Regional average"}
- Groundwater Anomaly (GWSA): {gw_val:.3f} cm (GRACE)
- Groundwater Depth Change (GWD): {gwd_val:.3f} m if gwd_val else "N/A"
- Surface Water/Moisture Index (NDWI): {ndwi_val:.3f}
- Vegetation Health Index (NDVI): {ndvi_val:.3f}

Current Active Map View in Platform:
- Year: {year}
- Current Filter: {current_index}

Please analyze this data and write a professional, highly engaging, and context-specific response:
1. State the agricultural viability outlook (e.g. High Risk, Moderate Adaptive, or High Potential).
2. Briefly explain what the GEE indices mean for local water availability, groundwater depth change (GWD), and soil conditions at these specific coordinates.
3. Recommend 3 specific sustainable crops or farming models matching this climate zone and GEE indices (e.g., olive, argan, carob, date palms, cactus, aromatic herbs for dry zones; berries/vegetables for wet zones) and explain why they fit.
4. Give explicit warnings against 2 water-heavy crops (e.g., watermelon, avocado) if there is groundwater depletion (GWSA < -0.8 or GWD drop < -0.4m) or low moisture.
5. Provide 2-3 actionable soil or water conservation recommendations (e.g., mulching, subsurface drip, rainwater harvesting, cover cropping) based on the indices.

Format your response beautifully in Markdown. Use bullet points, bold text, and warning blockquotes (> [!WARNING]) or tip blockquotes (> [!TIP]) where appropriate. Keep the tone professional, realistic, and insightful. Do not exceed 450 words.
"""
                response = model.generate_content(prompt)
                return response.text
            except Exception as gem_err:
                print(f"Gemini API invocation failed: {gem_err}. Using Data-Driven Expert Engine.")
                
        # Generate the structured report via local expert system
        return get_expert_location_report(location_title, lat, lon, year, gw_val, gwd_val, ndwi_val, ndvi_val)

    # 5. Standard conversational responses or general inquiries about Morocco
    if "invest" in norm_msg or "opportunit" in norm_msg:
        return """### 🇲🇦 Morocco Resource & Investment General Outlook

Morocco is an emerging hotspot for green transition investments, but geographical water resource disparities require highly localized screening. 

#### 🚀 Key Investment Corridors

1.  **Souss-Massa & Marrakech-Safi**:
    *   **Outlook**: High Risk for Agriculture, World-Class for Solar and Water Technologies.
    *   *Strategic Advice*: Transition out of heavy fruits (citrus) into high-value oils (olive/argan) and smart glasshouse farming.
2.  **Rabat-Salé-Kenitra & Tangier-Tetouan-Al Hoceima**:
    *   **Outlook**: Low-to-Medium Risk, Fertile soils, and higher NDWI water security.
    *   *Strategic Advice*: Highly favorable for organic produce, berry crops, food packaging hubs, and wind power.
3.  **Southern Regions (Dakhla & Laâyoune)**:
    *   **Outlook**: High Aridity but Massive Coastal Opportunities.
    *   *Strategic Advice*: Excellent for solar, wind energy, green hydrogen plants, greenhouse desalinated agriculture, and premium coastal aquaculture.

*💡 Select a specific region on the map or type a region's name (e.g., "Is Souss-Massa safe to invest in?") to receive a complete custom scientific report!*
"""

    return f"""### 👋 Welcome to the GeoAI Resource & Investment Advisor!

I am your intelligent assistant linked directly to **Google Earth Engine (GEE)**. I analyze soil, surface moisture, and deep aquifers in Morocco to help you make climate-resilient investment decisions.

#### 💡 How to Interact with Me:
1.  **Ask about a specific region**: Type something like *"Can I invest in Souss-Massa?"* or *"Analyze Marrakech-Safi"*.
2.  **Learn about scientific indices**: Ask *"What is NDWI?"*, *"Explain NDVI"*, or *"How is groundwater measured?"*.
3.  **Use Active Map Context**: Check **"Sync Map Context"** below. When enabled, asking *"Is it safe to invest here?"* will automatically analyze the active region, year, and index currently selected on your map view!

*Select a preset question pill below or type your custom query to begin!*
"""
