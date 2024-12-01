import streamlit as st
import pandas as pd
import pydeck as pdk
import json

# Data: U.S. states with their centroids (latitude and longitude)
state_data = {
'State': ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
              'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
              'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey',
              'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
              'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming', 'Washington D.C.', 'Puerto Rico'],
    'Latitude': [32.806671, 61.370716, 33.729759, 34.969704, 36.116203, 39.059811, 41.597782, 39.318523, 27.766279, 33.040619,
                 21.094318, 44.240459, 40.349457, 39.849426, 42.011539, 38.526600, 37.668140, 31.169546, 44.693947, 39.063946,
                 42.230171, 43.326618, 45.694454, 32.741646, 38.456085, 46.921925, 41.125370, 38.313515, 43.452492, 40.298904,
                 34.840515, 42.165726, 35.630066, 47.528912, 40.388783, 35.565342, 44.572021, 40.590752, 41.680893, 33.856892, 44.299782,
                 35.747845, 31.054487, 40.150032, 44.045876, 37.769337, 47.400902, 38.491226, 44.268543, 42.755966, 38.9072, 18.2208],
    'Longitude': [-86.791130, -152.404419, -111.431221, -92.373123, -119.681564, -105.311104, -72.755371, -75.507141, -81.686783, -83.643074,
                  -157.498337, -114.478828, -88.986137, -86.258278, -93.210526, -96.726486, -84.670067, -91.867805, -69.381927, -76.802101,
                  -71.530106, -84.536095, -93.900192, -89.678696, -92.288368, -110.454353, -98.268082, -117.055374, -71.563896, -74.521011,
                  -106.248482, -74.948051, -79.806419, -99.784012, -82.764915, -96.928917, -122.070938, -77.209755, -71.511780, -80.945007, -99.438828,
                  -86.692345, -97.563461, -111.862434, -72.710686, -78.169968, -121.490494, -80.954456, -89.616508, -107.302490, -77.0369, -66.5901]
}
# Create a DataFrame from the state data
df_states = pd.DataFrame(state_data)

# Load state boundaries from a GeoJSON file
with open("gz_2010_us_040_00_5m.json") as f:
    geojson_data = json.load(f)

# Streamlit app
st.title("Select Options to Load Data")

# User selects state, unit type, and data category
selected_state = st.selectbox("Choose a State:", df_states['State'])
unit_types = ["Allunits", "Newerunits"]
category_labels = {
    "Persons by Age": "pop",
    "Public School Children": "psc",
    "School Age Children": "sac"
}
selected_unit_type = st.selectbox("Choose Unit Type:", unit_types)
selected_category_label = st.selectbox("Choose Data Category:", category_labels.keys())
selected_category = category_labels[selected_category_label]

# Construct the file path based on user selections
file_path = f"DM_{selected_category}_{selected_state}_{selected_unit_type}.csv"

try:
    # Load the selected file into a DataFrame
    data = pd.read_csv(file_path)

    # Get unique values from the "Structure" column
    unique_structures = data["Structure"].unique()

    # User selects a structure to view details
    selected_structure = st.selectbox("Choose a Structure:", unique_structures)

    # Filter data based on the selected structure
    filtered_data = data[data["Structure"] == selected_structure]

    # Display the filtered data
    if not filtered_data.empty:
        st.write(f"Details for {selected_structure}:")
        st.dataframe(filtered_data)
    else:
        st.write("No data available for the selected structure.")

    # Get coordinates for the selected state
    state_row = df_states[df_states['State'] == selected_state]
    if not state_row.empty:
        coordinates = state_row[['Latitude', 'Longitude']].values[0]

        # Filter the GeoJSON data to include only the selected state
        selected_state_feature = next(
            (feature for feature in geojson_data["features"] if feature["properties"]["NAME"] == selected_state), None
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
                    #get_fill_color=[0, 0, 255, 160],  # Blue fill with transparency
                    #get_radius=50000,  # Adjust the radius as needed
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

except FileNotFoundError:
    st.write("The selected file does not exist. Please check your options.")
