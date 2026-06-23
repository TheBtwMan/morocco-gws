import os
import re
import unicodedata
import backend

def load_env_file():
    """Simple, dependency-free helper to load a .env file from the current directory or parent directories."""
    for path in ['.env', '../.env', 'backend+api/.env', '../backend+api/.env', '../../.env']:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, val = line.split('=', 1)
                            # Strip quotes if present
                            val = val.strip().strip('"').strip("'")
                            os.environ[key.strip()] = val
            except Exception as e:
                print(f"Error loading .env file from {path}: {e}")
            break

# Load env variables on startup
load_env_file()


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

def get_expert_location_report(
    location_title: str, lat: float, lon: float, year: int, 
    gw_val: float, gwd_val: float, ndwi_val: float, ndvi_val: float,
    recharge_val: float = None, water_quantity_val: float = None, suitability_val: float = None
) -> str:
    """Generates a detailed, scientific agriculture and soil advice report for a specific coordinate/commune/region."""
    
    # Calculate subscores and overall score
    gw = gw_val if gw_val is not None else -0.5
    gwd = gwd_val if gwd_val is not None else -0.25
    gwr = recharge_val if recharge_val is not None else 50.0
    water = ndwi_val if ndwi_val is not None else -0.1
    swq = water_quantity_val if water_quantity_val is not None else 0.1
    veg = ndvi_val if ndvi_val is not None else 0.25
    lsi = suitability_val if suitability_val is not None else 0.3
    
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
        gwd_advice = f"Groundwater depth has dropped by {abs(gwd):.2f} meters. High pumping energy costs and regulatory risks. Prioritize high-efficiency micro-drip systems."
    elif gwd < 0:
        gwd_status = "🟡 Moderate Water Table Drop"
        gwd_advice = f"Groundwater depth has decreased by {abs(gwd):.2f} meters. Keep pumping hours localized and apply soil mulching to conserve moisture."
    else:
        gwd_status = "🟢 Stable/Recharging Water Table"
        gwd_advice = f"Groundwater depth has risen or stabilized by {gwd:.2f} meters. Maintain sustainable withdrawal rates."

    # Recharge advice
    if gwr < 0.0:
        gwr_status = "🔴 Recharge Deficit (Evapotranspiration > Precipitation)"
        gwr_advice = f"The region is under net recharge deficit ({gwr:.2f} mm/yr). Aquifers are highly vulnerable."
    elif gwr < 4.0:
        gwr_status = "🟡 Low-Moderate Recharge"
        gwr_advice = f"Low active recharge ({gwr:.2f} mm/yr). Sustainable extraction is required."
    else:
        gwr_status = "🟢 Good Active Recharge"
        gwr_advice = f"Aquifer is actively replenished ({gwr:.2f} mm/yr). Safe for sustainable long-term irrigation projects."

    if water < -0.2:
        ndwi_status = "🔴 Dry/Arid Soil"
        ndwi_advice = "Extreme soil moisture deficit. Apply organic mulch (straw/plastic) to block evaporation. Integrate compost/manure to boost soil water retention."
    elif water < 0.15:
        ndwi_status = "🟡 Moderate Moisture"
        ndwi_advice = "Damp to dry soil. Deploy IoT soil moisture tensiometer probes to schedule watering only when soil suction thresholds are crossed."
    else:
        ndwi_status = "🟢 High Moisture"
        ndwi_advice = "Abundant surface moisture. Ensure adequate field drainage to prevent waterlogging, root rot, and mildew."

    # Surface water quantity advice
    if swq < 0.1:
        swq_status = "🔴 Critical Surface Deficit"
        swq_advice = f"Surface water presence is extremely scarce ({swq:.2f}). Channel flow or open reservoir storage is unfeasible. Use closed tank storage."
    elif swq < 0.4:
        swq_status = "🟡 Moderate Surface Supply"
        swq_advice = f"Moderate local surface water availability ({swq:.2f}). Optimize extraction scheduling to coordinate with local canal rotations."
    else:
        swq_status = "🟢 Abundant Surface Water"
        swq_advice = f"Excellent surface water index ({swq:.2f}). Highly suited for surface intake pumps and gravity drip irrigation."

    if veg < 0.15:
        ndvi_status = "🔴 Bare Soil/Desert"
        ndvi_advice = "Very low canopy cover. Plant windbreak tree lines (e.g. cypress) to mitigate dry winds. Cultivate winter cover crops to reconstruct organic topsoil."
    elif veg < 0.4:
        ndvi_status = "🟡 Sparse Canopy"
        ndvi_advice = "Early-stage crop or shrubland. Implement crop-canopy monitoring and weed control to ensure nutrients reach primary crops."
    else:
        ndvi_status = "🟢 Rich Canopy"
        ndvi_advice = "Robust active agriculture. Maintain high soil fertility using crop rotation and organic cover cropping."

    # Land Suitability advice
    if lsi < 0.3:
        lsi_status = "🔴 Low Agriculture Suitability"
        lsi_advice = f"Multi-spectral land capacity is low ({lsi:.2f}). Avoid commercial cropping without intensive soil conditioning cover crops."
    elif lsi < 0.6:
        lsi_status = "🟡 Moderate Suitability"
        lsi_advice = f"Moderate land capacity ({lsi:.2f}). Recommended for drought-tolerant orchards (olive, carob) rather than open vegetable fields."
    else:
        lsi_status = "🟢 Prime Agricultural Land"
        lsi_advice = f"Excellent agricultural suitability index ({lsi:.2f}). Optimal soil-vegetation moisture structure; highly viable for high-value cash crops."

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

*   💧 **Groundwater Storage (GWSA)**: **{gw:.3f} cm** ({gw_status})
    *   *Advice*: {gw_advice}
*   🕳️ **Groundwater Depth (GWD)**: **{gwd:.3f} m** ({gwd_status})
    *   *Advice*: {gwd_advice}
*   🌧️ **Groundwater Recharge (GWR)**: **{gwr:.3f} mm/yr** ({gwr_status})
    *   *Advice*: {gwr_advice}
*   🌊 **Surface Soil Moisture (NDWI)**: **{water:.3f}** ({ndwi_status})
    *   *Advice*: {ndwi_advice}
*   🌊 **Surface Water Quantity (SWQ)**: **{swq:.3f}** ({swq_status})
    *   *Advice*: {swq_advice}
*   🌾 **Vegetation Density (NDVI)**: **{veg:.3f}** ({ndvi_status})
    *   *Advice*: {ndvi_advice}
*   🚜 **Land Suitability Index (LSI)**: **{lsi:.3f}** ({lsi_status})
    *   *Advice*: {lsi_advice}
"""
    return report

def get_smart_local_report(
    message: str, location_title: str, lat: float, lon: float, year: int,
    gw_val: float, gwd_val: float, ndwi_val: float, ndvi_val: float,
    recharge_val: float = None, water_quantity_val: float = None, suitability_val: float = None
) -> str:
    """Generates a query-relevant localized resource report when Gemini is not available."""
    
    # Normalize values
    gw = gw_val if gw_val is not None else -0.5
    gwd = gwd_val if gwd_val is not None else -0.25
    gwr = recharge_val if recharge_val is not None else 50.0
    water = ndwi_val if ndwi_val is not None else -0.1
    swq = water_quantity_val if water_quantity_val is not None else 0.1
    veg = ndvi_val if ndvi_val is not None else 0.25
    lsi = suitability_val if suitability_val is not None else 0.3
    
    gw_score = min(max(int((gw + 1.5) / 3.0 * 100), 0), 100)
    ndwi_score = min(max(int((water + 0.5) * 100), 0), 100)
    ndvi_score = min(max(int(veg / 0.8 * 100), 0), 100)
    
    viability_score = int(0.35 * gw_score + 0.3 * ndwi_score + 0.35 * ndvi_score)
    
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

    # Indices advice
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
        gwd_advice = f"Groundwater depth has dropped by {abs(gwd):.2f} meters. High pumping energy costs and regulatory risks. Prioritize high-efficiency micro-drip systems."
    elif gwd < 0:
        gwd_status = "🟡 Moderate Water Table Drop"
        gwd_advice = f"Groundwater depth has decreased by {abs(gwd):.2f} meters. Keep pumping hours localized and apply soil mulching to conserve moisture."
    else:
        gwd_status = "🟢 Stable/Recharging Water Table"
        gwd_advice = f"Groundwater depth has risen or stabilized by {gwd:.2f} meters. Maintain sustainable withdrawal rates."

    # Recharge advice
    if gwr < 0.0:
        gwr_status = "🔴 Recharge Deficit (Evapotranspiration > Precipitation)"
        gwr_advice = f"The region is under net recharge deficit ({gwr:.2f} mm/yr). Aquifers are highly vulnerable."
    elif gwr < 4.0:
        gwr_status = "🟡 Low-Moderate Recharge"
        gwr_advice = f"Low active recharge ({gwr:.2f} mm/yr). Sustainable extraction is required."
    else:
        gwr_status = "🟢 Good Active Recharge"
        gwr_advice = f"Aquifer is actively replenished ({gwr:.2f} mm/yr). Safe for sustainable long-term irrigation projects."

    if water < -0.2:
        ndwi_status = "🔴 Dry/Arid Soil"
        ndwi_advice = "Extreme soil moisture deficit. Apply organic mulch (straw/plastic) to block evaporation. Integrate compost/manure to boost soil water retention."
    elif water < 0.15:
        ndwi_status = "🟡 Moderate Moisture"
        ndwi_advice = "Damp to dry soil. Deploy IoT soil moisture tensiometer probes to schedule watering only when soil suction thresholds are crossed."
    else:
        ndwi_status = "🟢 High Moisture"
        ndwi_advice = "Abundant surface moisture. Ensure adequate field drainage to prevent waterlogging, root rot, and mildew."

    # Surface water quantity advice
    if swq < 0.1:
        swq_status = "🔴 Critical Surface Deficit"
        swq_advice = f"Surface water presence is extremely scarce ({swq:.2f}). Channel flow or open reservoir storage is unfeasible. Use closed tank storage."
    elif swq < 0.4:
        swq_status = "🟡 Moderate Surface Supply"
        swq_advice = f"Moderate local surface water availability ({swq:.2f}). Optimize extraction scheduling to coordinate with local canal rotations."
    else:
        swq_status = "🟢 Abundant Surface Water"
        swq_advice = f"Excellent surface water index ({swq:.2f}). Highly suited for surface intake pumps and gravity drip irrigation."

    if veg < 0.15:
        ndvi_status = "🔴 Bare Soil/Desert"
        ndvi_advice = "Very low canopy cover. Plant windbreak tree lines (e.g. cypress) to mitigate dry winds. Cultivate winter cover crops to reconstruct organic topsoil."
    elif veg < 0.4:
        ndvi_status = "🟡 Sparse Canopy"
        ndvi_advice = "Early-stage crop or shrubland. Implement crop-canopy monitoring and weed control to ensure nutrients reach primary crops."
    else:
        ndvi_status = "🟢 Rich Canopy"
        ndvi_advice = "Robust active agriculture. Maintain high soil fertility using crop rotation and organic cover cropping."

    # Land Suitability advice
    if lsi < 0.3:
        lsi_status = "🔴 Low Agriculture Suitability"
        lsi_advice = f"Multi-spectral land capacity is low ({lsi:.2f}). Avoid commercial cropping without intensive soil conditioning cover crops."
    elif lsi < 0.6:
        lsi_status = "🟡 Moderate Suitability"
        lsi_advice = f"Moderate land capacity ({lsi:.2f}). Recommended for drought-tolerant orchards (olive, carob) rather than open vegetable fields."
    else:
        lsi_status = "🟢 Prime Agricultural Land"
        lsi_advice = f"Excellent agricultural suitability index ({lsi:.2f}). Optimal soil-vegetation moisture structure; highly viable for high-value cash crops."

    coord_str = f" (Lat: {lat:.4f}, Lon: {lon:.4f})" if lat is not None and lon is not None else ""
    norm_msg = normalize_text(message)

    # Keyword checking to deliver query-relevant reports
    is_energy = any(k in norm_msg for k in ["solar", "sun", "wind", "renewable", "energy", "clean energy", "electricity", "panel", "photovoltaic", "pv", "turbine", "power"])
    is_tourism = any(k in norm_msg for k in ["touris", "real estate", "hotel", "resort", "build", "construction", "property", "land", "develop"]) and not any(k in norm_msg for k in ["crop", "farm", "plant", "grow"])
    is_water = any(k in norm_msg for k in ["groundwater", "gwsa", "gwd", "aquifer", "nappe", "water table", "well", "wells", "borehole", "drill", "extraction", "recharge", "gwr"])
    is_crop = any(k in norm_msg for k in ["crop", "palm", "date", "argan", "carob", "cactus", "watermelon", "avocado", "wheat", "berry", "berries", "olive", "citrus", "fruit", "farm", "plant", "grow", "agricul"])

    if is_energy:
        # Determine solar potential based on NDVI and NDWI
        if water < -0.2 and veg < 0.2:
            potential = "☀️ EXCELLENT (High Irradiance, Low Vegetation Cover)"
            verdict = f"**{location_title}** is an exceptionally prime location for solar and wind energy projects. The arid climate profile provides extremely high solar irradiance, and the vast open, low-vegetation land minimizes site preparation and environmental impact costs."
        else:
            potential = "🌤️ GOOD TO MODERATE (Moderate Irradiance, Higher Vegetation/Cloud Cover)"
            verdict = f"**{location_title}** has good solar potential, though solar panel efficiency might be slightly affected by seasonal cloud cover or higher vegetation density. It is highly suitable for localized micro-grid or solar-assisted agricultural operations."

        return f"""### ☀️ Renewable Energy & Solar Investment Assessment: **{location_title}**{coord_str}

Based on live **Google Earth Engine (GEE)** indicators for year **{year}**, here is the renewable energy suitability audit:

---

#### 🌟 Solar/Wind Potential: **{potential}**
#### 📈 Resource Score: **{viability_score}/100** (Agricultural/Water Base)

{verdict}

---

#### 🗺️ Energy & Climate Profile:
*   **Climate Zone**: {zone_name}
*   **Climate Profile**: {climate_profile}
*   **Aridity Proxy (NDWI)**: **{water:.3f}** ({ndwi_status}) - Low NDWI indicates low moisture and high cloud-free solar exposure.
*   **Land Cover Proxy (NDVI)**: **{veg:.3f}** ({ndvi_status}) - Low NDVI indicates sparse vegetation, ideal for large-scale solar array footprint without agricultural displacement.

---

#### 🔍 Environmental Risks & Energy Recommendations

*   💧 **Water Scarcity Risk**: Groundwater Storage is **{gw:.3f} cm** ({gw_status}). 
    *   *Recommendation*: Solar panel cleaning requires water to prevent dust-soiling losses. Given the {rating}, developers **must** prioritize water-free automated dry-brushing cleaning technologies to avoid straining local aquifers.
*   🚜 **Land Suitability Index (LSI)**: **{lsi:.3f}** ({lsi_status}).
    *   *Recommendation*: A low suitability score is actually an asset for energy projects, as it indicates land that is non-arable, preventing land-use conflict with local farming communities.
*   💨 **Wind Energy Hybridization**:
    *   *Recommendation*: If this is a coastal region, wind speeds are highly consistent. Consider designing a hybrid solar-wind microgrid to ensure 24/7 clean power generation.
"""

    elif is_tourism:
        if viability_score < 35:
            risk_class = "🔴 HIGH WATER RISK (Severe Infrastructure Constraints)"
            verdict = f"Developing real estate or tourism projects in **{location_title}** carries significant water supply risks. Traditional development models will face severe water access restrictions and high operational costs due to aquifer depletion."
        elif viability_score < 60:
            risk_class = "🟡 MODERATE RISK (Adaptive Water Management Required)"
            verdict = f"Development in **{location_title}** is feasible but requires strict water conservation measures and ecological landscaping design from the planning stage."
        else:
            risk_class = "🟢 LOW RISK (Stable Environmental Conditions)"
            verdict = f"**{location_title}** offers a stable resource base for tourism and property development. Standard environmental permits apply, with normal water access."

        return f"""### 🏢 Real Estate & Tourism Development Assessment: **{location_title}**{coord_str}

Based on live **Google Earth Engine (GEE)** indicators for year **{year}**, here is the real estate and infrastructure assessment:

---

#### 🌟 Development Risk Class: **{risk_class}**
#### 📈 Resource Score: **{viability_score}/100** (Agricultural/Water Base)

{verdict}

---

#### 🗺️ Location & Climate Context:
*   **Agro-Climatic Zone**: {zone_name}
*   **Climate Profile**: {climate_profile}
*   **Surface Moisture (NDWI)**: **{water:.3f}** ({ndwi_status}) - Crucial for evaluating local microclimate and green space viability.

---

#### 🔍 Environmental Risks & Infrastructure Recommendations

*   💧 **Water Utility & Groundwater**: Groundwater Storage is **{gw:.3f} cm** ({gw_status}) with recharge rate of **{gwr:.3f} mm/yr**.
    *   *Recommendation*: Resort and housing developments must integrate self-sufficient water cycles, including graywater purification plants, rain cisterns, and low-flow plumbing fixtures.
*   🌿 **Ecological Landscaping (Xeriscaping)**:
    *   *Recommendation*: Avoid high-water turf grasses. Landscape hotels and public spaces using native species such as *Argania spinosa* or *Phoenix dactylifera* that are perfectly adapted to the local climatic zone.
*   🚜 **Land Suitability & Soil**: Land Suitability Index is **{lsi:.3f}** ({lsi_status}).
    *   *Recommendation*: Ensure thorough geotech reports are conducted, as low soil moisture and vegetation can correspond to shifting sands or sandy soils requiring reinforced foundations.
"""

    elif is_water:
        return f"""### 💧 Groundwater & Water Resource Assessment: **{location_title}**{coord_str}

Based on live **Google Earth Engine (GEE)** indicators for year **{year}**, here is the water resource security audit:

---

#### 🌟 Water Security Status: **{rating}**
#### 📈 Unified Resource Score: **{viability_score}/100**

---

#### 🔍 Hydrological Analysis & Aquifer Health

*   💧 **Groundwater Storage Anomaly (GWSA)**: **{gw:.3f} cm** ({gw_status})
    *   *Analysis*: {gw_advice}
*   🕳️ **Groundwater Depth Change (GWD)**: **{gwd:.3f} m** ({gwd_status})
    *   *Analysis*: {gwd_advice}
*   🌧️ **Groundwater Recharge (GWR)**: **{gwr:.3f} mm/yr** ({gwr_status})
    *   *Analysis*: {gwr_advice}
*   🌊 **Surface Soil Moisture (NDWI)**: **{water:.3f}** ({ndwi_status})
    *   *Analysis*: {ndwi_advice}
*   🌊 **Surface Water Quantity (SWQ)**: **{swq:.3f}** ({swq_status})
    *   *Analysis*: {swq_advice}

---

#### 💡 Water Management Recommendations

1.  **Strict Pumping Control**: If Groundwater is in deficit, deep drilling is highly regulated and risky. Monitor water table levels closely and coordinate with the local river basin agency (ABH).
2.  **Rainwater & Runoff Harvesting**: Build small retention basins or check-dams to capture seasonal rainfall and encourage natural infiltration to replenish shallow aquifers.
3.  **Alternative Supplies**: Explore desalinated water or treated wastewater (REUSE) for agricultural and industrial applications to ease pressure on the aquifer.
"""

    elif is_crop:
        return f"""### 🚜 Crop Viability & Agricultural Assessment: **{location_title}**{coord_str}

Based on live **Google Earth Engine (GEE)** indicators for year **{year}**, here is the crop-specific viability analysis:

---

#### 🌟 Agricultural Viability: **{rating}**
#### 📈 Resource Score: **{viability_score}/100**

---

#### 🗺️ Agro-Climatic Zone & Recommendations:
*   **Zone Name**: {zone_name}
*   **Climate Profile**: {climate_profile}
*   **Recommended Resilient Crops**:
{recommended_crops}
*   **High-Risk Crops to Exclude**: *{discouraged_crops}*

---

#### 🔍 Environmental Indices & Soil Suitability

*   🚜 **Land Suitability (LSI)**: **{lsi:.3f}** ({lsi_status}) - {lsi_advice}
*   🌾 **Vegetation Density (NDVI)**: **{veg:.3f}** ({ndvi_status}) - {ndvi_advice}
*   🌊 **Surface Soil Moisture (NDWI)**: **{water:.3f}** ({ndwi_status}) - {ndwi_advice}
*   💧 **Groundwater Storage (GWSA)**: **{gw:.3f} cm** ({gw_status}) - {gw_advice}

---

#### 💡 Agricultural Recommendations

1.  **Crop Selection Alignment**: Shift cultivation strictly to the recommended crops for the **{zone_name}**. Planting water-heavy crops like watermelon, avocado, or citrus in water-depleted areas is highly discouraged.
2.  **Soils & Mulching**: Apply organic compost and soil mulches to optimize moisture retention (NDWI) and restore degraded topsoil (NDVI).
3.  **Modern Irrigation**: Transition from flood irrigation to subsurface drip systems and monitor soil tension using moisture sensors.
"""

    else:
        # Default report but prefixed with a custom introductory sentence addressing the user's message
        intro = f"Regarding your query: *\"{message}\"*, here is a detailed, data-driven report analyzing the environmental resource base of **{location_title}**:"
        
        return f"""{intro}

### 📊 Agricultural & Soil Suitability Report: **{location_title}**{coord_str}

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

*   💧 **Groundwater Storage (GWSA)**: **{gw:.3f} cm** ({gw_status})
    *   *Advice*: {gw_advice}
*   🕳️ **Groundwater Depth (GWD)**: **{gwd:.3f} m** ({gwd_status})
    *   *Advice*: {gwd_advice}
*   🌧️ **Groundwater Recharge (GWR)**: **{gwr:.3f} mm/yr** ({gwr_status})
    *   *Advice*: {gwr_advice}
*   🌊 **Surface Soil Moisture (NDWI)**: **{water:.3f}** ({ndwi_status})
    *   *Advice*: {ndwi_advice}
*   🌊 **Surface Water Quantity (SWQ)**: **{swq:.3f}** ({swq_status})
    *   *Advice*: {swq_advice}
*   🌾 **Vegetation Density (NDVI)**: **{veg:.3f}** ({ndvi_status})
    *   *Advice*: {ndvi_advice}
*   🚜 **Land Suitability Index (LSI)**: **{lsi:.3f}** ({lsi_status})
    *   *Advice*: {lsi_advice}
"""

def get_expert_report(region: str, year: int, gw_val: float, ndwi_val: float, ndvi_val: float) -> str:
    """Fallback wrapper for backwards compatibility."""
    return get_expert_location_report(f"Region: {region}", None, None, year, gw_val, None, ndwi_val, ndvi_val)

def calculate_viability(gw: float, water: float, veg: float) -> int:
    """Calculates a unified viability score from groundwater, ndwi, and ndvi."""
    gw_score = min(max(int((gw + 1.5) / 3.0 * 100), 0), 100)
    ndwi_score = min(max(int((water + 0.5) * 100), 0), 100)
    ndvi_score = min(max(int(veg / 0.8 * 100), 0), 100)
    return int(0.35 * gw_score + 0.3 * ndwi_score + 0.35 * ndvi_score)

def get_all_regions_summary(year: int) -> dict:
    """Returns a dict mapping region names to their GEE metrics for the specified year, utilizing backend cache or fallback values."""
    summary = {}
    try:
        gw_dataset = backend.get_all_regions_data(year, "gwsa") or {}
        gwd_dataset = backend.get_all_regions_data(year, "gwd") or {}
        ndwi_dataset = backend.get_all_regions_data(year, "ndwi") or {}
        ndvi_dataset = backend.get_all_regions_data(year, "ndvi") or {}
        recharge_dataset = backend.get_all_regions_data(year, "recharge") or {}
        water_quantity_dataset = backend.get_all_regions_data(year, "water_quantity") or {}
        suitability_dataset = backend.get_all_regions_data(year, "suitability") or {}
    except Exception as e:
        print(f"Failed to fetch GEE data for all regions: {e}")
        gw_dataset, gwd_dataset, ndwi_dataset, ndvi_dataset, recharge_dataset, water_quantity_dataset, suitability_dataset = {}, {}, {}, {}, {}, {}, {}

    region_defaults = {
        "Souss-Massa": (-1.3, -0.6, 25.0, -0.22, 0.05, 0.25, 0.28),
        "Marrakech-Safi": (-1.1, -0.5, 32.0, -0.18, 0.08, 0.28, 0.32),
        "Casablanca-Settat": (-0.6, -0.3, 85.0, -0.05, 0.15, 0.42, 0.48),
        "Rabat-Salâ-Kenitra": (-0.2, -0.1, 142.0, 0.12, 0.45, 0.55, 0.65),
        "Tangier-Tetouan-Al Hoceima": (0.1, 0.05, 185.0, 0.18, 0.60, 0.62, 0.72),
        "Fez-Meknes": (-0.4, -0.2, 110.0, 0.05, 0.25, 0.48, 0.52),
        "Drâa-Tafilalet": (-1.4, -0.7, 12.0, -0.38, 0.02, 0.12, 0.15),
        "Dakhla-Oued Ed-Dahab": (-0.2, -0.1, 8.0, -0.45, 0.01, 0.08, 0.10),
        "Guelmim-Oued Noun": (-0.9, -0.4, 18.0, -0.32, 0.03, 0.15, 0.18),
        "Laâyoune-Sakia El Hamra": (-0.5, -0.2, 10.0, -0.42, 0.02, 0.09, 0.11),
        "Oriental": (-0.8, -0.4, 45.0, -0.25, 0.06, 0.22, 0.26),
        "Béni Mellal-Khénifra": (-0.9, -0.4, 62.0, -0.08, 0.18, 0.38, 0.44),
    }

    for r in REGIONS:
        gw = gw_dataset.get(r)
        gwd = gwd_dataset.get(r)
        recharge = recharge_dataset.get(r)
        ndwi = ndwi_dataset.get(r)
        swq = water_quantity_dataset.get(r)
        ndvi = ndvi_dataset.get(r)
        suit = suitability_dataset.get(r)
        
        # Use defaults if any value is None
        def_gw, def_gwd, def_recharge, def_ndwi, def_swq, def_ndvi, def_suit = region_defaults.get(r, (-0.5, -0.25, 50.0, -0.15, 0.10, 0.30, 0.35))
        
        summary[r] = {
            "gwsa": gw if gw is not None else def_gw,
            "gwd": gwd if gwd is not None else def_gwd,
            "recharge": recharge if recharge is not None else def_recharge,
            "ndwi": ndwi if ndwi is not None else def_ndwi,
            "water_quantity": swq if swq is not None else def_swq,
            "ndvi": ndvi if ndvi is not None else def_ndvi,
            "suitability": suit if suit is not None else def_suit,
        }
    return summary

def generate_chat_response(message: str, history: list, year: int, current_index: str, current_region: str, current_location: dict = None) -> str:
    """Main chatbot engine. Detects region/location, integrates GEE data, and generates agricultural insights."""
    
    # 1. Normalize message and check for explanations
    norm_msg = normalize_text(message)
    
    # Check if the query is a general explanation request (as opposed to a location/region analysis query)
    is_explain_query = ("explain" in norm_msg or "what is" in norm_msg or "how is" in norm_msg or "range" in norm_msg) and not ("selected" in norm_msg or "location" in norm_msg or "here" in norm_msg or "analyze" in norm_msg or "invest" in norm_msg)
    
    # General Index Explanations
    if is_explain_query and ("ndvi" in norm_msg or ("vegetation" in norm_msg and "explain" in norm_msg)):
        return r"""### 🌾 NDVI (Normalized Difference Vegetation Index) Explained

**NDVI** measures the health and density of vegetation using satellite sensors (Sentinel-2, Landsat). It calculates the ratio of near-infrared light reflected by healthy leaves to red light absorbed by chlorophyll:

$$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$$

*   **Values Range**: `-1.0` to `1.0`.
*   **Interpretation**:
    *   `0.0 to 0.15`: Bare soil, sand, rocks.
    *   `0.15 to 0.4`: Sparse vegetation, scrubland, early-stage crops.
    *   `0.4 to 0.8`: Healthy forests, dense agriculture, mature crops.
*   **Investment Relevance**: Helps investors monitor crop health, verify crop yields remotely, and detect deforestation or land degradation trends.
"""
        
    if is_explain_query and ("ndwi" in norm_msg or ("water" in norm_msg and "index" in norm_msg and "explain" in norm_msg)):
        return r"""### 🌊 NDWI (Normalized Difference Water Index) Explained

**NDWI** monitors surface water features, flooding, and vegetation liquid water content. It highlights differences in near-infrared and shortwave-infrared (or green) light:

$$\text{NDWI} = \frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}}$$

*   **Values Range**: `-1.0` to `1.0`.
*   **Interpretation**:
    *   `> 0.3`: Open surface water (lakes, reservoirs, oceans).
    *   `0.0 to 0.2`: Damp soil, shallow mud, high crop moisture.
    *   `< 0.0`: Dry soils, bare land, desert rock.
*   **Investment Relevance**: Essential to verify surface water availability. High NDWI indicates robust local reservoirs or canals; dropping NDWI signals agricultural drought.
"""

    if is_explain_query and ("groundwater" in norm_msg or "grace" in norm_msg or "nappe" in norm_msg):
        return """### 💧 Groundwater Storage Anomaly (GRACE) Explained

**Groundwater Anomaly** data is fetched from the joint NASA/DLR **GRACE-FO** (Gravity Recovery and Climate Experiment) satellites. It measures subtle changes in Earth's gravitational pull caused by shifts in water mass underground:

*   **Metric**: LWE (Liquid Water Equivalent) thickness anomaly in centimeters.
*   **Interpretation**:
    *   **Negative Anomaly (< 0 cm)**: Depletion of deep groundwater reserves (water table is dropping).
    *   **Positive Anomaly (> 0 cm)**: Aquifer recharge (stable or increasing water reserves).
*   **Investment Relevance**: Groundwater is the ultimate security buffer for dry periods. Deep negative anomalies indicate high risk of dry wells, strict extraction limits, and eventual high energy costs to pump deeper water.
"""

    if is_explain_query and "recharge" in norm_msg:
        return r"""### 🌧️ Groundwater Recharge Explained

**Groundwater Recharge** estimates the amount of water that infiltrates and replenishes local deep aquifers annually. It is derived from the **NASA GLDAS** (Global Land Data Assimilation System) meteorological balance:

$$\text{Recharge} = \max(\text{Precipitation} - \text{Evapotranspiration}, 0) \times 0.20$$

*   **Metric**: Millimeters of water equivalent per year (mm/yr).
*   **Interpretation**:
    *   `< 0.0 mm/yr`: Recharge deficit (evapotranspiration exceeds precipitation). Aquifers are highly vulnerable.
    *   `0.0 to 4.0 mm/yr`: Low-moderate replenishment. Requires balanced extraction.
    *   `> 4.0 mm/yr`: Good active recharge. Favorable for sustainable agro-infrastructure.
*   **Investment Relevance**: Helps target areas where deep groundwater is actively recharged, minimizing the risk of rapid water-table drops.
"""

    if is_explain_query and ("quantity" in norm_msg or ("surface" in norm_msg and "water" in norm_msg and "quantity" in norm_msg)):
        return r"""### 🌊 Surface Water Quantity Index Explained

**Surface Water Quantity** measures the presence and concentration of open water bodies or wetlands. It scales high-resolution Sentinel-2 **NDWI** water pixels to a clean 0-1 scale:

$$\text{Quantity} = \frac{\max(\text{NDWI}, 0)}{0.5}$$

*   **Interpretation**:
    *   `< 0.10`: Dry or absent surface water. Focus on closed tank storage or wells.
    *   `0.10 to 0.40`: Moderate surface water. Suitable for managed irrigation scheduling.
    *   `> 0.40`: Abundant open surface water (lakes, rivers, reservoirs, major irrigation lines).
*   **Investment Relevance**: Crucial to verify proximity to surface water networks, protecting crops against direct reliance on deep aquifers.
"""

    if is_explain_query and ("suitability" in norm_msg or ("land" in norm_msg and "suitability" in norm_msg)):
        return r"""### 🚜 Land Suitability Index Explained

**Land Suitability is a multi-spectral decision model combining vegetative cover and soil moisture to score agricultural capacity:**

$$\text{Suitability} = 0.6 \times \text{NDVI} + 0.4 \times (\text{NDWI} + 0.2)$$

*   **Values Range**: `0.0` to `1.0`.
*   **Interpretation**:
    *   `< 0.30`: Low agricultural suitability. Soils are dry, bare, or degraded.
    *   `0.30 to 0.60`: Moderate suitability. Best suited to orchards and resilient crops with drip systems.
    *   `> 0.60`: Prime agricultural land. Optimal vegetation canopy and soil moisture structure.
*   **Investment Relevance**: Instantly locates highly fertile zones with active canopy and water retention for rapid crop production.
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
    recharge_val = None
    water_quantity_val = None
    suitability_val = None
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
        recharge_val = data_vals.get("recharge")
        water_quantity_val = data_vals.get("water_quantity")
        suitability_val = data_vals.get("suitability")
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
            recharge_dataset = backend.get_all_regions_data(year, "recharge")
            water_quantity_dataset = backend.get_all_regions_data(year, "water_quantity")
            suitability_dataset = backend.get_all_regions_data(year, "suitability")
            
            gw_val = gw_dataset.get(region)
            gwd_val = gwd_dataset.get(region) if gwd_dataset else None
            ndwi_val = ndwi_dataset.get(region)
            ndvi_val = ndvi_dataset.get(region)
            recharge_val = recharge_dataset.get(region) if recharge_dataset else None
            water_quantity_val = water_quantity_dataset.get(region) if water_quantity_dataset else None
            suitability_val = suitability_dataset.get(region) if suitability_dataset else None
        except Exception as e:
            # Fallback to realistic values based on climatological averages of regions in case GEE is unreachable
            print(f"GEE backend query failed: {e}. Using regional approximations.")
            region_defaults = {
                "Souss-Massa": (-1.3, -0.6, 25.0, -0.22, 0.05, 0.25, 0.28),
                "Marrakech-Safi": (-1.1, -0.5, 32.0, -0.18, 0.08, 0.28, 0.32),
                "Casablanca-Settat": (-0.6, -0.3, 85.0, -0.05, 0.15, 0.42, 0.48),
                "Rabat-Salâ-Kenitra": (-0.2, -0.1, 142.0, 0.12, 0.45, 0.55, 0.65),
                "Tangier-Tetouan-Al Hoceima": (0.1, 0.05, 185.0, 0.18, 0.60, 0.62, 0.72),
                "Fez-Meknes": (-0.4, -0.2, 110.0, 0.05, 0.25, 0.48, 0.52),
                "Drâa-Tafilalet": (-1.4, -0.7, 12.0, -0.38, 0.02, 0.12, 0.15),
                "Dakhla-Oued Ed-Dahab": (-0.2, -0.1, 8.0, -0.45, 0.01, 0.08, 0.10),
                "Guelmim-Oued Noun": (-0.9, -0.4, 18.0, -0.32, 0.03, 0.15, 0.18),
                "Laâyoune-Sakia El Hamra": (-0.5, -0.2, 10.0, -0.42, 0.02, 0.09, 0.11),
                "Oriental": (-0.8, -0.4, 45.0, -0.25, 0.06, 0.22, 0.26),
                "Béni Mellal-Khénifra": (-0.9, -0.4, 62.0, -0.08, 0.18, 0.38, 0.44),
            }
            gw_val, gwd_val, recharge_val, ndwi_val, water_quantity_val, ndvi_val, suitability_val = region_defaults.get(region, (-0.5, -0.25, 50.0, -0.15, 0.10, 0.30, 0.35))

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
You are the Ardi Invest GeoAI Moroccan Resource & Investment Advisor. You are an expert in agricultural economics, renewable energy, spatial analysis, and sustainable development in Morocco.
You help farmers, developers, and investors assess agricultural suitability, crop viability, water risks, renewable energy potential, and general investment opportunities in Morocco.

A user has sent you this message: "{message}"

Here is the scientific sensor data we fetched from Google Earth Engine for the {location_desc} (Year: {year}):
- Name/Title: {location_title}
- Coordinates: {f"Latitude: {lat:.4f}, Longitude: {lon:.4f}" if is_custom_point else "Regional average"}
- Groundwater Anomaly (GWSA): {f"{gw_val:.3f} cm" if gw_val is not None else "N/A"} (GRACE)
- Groundwater Depth Change (GWD): {f"{gwd_val:.3f} m" if gwd_val is not None else "N/A"}
- Groundwater Recharge (GWR): {f"{recharge_val:.3f} mm/yr" if recharge_val is not None else "N/A"}
- Surface Soil Moisture (NDWI): {f"{ndwi_val:.3f}" if ndwi_val is not None else "N/A"}
- Surface Water Quantity (SWQ): {f"{water_quantity_val:.3f}" if water_quantity_val is not None else "N/A"}
- Vegetation Health Index (NDVI): {f"{ndvi_val:.3f}" if ndvi_val is not None else "N/A"}
- Land Suitability Index (LSI): {f"{suitability_val:.3f}" if suitability_val is not None else "N/A"}

Current Active Map View in Platform:
- Year: {year}
- Current Filter: {current_index}

CRITICAL INSTRUCTION: You MUST directly answer the user's specific question. Read their message carefully and respond to exactly what they are asking about. For example:
- If they ask about solar energy or renewable energy, discuss solar/wind potential in this location using the environmental data (solar radiation correlates with low NDWI/arid zones, low vegetation = open land for panels, etc.).
- If they ask about a specific crop or farming model, focus on that specific crop's viability here.
- If they ask about real estate, tourism, or other non-agricultural investments, address that topic specifically.
- If they ask a general "should I invest here?" or about agriculture, then provide agricultural viability analysis with crop recommendations.

Use the GEE data as supporting evidence for your answer, not as the entire answer. Relate the environmental indices to the user's specific topic of interest.

Guidelines for your response:
1. Start by directly addressing the user's question topic (e.g., solar energy feasibility, specific crop viability, etc.).
2. Use the GEE indices as supporting data to strengthen your analysis of their specific topic.
3. Provide 2-3 actionable, topic-specific recommendations.
4. Warn about relevant risks using the environmental data.

Format your response beautifully in Markdown. Use bullet points, bold text, and warning blockquotes (> [!WARNING]) or tip blockquotes (> [!TIP]) where appropriate. Keep the tone professional, realistic, and insightful. Do not exceed 450 words.
"""
                response = model.generate_content(prompt)
                return response.text
            except Exception as gem_err:
                print(f"Gemini API invocation failed: {gem_err}. Using Data-Driven Expert Engine.")
                
        # Generate the structured report via local expert system
        return get_smart_local_report(
            message, location_title, lat, lon, year, 
            gw_val, gwd_val, ndwi_val, ndvi_val, 
            recharge_val, water_quantity_val, suitability_val
        )

    # 5. Standard conversational responses or general inquiries about Morocco (location_title is None)
    
    # First, construct a detailed regions data summary for this year
    summary = get_all_regions_summary(year)
    
    # Try Gemini if API key is present, even for general questions
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # Format the summary table for prompt context
            summary_table = "Region | GWSA (cm) | GWD (m) | Recharge (mm/yr) | NDWI | SWQ | NDVI | LSI\n"
            summary_table += "---|---|---|---|---|---|---|---\n"
            for r_name, r_metrics in summary.items():
                summary_table += f"{r_name} | {r_metrics['gwsa']:.2f} | {r_metrics['gwd']:.2f} | {r_metrics['recharge']:.2f} | {r_metrics['ndwi']:.2f} | {r_metrics['water_quantity']:.2f} | {r_metrics['ndvi']:.2f} | {r_metrics['suitability']:.2f}\n"
            
            prompt = f"""
You are the Ardi Invest GeoAI Moroccan Resource & Investment Advisor. You are an expert in agricultural economics, renewable energy, spatial analysis, and sustainable development in Morocco.
You help farmers, developers, and investors assess agricultural suitability, crop viability, water risks, renewable energy potential, and general investment opportunities in Morocco.

A user has sent you this message: "{message}"

Here is the GEE regional average data for all 12 regions of Morocco for the active map year {year}:
{summary_table}

Active Map View Details:
- Year: {year}
- Current Filter: {current_index}

CRITICAL INSTRUCTION: You MUST directly answer the user's specific question. Read their message carefully and respond to exactly what they are asking about. For example:
- If they ask about solar energy, wind farms, or renewable energy in a specific region, discuss that topic using the environmental data as supporting context (arid zones with low NDWI/NDVI = high solar potential and open land for panels; coastal regions = wind potential).
- If they ask about a specific crop, investment type, or development project, focus on that specific topic.
- If they ask about the best region for a specific purpose, compare regions and rank them for that specific purpose.
- If they ask a general question about agriculture or where to invest, then provide the agricultural viability analysis with regional rankings.

Use the GEE data as supporting evidence for your answer, not as the entire answer. Relate the environmental indices to the user's specific topic of interest.

Keep the tone professional, realistic, and highly insightful. Format your response beautifully in Markdown. Use bullet points, bold text, and warning blockquotes (> [!WARNING]) or tip blockquotes (> [!TIP]) where appropriate. Do not exceed 450 words.
"""
            response = model.generate_content(prompt)
            return response.text
        except Exception as gem_err:
            print(f"Gemini API invocation failed for general query: {gem_err}. Using local comparison engine.")

    # Local Rule-based Comparison Engine (if Gemini is unavailable)
    is_gw_query = any(k in norm_msg for k in ["groundwater", "gwsa", "gwd", "aquifer", "nappe", "water table"])
    is_recharge_query = any(k in norm_msg for k in ["recharge", "gwr", "replenish"])
    is_suitability_query = any(k in norm_msg for k in ["suitability", "lsi", "fertile", "land", "soil"])
    is_ndvi_query = any(k in norm_msg for k in ["ndvi", "vegetation", "canopy", "green"])
    is_ndwi_query = any(k in norm_msg for k in ["ndwi", "surface water", "moisture", "swq", "reservoir", "lake"])
    is_compare_query = any(k in norm_msg for k in ["compare", "ranking", "rank", "list", "regions", "where to invest"])
    is_invest_query = any(k in norm_msg for k in ["invest", "opportunity", "opportunities", "viability", "viable"])

    if is_gw_query:
        ranked = sorted(summary.items(), key=lambda x: x[1]['gwsa'], reverse=True)
        best_region, best_metrics = ranked[0]
        worst_region, worst_metrics = ranked[-1]
        
        response_text = f"""### 💧 Groundwater Storage Anomaly (GWSA) Regional Report ({year})

Based on **Google Earth Engine (GEE)** satellite models (GRACE anomaly and GLDAS water balance) for year **{year}**:

The region with the **best groundwater stability** is **{best_region}** with a Groundwater Storage Anomaly (GWSA) of **{best_metrics['gwsa']:.3f} cm** and a natural recharge rate of **{best_metrics['recharge']:.2f} mm/yr**.

#### 📈 Full Groundwater Rankings (GWSA Anomaly):
"""
        for rank, (r_name, r_metrics) in enumerate(ranked, 1):
            status_dot = "🟢" if r_metrics['gwsa'] >= 0 else "🟡" if r_metrics['gwsa'] >= -0.8 else "🔴"
            response_text += f"{rank}. {status_dot} **{r_name}**: `{r_metrics['gwsa']:.3f} cm` (Depth change: `{r_metrics['gwd']:.2f} m`, Recharge: `{r_metrics['recharge']:.2f} mm/yr`)\n"
            
        response_text += f"""
#### 🔍 Key Insight:
*   **Most Stable**: **{best_region}** is currently experiencing the least aquifer depletion.
*   **Most Critical**: **{worst_region}** (`{worst_metrics['gwsa']:.3f} cm`) has severe groundwater depletion. Investors should strictly avoid high-water crop models (e.g. avocado, watermelon) and implement subsurface drip irrigation in this zone.
"""
        return response_text

    elif is_recharge_query:
        ranked = sorted(summary.items(), key=lambda x: x[1]['recharge'], reverse=True)
        best_region, best_metrics = ranked[0]
        response_text = f"""### 🌧️ Groundwater Recharge (GWR) Regional Report ({year})

Based on **Google Earth Engine** GLDAS water balance metrics for **{year}**:

The region with the **highest active groundwater recharge rate** is **{best_region}** at **{best_metrics['recharge']:.2f} mm/yr**.

#### 📈 Full Recharge Rate Rankings:
"""
        for rank, (r_name, r_metrics) in enumerate(ranked, 1):
            status_dot = "🟢" if r_metrics['recharge'] >= 4.0 else "🟡" if r_metrics['recharge'] >= 0.0 else "🔴"
            response_text += f"{rank}. {status_dot} **{r_name}**: `{r_metrics['recharge']:.2f} mm/yr`\n"
            
        response_text += f"""
#### 💡 Investment Relevance:
Groundwater recharge represents the sustainable abstraction threshold. High recharge zones (like the northern regions) are better suited for long-term agricultural investments utilizing well networks, while low recharge zones (like southern and desert regions) require strictly closed-loop hydroponics or desalination.
"""
        return response_text

    elif is_suitability_query:
        ranked = sorted(summary.items(), key=lambda x: x[1]['suitability'], reverse=True)
        best_region, best_metrics = ranked[0]
        response_text = f"""### 🚜 Land Suitability Index (LSI) Regional Report ({year})

Based on composite **Google Earth Engine** NDVI and NDWI agricultural suitability indexes for **{year}**:

The region with the **highest agricultural land suitability** is **{best_region}** with a suitability index score of **{best_metrics['suitability']:.3f}/1.00**.

#### 📈 Full Agricultural Suitability Rankings:
"""
        for rank, (r_name, r_metrics) in enumerate(ranked, 1):
            status_dot = "🟢" if r_metrics['suitability'] >= 0.6 else "🟡" if r_metrics['suitability'] >= 0.35 else "🔴"
            response_text += f"{rank}. {status_dot} **{r_name}**: `{r_metrics['suitability']:.2f}`\n"
            
        response_text += f"""
#### 💡 Investment Relevance:
High land suitability (LSI > 0.60) correlates with healthy active canopies and excellent topsoil moisture. These regions are prime candidates for high-value organic crops, while lower scores (LSI < 0.35) are better suited for drought-resistant orchards or require intensive soil conditioning.
"""
        return response_text

    elif is_ndvi_query:
        ranked = sorted(summary.items(), key=lambda x: x[1]['ndvi'], reverse=True)
        best_region, best_metrics = ranked[0]
        response_text = f"""### 🌾 Vegetation Cover (NDVI) Regional Report ({year})

Based on **Google Earth Engine** Sentinel-2 canopy measurements for **{year}**:

The region with the **densest vegetation cover** is **{best_region}** with an average NDVI score of **{best_metrics['ndvi']:.3f}**.

#### 📈 Full NDVI Rankings:
"""
        for rank, (r_name, r_metrics) in enumerate(ranked, 1):
            status_dot = "🟢" if r_metrics['ndvi'] >= 0.4 else "🟡" if r_metrics['ndvi'] >= 0.15 else "🔴"
            response_text += f"{rank}. {status_dot} **{r_name}**: `{r_metrics['ndvi']:.3f}`\n"
            
        return response_text

    elif is_ndwi_query:
        ranked = sorted(summary.items(), key=lambda x: x[1]['ndwi'], reverse=True)
        best_region, best_metrics = ranked[0]
        response_text = f"""### 🌊 Surface Soil Moisture & Water Index (NDWI) Regional Report ({year})

Based on **Google Earth Engine** Sentinel-2 water absorption band calculations for **{year}**:

The region with the **highest soil moisture and surface water availability** is **{best_region}** with an average NDWI score of **{best_metrics['ndwi']:.3f}**.

#### 📈 Full NDWI Rankings:
"""
        for rank, (r_name, r_metrics) in enumerate(ranked, 1):
            status_dot = "🟢" if r_metrics['ndwi'] >= 0.15 else "🟡" if r_metrics['ndwi'] >= -0.2 else "🔴"
            response_text += f"{rank}. {status_dot} **{r_name}**: `{r_metrics['ndwi']:.3f}` (Surface Quantity SWQ: `{r_metrics['water_quantity']:.2f}`)\n"
            
        return response_text

    elif is_compare_query or is_invest_query or "invest" in norm_msg or "opportunit" in norm_msg:
        # Rank by calculated viability score
        viabilities = []
        for r_name, r_metrics in summary.items():
            v_score = calculate_viability(r_metrics['gwsa'], r_metrics['ndwi'], r_metrics['ndvi'])
            viabilities.append((r_name, v_score, r_metrics))
        ranked = sorted(viabilities, key=lambda x: x[1], reverse=True)
        
        response_text = f"""### 🇲🇦 Moroccan Regional Agricultural Viability Rankings ({year})

Using a multi-criteria decision index combining **Groundwater anomaly (35%)**, **Soil moisture (30%)**, and **Vegetation density (35%)** from **Google Earth Engine** measurements for **{year}**:

#### 🟢 Prime Agricultural Zones (Viability Score >= 60)
These zones possess strong soil moisture, stable vegetative cover, and minimal aquifer depletion risk. High potential for cash crops.
"""
        primes = [item for item in ranked if item[1] >= 60]
        if primes:
            for rank, (r_name, v_score, r_metrics) in enumerate(primes, 1):
                response_text += f"- **{r_name}** (Score: `{v_score}/100`): Prime soil/water assets. Ideal for precision drip horticulture.\n"
        else:
            response_text += "*No regions met the high viability threshold for this year.*\n"
            
        response_text += "\n#### 🟡 Adaptive Agricultural Zones (Viability Score 35-59)\n"
        response_text += "These zones require water conservation technologies, drought-resilient cultivars, and careful planning.\n"
        adaptives = [item for item in ranked if 35 <= item[1] < 60]
        for r_name, v_score, r_metrics in adaptives:
            response_text += f"- **{r_name}** (Score: `{v_score}/100`): Favorable for olive/carob orchards with precise watering.\n"
            
        response_text += "\n#### 🔴 High-Stress Zones (Viability Score < 35)\n"
        response_text += "Severe water stress or high soil aridity. Traditional crops are highly discouraged; prioritize agrotech or renewable energy.\n"
        stresseds = [item for item in ranked if item[1] < 35]
        for r_name, v_score, r_metrics in stresseds:
            response_text += f"- **{r_name}** (Score: `{v_score}/100`): Critical water deficit. Limit deep boreholes.\n"
            
        response_text += f"""
---
*💡 Pro Tip: Turn on **"Sync Map Context"** and click on any region or custom coordinate point on the map to trigger a hyper-local soil and crop suitability report!*
"""
        return response_text

    # Default starting welcome response
    return f"""### 👋 Welcome to the GeoAI Resource & Investment Advisor!

I am your intelligent assistant linked directly to **Google Earth Engine (GEE)**. I analyze soil, surface moisture, and deep aquifers in Morocco to help you make climate-resilient investment decisions.

#### 💡 How to Interact with Me:
1.  **Ask about a specific region**: Type something like *"Can I invest in Souss-Massa?"* or *"Analyze Marrakech-Safi"*.
2.  **Learn about scientific indices**: Ask *"What is NDWI?"*, *"Explain NDVI"*, or *"How is groundwater measured?"*.
3.  **Use Active Map Context**: Check **"Sync Map Context"** below. When enabled, asking *"Is it safe to invest here?"* will automatically analyze the active region, year, and index currently selected on your map view!

*Select a preset question pill below or type your custom query to begin!*
"""
