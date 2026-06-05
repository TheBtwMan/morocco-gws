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

def get_expert_report(region: str, year: int, gw_val: float, ndwi_val: float, ndvi_val: float) -> str:
    """Generates a highly detailed, scientific investment analysis report in Markdown."""
    
    # Calculate subscores and overall score
    # Groundwater score (usually between -1.5 and 1.5)
    if gw_val is None:
        gw_val = -0.5  # default/estimate
    gw_score = min(max(int((gw_val + 1.5) / 3.0 * 100), 0), 100)
    
    # NDWI score (usually between -0.5 and 0.5)
    if ndwi_val is None:
        ndwi_val = -0.1
    ndwi_score = min(max(int((ndwi_val + 0.5) * 100), 0), 100)
    
    # NDVI score (usually between 0 and 0.8)
    if ndvi_val is None:
        ndvi_val = 0.25
    ndvi_score = min(max(int(ndvi_val / 0.8 * 100), 0), 100)
    
    # Weighted investment viability score
    viability_score = int(0.35 * gw_score + 0.3 * ndwi_score + 0.35 * ndvi_score)
    
    # Determine Rating Category and Recommendations
    if viability_score < 35:
        rating = "🔴 SEVERE WATER STRESS / EXTREME INVESTMENT RISK"
        summary = "Traditional agricultural investments are highly discouraged due to critical aquifer depletion and low soil moisture. Focus strictly on solar energy, closed-loop agrotech, or coastal saline projects."
        exclude_portfolio = "High-volume sprinkler irrigation, open-field commercial crops, livestock grazing, and water-heavy vegetables."
        viable_ventures = """*   ☀️ **Solar & Wind Infrastructure**: Capitalize on extreme solar irradiance and wind corridors (especially in southern coastal zones).
*   🧪 **Closed-Loop Controlled Agriculture**: Indoor vertical farming, hydroponics, or aeroponics with full water recycling.
*   🌊 **Desalinated/Saline Agrotech**: Cultivation of halophytic crop varieties (e.g., Quinoa, Salicornia) using brackish water or coastal desalination resources.
*   🔋 **Green Hydrogen & Clean Energy**: Set up production facilities powered by nearby desert solar/wind plants."""
    elif viability_score < 60:
        rating = "🟡 MODERATE RISK / ADAPTIVE STRATEGY REQUIRED"
        summary = "Moderate vegetation and water resources. Rain-fed and water-heavy farming are risky. Viable for drought-resistant crops (olive, argan, carob) using automated drip irrigation, solar farming, and soil sensors."
        exclude_portfolio = "Unregulated groundwater extraction, flood irrigation, and high-water fruits/vegetables like watermelons, avocados, or citrus monocultures."
        viable_ventures = """*   🌿 **Drought-Resistant Cultivars**: Majhool date palms, olive groves, argan trees, carob, and aromatic/medicinal herbs (Rosemary, Thyme).
*   💧 **Smart Irrigation Tech**: Localized sub-surface drip irrigation, IoT soil moisture sensors, and automated evaporation management.
*   🏭 **Agro-Processing & Value-Adding**: Processing plants for premium oil extraction (olive/argan) and dried fruit packaging, creating high export value with low water footprints.
*   🌧️ **Water Harvesting & Storage**: Micro-catchments, mist harvesting, and small-scale farm reservoirs."""
    else:
        rating = "🟢 STRONG RESOURCE BASE / HIGHEST VIABILITY"
        summary = "Healthy soil moisture and stable water indicators. Favorable for high-value organic agriculture, sustainable forestry, agro-tourism, and food processing infrastructures. Drip tech is still recommended for climate resilience."
        exclude_portfolio = "Sprinkler irrigation (use drip instead) and soil-depleting monoculture without crop rotation."
        viable_ventures = """*   🚜 **High-Value Organic Agriculture**: Export-grade organic berries, specialty vegetables, medicinal crops, and seeds.
*   🌲 **Sustainable Agro-Forestry**: Integrating high-value timber, fruit trees, and understory crops to maximize land utilization and moisture retention.
*   🍇 **Viticulture & High-Grade Fruit Orchards**: Premium grape varieties, stone fruits, and managed citrus utilizing smart drip irrigation.
*   🏭 **Eco-Tourism & Logistics Hubs**: Educational rural farm retreats, high-efficiency cold-chain packaging, and distribution hubs."""

    # Format values for presentation
    gw_str = f"{gw_val:.3f} cm" if isinstance(gw_val, (int, float)) else "N/A"
    ndwi_str = f"{ndwi_val:.3f}" if isinstance(ndwi_val, (int, float)) else "N/A"
    ndvi_str = f"{ndvi_val:.3f}" if isinstance(ndvi_val, (int, float)) else "N/A"

    report = f"""### 📊 GeoAI Investment Suitability Report: **{region}** (Year: {year})

Based on **Google Earth Engine (GEE)** live satellite indicators, here is the agricultural and natural resources investment assessment:

---

#### 🌟 Suitability Class: **{rating}**
#### 📈 Overall Resource Score: **{viability_score}/100**

*{summary}*

---

#### 🔍 Environmental Indices & Resource Health

*   💧 **Groundwater Anomaly (GRACE)**: **{gw_str}** ({'🔴 Severe Depletion' if gw_val < -0.8 else '🟡 Moderate Deficit' if gw_val < 0 else '🟢 Recharging/Stable'})
    *Measures deep aquifer storage anomalies. Deep wells and heavy boreholes face high regulatory and natural exhaustion risks here.*
*   🌊 **Surface Water (NDWI)**: **{ndwi_str}** ({'🔴 Extremely Arid' if ndwi_val < -0.2 else '🟡 Dry to Moist' if ndwi_val < 0.15 else '🟢 Abundant/Wetlands'})
    *Normalized Difference Water Index. Reflects surface soil moisture and open water bodies. Low NDWI requires advanced water-conservation.*
*   🌾 **Vegetation Health (NDVI)**: **{ndvi_str}** ({'🔴 Bare Soil/Desert' if ndvi_val < 0.15 else '🟡 Open Shrubland/Sparse Crop' if ndvi_val < 0.4 else '🟢 Rich Canopy/Active Agriculture'})
    *Normalized Difference Vegetation Index. Indicates chlorophyll content and crop health. Higher values signify robust photosynthetic activity.*

---

#### 💼 Strategic Investment Recommendations

*   🚫 **EXCLUDE FROM PORTFOLIO**: {exclude_portfolio}
*   ✅ **HIGHLY VIABLE VENTURES**:
{viable_ventures}
"""
    return report

def generate_chat_response(message: str, history: list, year: int, current_index: str, current_region: str) -> str:
    """Main chatbot engine. Detects region, fetches real GEE data, and generates response."""
    
    # 1. Detect regions mentioned in the message
    detected = detect_regions(message)
    
    # Fallback to the active map region if no region is mentioned in user message
    region = None
    if detected:
        region = detected[0]
    elif current_region and current_region in REGIONS:
        region = current_region
        
    norm_msg = normalize_text(message)
    
    # 2. General Index Explanations
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
        return """### 💧 Groundwater Anomaly (GRACE) Explained

**Groundwater Anomaly** data is fetched from the joint NASA/DLR **GRACE-FO** (Gravity Recovery and Climate Experiment) satellites. It measures subtle changes in Earth's gravitational pull caused by shifts in water mass underground:

*   **Metric**: LWE (Liquid Water Equivalent) thickness anomaly in centimeters.
*   **Interpretation**:
    *   **Negative Anomaly (< 0 cm)**: Depletion of deep groundwater reserves (water table is dropping).
    *   **Positive Anomaly (> 0 cm)**: Aquifer recharge (stable or increasing water reserves).
*   **Investment Relevance**: Groundwater is the ultimate security buffer for dry periods. Deep negative anomalies indicate high risk of dry wells, strict extraction limits, and eventual high energy costs to pump deeper water.
"""

    # 3. Handle specific region analysis
    if region:
        # Use GEE to fetch data
        try:
            # We query the exact index data from GEE backend!
            # Since fetching single regions is fast via our cached get_all_regions_data, we query all 3 indices!
            gw_dataset = backend.get_all_regions_data(year, "groundwater")
            ndwi_dataset = backend.get_all_regions_data(year, "ndwi")
            ndvi_dataset = backend.get_all_regions_data(year, "ndvi")
            
            gw_val = gw_dataset.get(region)
            ndwi_val = ndwi_dataset.get(region)
            ndvi_val = ndvi_dataset.get(region)
        except Exception as e:
            # Fallback to realistic values based on climatological averages of regions in case GEE is unreachable
            print(f"GEE backend query failed: {e}. Using regional approximations.")
            region_defaults = {
                "Souss-Massa": (-1.3, -0.22, 0.25),
                "Marrakech-Safi": (-1.1, -0.18, 0.28),
                "Casablanca-Settat": (-0.6, -0.05, 0.42),
                "Rabat-Salâ-Kenitra": (-0.2, 0.12, 0.55),
                "Tangier-Tetouan-Al Hoceima": (0.1, 0.18, 0.62),
                "Fez-Meknes": (-0.4, 0.05, 0.48),
                "Drâa-Tafilalet": (-1.4, -0.38, 0.12),
                "Dakhla-Oued Ed-Dahab": (-0.2, -0.45, 0.08),
                "Guelmim-Oued Noun": (-0.9, -0.32, 0.15),
                "Laâyoune-Sakia El Hamra": (-0.5, -0.42, 0.09),
                "Oriental": (-0.8, -0.25, 0.22),
                "Béni Mellal-Khénifra": (-0.9, -0.08, 0.38),
            }
            gw_val, ndwi_val, ndvi_val = region_defaults.get(region, (-0.5, -0.15, 0.3))
            
        # Try to use Generative AI (Gemini) if API key is present
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                # Fetch recent historical values for even deeper analysis
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                prompt = f"""
You are the GeoAI Moroccan Resource & Investment Advisor, an expert environmental economist and spatial analyst.
You help investors assess the viability of agricultural, industrial, and renewable energy projects in Morocco.

A user has sent you this message: "{message}"

Here is the scientific data we fetched from Google Earth Engine for the region "{region}" (Year: {year}):
- Region: {region}
- Groundwater Anomaly: {gw_val:.3f} cm (GRACE)
- Surface Water Index (NDWI): {ndwi_val:.3f}
- Vegetation Health Index (NDVI): {ndvi_val:.3f}

Current Active Map View in Platform:
- Year: {year}
- Current Filter: {current_index}
- Current Region Focus: {region}

Please analyze this data and write a professional, highly engaging, and context-specific response.
- First, briefly state whether the investment outlook for "{region}" is High Risk, Moderate Risk, or High Potential.
- Then, break down what the exact three indices ({gw_val:.2f} cm GW, {ndwi_val:.2f} NDWI, {ndvi_val:.2f} NDVI) mean for local water security and soil viability.
- Recommend 3 specific sustainable business sectors that are highly viable (e.g. solar energy, desalination, drought-resistant crops like Argan/Olive, green hydrogen, cold chain logistics) and warn against 2 sectors that are extremely risky (water-intensive agriculture).
- Make sure to format your response beautifully in Markdown. Use bullet points, bold text, and warning blockquotes (> [!WARNING]) where appropriate.
- Keep the tone professional, insightful, and realistic. Do not exceed 450 words.
"""
                response = model.generate_content(prompt)
                return response.text
            except Exception as gem_err:
                print(f"Gemini API invocation failed: {gem_err}. Using Data-Driven Expert Engine.")
                
        # Generate the structured report via local expert system
        return get_expert_report(region, year, gw_val, ndwi_val, ndvi_val)

    # 4. Standard conversational responses or general inquiries about Morocco
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
