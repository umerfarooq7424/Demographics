import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import re

st.markdown(
    """
    <style> 
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .title {
        font-size: 30px;
        font-weight: bold;
        color: #4CAF50;
        margin-bottom: 10px;
    }
    .instructions {
        font-size: 16px;
        color: #555;
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and Instructions container
with st.container():
    st.markdown('<div class="title">Explore US Housing and Demographics Data</div>', unsafe_allow_html=True)

# Data: U.S. states with their centroids (latitude and longitude)
state_data = {
    'State': ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
              'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
              'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey',
              'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Puerto Rico', 'Rhode Island', 'South Carolina', 'South Dakota',
              'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'Washington D.C.', 'West Virginia', 'Wisconsin', 'Wyoming'],
    'Latitude': [32.806671, 61.370716, 33.729759, 34.969704, 36.116203, 39.059811, 41.597782, 39.318523, 27.766279, 33.040619,
                 21.094318, 44.240459, 40.349457, 39.849426, 42.011539, 38.526600, 37.668140, 31.169546, 44.693947, 39.063946,
                 42.230171, 43.326618, 45.694454, 32.741646, 38.456085, 46.921925, 41.125370, 38.313515, 43.452492, 40.298904,
                 34.840515, 42.165726, 35.630066, 47.528912, 40.388783, 35.565342, 44.572021, 40.590752, 38.89511, 41.680893, 33.856892, 44.299782,
                 35.747845, 31.054487, 40.150032, 44.045876, 37.769337, 47.400902, 38.9072, 38.491226, 44.268543, 42.755966],
    'Longitude': [-86.791130, -152.404419, -111.431221, -92.373123, -119.681564, -105.311104, -72.755371, -75.507141, -81.686783, -83.643074,
                  -157.498337, -114.478828, -88.986137, -86.258278, -93.210526, -96.726486, -84.670067, -91.867805, -69.381927, -76.802101,
                  -71.530106, -84.536095, -93.900192, -89.678696, -92.288368, -110.454353, -98.268082, -117.055374, -71.563896, -74.521011,
                  -106.248482, -74.948051, -79.806419, -99.784012, -82.764915, -96.928917, -122.070938, -77.209755, -77.03637, -71.511780, -80.945007, -99.438828,
                  -86.692345, -97.563461, -111.862434, -72.710686, -78.169968, -121.490494, -77.0369, -80.954456, -89.616508, -107.302490]
}

# Create a DataFrame from the state data
df_states = pd.DataFrame(state_data)

# Load state boundaries from a GeoJSON file
with open("gz_2010_us_040_00_5m.json") as f:
    geojson_data = json.load(f)

# Definitions for selection
definitions = {
    "Persons by Age": "Demographic data on the distribution of persons by age categories.",
    "Public School Children": "Data representing children enrolled in public schools across various units.",
    "School Age Children": "Statistics of children belonging to school-going age ranges."
}

# Streamlit app
st.sidebar.title("Options")

# User selects state, unit type, and data category
selected_state = st.sidebar.selectbox("State:", df_states['State']).upper()
# unit_types = ["Allunits", "Newerunits"]
unit_types = {
    "All (All Age) Housing - Built in any year": "Allunits",
    "Newer (Newer Built) Housing - Built 2000-2021": "Newerunits"
}
category_labels = {
    "Household Size": "pop",
    "Persons by Age": "pop",
    "Household Size Statistics": "pop",
    "Total Public School Children" : "psc",
    "Public School Children by school level and grade group": "psc",
    "Public School Children Statistics": "psc",
    "Total School Age Children" : "sac",
    "School Age Children by school level and grade group": "sac",
    "School Age Children Statistics": "sac",
}

# selected_unit_type = st.sidebar.selectbox("Housing Age:", unit_types, help="Newer Housing: Built between 2000-2021.\nAll Housing: Built in any year.")
selected_label = st.sidebar.selectbox("Housing Age:", list(unit_types.keys()))
selected_unit_type = unit_types[selected_label]

selected_category_label = st.sidebar.selectbox("Data Category:", category_labels.keys())
selected_category = category_labels[selected_category_label]
if (selected_unit_type=='Allunits'):
    selected_unit_type='ALLunits'
else:
    selected_unit_type='NEWERunits'
try:
    file_name = f"DM_{selected_category}_{selected_state}_{selected_unit_type}.csv"
    data = pd.read_csv(file_name)
    # Get unique values from the "Structure" column
    # unique_structures = data["Structure"].unique()
    #####
    # Split into components
    def normalize_structure(structure):
        structure = re.sub(r"\s*\(\s*", " (", structure)
        structure = re.sub(r"\s*\)\s*,?\s*", ") ", structure)
        return structure.strip()  
    unique_structures = data["Structure"].apply(normalize_structure).unique()

    structure_options = []
    tenure_options = set()
    size_options = set()
    for structure in unique_structures:
        parts = structure.split("(")
        if len(parts) == 2:
            house_type = parts[0].strip()
            tenure_bedroom = parts[1].split(")")
            if len(tenure_bedroom) == 2:
                tenure = tenure_bedroom[0].strip()
                bedroom = tenure_bedroom[1].strip()
                structure_options.append(house_type)
                tenure_options.add(tenure)
                size_options.add(bedroom)

    # Convert sets to lists
    tenure_options = list(tenure_options)
    size_options = list(size_options)

    custom_order_structure = ['Single-Family Detached','Single-Family Attached','2-4 Units','5-49 Units','50+ Units','All Housing Types']
    structure_rename_map = {
    'Single-Family Detached': 'Single Family Detached',
    'Single-Family Attached': 'Single Family Attached (Townhouses)',
    '2-4 Units': 'Smaller Multifamily (2-4 units)',
    '5-49 Units': 'Midsize Multifamily (5-49 units)',
    '50+ Units': 'Larger Multifamily (50 units+)',
    'All Housing Types': 'All Housing Units'
    }   
    # Combined structure and tenure options
    combined_options = [
        "Single-Family Detached (Combines Own and Rent tenure)",
        "Single-Family Attached (Combines Own and Rent tenure)",
        "Smaller (2-4 unit) Multifamily (Combines Own and Rent tenure)",
        "Midsize (5-49 units) Multifamily (Own tenure alone)",
        "Midsize (5-49 units) Multifamily (Rent tenure alone)",
        "Larger (50 or more units) Multifamily (Own tenure alone)",
        "Larger (50 or more units) Multifamily (Rent tenure alone)",
        "All Housing (all above housing types) (Own tenure alone)",
        "All Housing (all above housing types) (Rent tenure alone)"
    ]

    # Sidebar selectbox to choose structure and tenure together
    selected_combined_option = st.sidebar.selectbox("Select Housing Type and Tenure:", combined_options)

    # Mapping selected option back to structure and tenure
    structure_tenure_map = {
        "Single-Family Detached (Combines Own and Rent tenure)": ("Single-Family Detached", "Own/Rent"),
        "Single-Family Attached (Combines Own and Rent tenure)": ("Single-Family Attached", "Own/Rent"),
        "Smaller (2-4 unit) Multifamily (Combines Own and Rent tenure)": ("2-4 Units", "Own/Rent"),
        "Midsize (5-49 units) Multifamily (Own tenure alone)": ("5-49 Units", "Own"),
        "Midsize (5-49 units) Multifamily (Rent tenure alone)": ("5-49 Units", "Rent"),
        "Larger (50 or more units) Multifamily (Own tenure alone)": ("50+ Units", "Own"),
        "Larger (50 or more units) Multifamily (Rent tenure alone)": ("50+ Units", "Rent"),
        "All Housing (all above housing types) (Own tenure alone)": ("All Housing Types", "Own"),
        "All Housing (all above housing types) (Rent tenure alone)": ("All Housing Types", "Rent"),
    }

    # Get the selected structure and tenure
    selected_type, selected_tenure = structure_tenure_map[selected_combined_option]

    # sorted_structure_options = sorted((set(structure_options)), key=lambda x: custom_order_structure.index(x))
    # renamed_structure_options = [structure_rename_map[x] for x in sorted_structure_options]
    # # User selects Type, Tenure, and Size separately
    # selected_display_type = st.sidebar.selectbox("Structure Type:", renamed_structure_options)
    # selected_type = next(key for key, value in structure_rename_map.items() if value == selected_display_type)

    # if selected_type in ["5-49 Units", "50+ Units", "All Housing Types"]:
    #     tenure_options_display = ["Own", "Rent"]
    # else:
    #     tenure_options_display = ["Own/Rent"]
    # selected_tenure = st.sidebar.selectbox("Tenure:", tenure_options_display)
    selected_size = st.sidebar.selectbox("Housing Size (Number of Bedrooms):", ['Studio-1BR' if x == '0-1 BR' else x for x in sorted(size_options)])

    # Reconstruct the structure format
    selected_structure = f"{selected_type} ({selected_tenure}) {selected_size}"
    
    data["Normalized_Structure"] = data["Structure"].apply(normalize_structure)

    filtered_data = data[data["Normalized_Structure"] == selected_structure].copy()
    data.drop(columns=["Normalized_Structure"], inplace=True)
    filtered_data.drop(columns=["Normalized_Structure"], inplace=True)
    #####
    # User selects a structure to view details
    #selected_structure = st.sidebar.selectbox("Structure:", unique_structures)

    # Filter data based on the selected structure
    # filtered_data = data[data["Structure"] == selected_structure]
    list_columns=["Structure", "VALUE_TENURE", "value_range"]
    statistics= ["Number of Households" , "Standard Errors", "Low", "High", "Error Margin as %"]
    labels_selected = {
    "Household Size": ["Structure", "VALUE_TENURE", "value_range", "PERSONS"],
    "Persons by Age": ["Structure", "VALUE_TENURE", "value_range", "0-4","5-17","18-34", "35-44", "45-54", "55-64", "65-74", "75+"],
    "Household Size Statistics" : ["Structure", "VALUE_TENURE", "value_range","Number of Households" , "Standard Errors", "Low", "High", "Error Margin as %"],
    "Total Public School Children" : ["Structure", "VALUE_TENURE", "value_range", "PSC"],
    "Public School Children by school level and grade group": ["Structure", "VALUE_TENURE", "value_range", "(K-5)", "(6-8)", "(9-12)"],
    "Public School Children Statistics": ["Structure", "VALUE_TENURE", "value_range", "Standard Errors", "Low", "High", "Error Margin as %"],
    "Total School Age Children" : ["Structure", "VALUE_TENURE", "value_range", "SAC"],
    "School Age Children by school level and grade group": ["Structure", "VALUE_TENURE", "value_range", "(K-5)", "(6-8)", "(9-12)"],
    "School Age Children Statistics":["Structure", "VALUE_TENURE", "value_range", "Standard Errors", "Low", "High", "Error Margin as %"],
    }

    selected_value = st.sidebar.selectbox("Housing Value", filtered_data['VALUE_TENURE'].dropna().unique())
    filtered_data = filtered_data[filtered_data['VALUE_TENURE'] == selected_value]
    # Display the filtered data
    if not filtered_data.empty:
        # st.dataframe(filtered_data)
        st.dataframe(filtered_data[labels_selected[selected_category_label]])
    else:
        st.write("No data available for the selected structure.")

    selected_state= selected_state.title()
    # Get coordinates for the selected state
    state_row = df_states[df_states['State'] == selected_state]
    if not state_row.empty:
        coordinates = state_row[['Latitude', 'Longitude']].values[0]

        # Filter the GeoJSON data to include only the selected state
        selected_state_feature = next(
            (feature for feature in geojson_data["features"] if feature["properties"]["NAME"]== selected_state), None
        )
        filtered_geojson_data = {
            "type": "FeatureCollection",
            "features": [selected_state_feature] if selected_state_feature else []
        }

        # Create a DataFrame for the map
        state_data_for_map = pd.DataFrame({
            'latitude': [coordinates[0]],
            'longitude': [coordinates[1]],
            'state': [selected_state]
        })

        # Define the map
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=coordinates[0],
                longitude=coordinates[1],
                zoom=5,
                pitch=0,
            ),
            layers=[
                # Scatterplot for the selected state
                pdk.Layer(
                    'ScatterplotLayer',
                    state_data_for_map,
                    get_position='[longitude, latitude]',
                    pickable=True,
                ),
                # GeoJSON layer for the selected state boundary
                pdk.Layer(
                    "GeoJsonLayer",
                    filtered_geojson_data,
                    pickable=True,
                    stroked=True,
                    filled=True,
                    extruded=False,
                    line_width_min_pixels=2,
                    get_fill_color=[255, 0, 0, 80],  # Red fill with transparency
                    get_line_color=[255, 0, 0, 255],  # Red boundary
                )
            ],
        ))
        with st.expander("Glossary and User Guide"):
            st.markdown(
                """
                <style>
                .heading {
                    color: #6AA84F; 
                    font-weight: bold;
                }
                .subheading {
                    color: #6D9EEB;
                    font-weight: bold;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("""
            - **<span class="heading">ACS</span>**: American Community Survey. The ACS is a yearly survey of population and housing in the United States that is administered by the United States Census Bureau
            - **<span class="heading">Bedrooms (BR) (Housing Size)</span>**: The number of rooms that would be listed as bedrooms if the house or apartment were listed on the market for sale or rent even if these rooms are currently used for other purposes. A housing unit consisting of only one room is classified as having no bedroom (studio).
            - **<span class="heading">Demographic Multipliers</span>**: In this study, encompasses residential demographic multipliers—the number and profile of occupants in housing.
            - **<span class="heading">Housing Age</span>**: 
                - **<span class="subheading">Newer (or Newer Built) housing</span>**: In this study, refers to housing units built in New Jersey over the period 2000-2021.
                - **<span class="subheading">All (or All Age) housing</span>**: In this study, refers to all housing units built in New Jersey of any year. It includes both newer and older housing units.
            - **<span class="heading">Housing Categories (Structure Type)</span>**: 
                - **<span class="subheading">Single-family detached</span>**: A 1-unit structure detached from any other house, that is, with open space on all four sides. Such structures are considered detached even if they have an adjoining shed or garage. A one-family house that contains a business is considered detached as long as the building has open space on all four sides.
                - **<span class="subheading">Single-family attached</span>**: A 1-unit structure that has one or more walls extending from ground to roof separating it from adjoining structures. In row houses (sometimes called townhouses), double houses, or houses attached to nonresidential structures, each house is a separate, attached structure if the dividing or common wall goes from ground to roof.
                - **<span class="subheading">2–4 units (smaller multifamily)</span>**: Units in structures containing 2, 3, or 4 housing units.
                - **<span class="subheading">5–49 units (mid-size multifamily)</span>**: Units in structures containing 5 to 49 housing units.
                - **<span class="subheading">50+ units (larger multifamily)</span>**: Units in structures containing 50 or more housing units.
            - **<span class="heading">Housing Rent (Contract Rent)</span>**: Contract rent is the monthly rent agreed to or contracted for, regardless of any furnishings, utilities, fees, meals, or services that may be included.
            - **<span class="heading">Housing Rent (Gross Rent)</span>**: Gross rent is the contract rent plus the estimated average monthly cost of utilities (electric, gas, water and sewer) and fuels (oil, coal, kerosene, wood, and the like) if these are paid by the renter (or paid for the renter by someone else). In this study, the monthly gross rents (converted to housing-unit value; see Housing Value) are indicated in the Part II demographic tables.
            - **<span class="heading">Household Size</span>**: The total number of persons in a housing unit.
            - **<span class="heading">Housing Tenure (Ownership or Rental)</span>**: A housing unit is occupied if it is either owner-occupied or renter-occupied. A housing unit is owner-occupied if the owner or co-owner lives in the unit, even if it is mortgaged or not fully paid for. All occupied housing units that are not owner-occupied, whether they are rented or occupied without payment of rent, are classified as renter-occupied.
            - **<span class="heading">Housing Unit</span>**: A housing unit may be a house, an apartment, a group of rooms, or a single room that is occupied (or, if vacant, intended for occupancy) as separate living quarters.
            - **<span class="heading">Housing Value (Rent)</span>**: For owner-occupied units, housing value is the census respondent’s estimate of how much the property (including the lot and additional buildings for non-condominium multi-unit buildings) would sell for if it were for sale. In this study, the value of a rented unit is estimated to be 110 times the monthly gross rent. The housing value and rents are adjusted to 2021 values using the ACS adjustment factor for housing dollar.  For Newer Housing in New Jersey (units built 2000–2021), housing value is categorized into tripartite classification: housing priced below the median, housing priced above the median, and All Value housing. Since in the 5-year ACS survey median values change from year to year, the classification is done relative to the year-specific median values. The above housing price terms are just as they are stated. Housing priced below the median should not be confused with affordable or Mount Laurel housing, as it is sometimes referred to in New Jersey. Housing priced above the median is not synonymous with what is sometimes referred to as market-rate housing (to contrast the marketrate from the affordable or “Mount Laurel” categories). For all housing units in New Jersey (newer and older built units), housing value is categorized into a quadripartite classification: All Value housing, and then housing units arrayed by terciles (thirds) of value: first tercile (lower one-third), second tercile (middle one-third), and third tercile (upper one-third). The first tercile is not synonymous with either affordable housing or Mount Laurel housing. 
            - **<span class="heading">Median Housing Value</span>**: The median divides the value distribution into two equal parts: one-half of the cases falling below the median value of the property, and one-half above the median. Reported medians are based on 5-year ACS data on housing values using adjusted 2021 dollars.
            - **<span class="heading">Public School Children (PSC)</span>**: The school-age children (SAC) attending public school.
            - **<span class="heading">Residential Multipliers</span>**: These multipliers show the population associated with different housing categories as well as housing differentiated by housing value, housing size (bedrooms), and housing tenure.
            - **<span class="heading">School-Age Children (SAC)</span>**: The household members of elementary and secondary school age, defined here as those 5 through 17 years of age.
            - **<span class="heading">Terciles (Housing Value)</span>**: Terciles of housing value (for the All Age housing in New Jersey) are the statistics that divide the observations of housing value into three intervals, each containing 33.333 percent of the data. The first (lower one-third), second (middle one-third), and third (upper one-third) terciles of housing value are computed by ordering the housing values from lowest to highest and then finding the housing values below which fall one-third and two-thirds of the housing value data. 
            """,
            unsafe_allow_html=True,
            )

except Exception as e:
    st.error(f"An error occurred: {e}")
