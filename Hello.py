import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt

LOGGER = get_logger(__name__)
import threading

_lock = threading.Lock()

def process_dataframe(xls_path):
    with _lock:
        # Cargar el archivo Excel especificando el motor 'openpyxl'
        xls = pd.ExcelFile(xls_path, engine='openpyxl')
        desembolsos = xls.parse('Desembolsos')
        operaciones = xls.parse('Operaciones')

    # Unir dataframes y calcular la columna 'Ano'
    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia']], on='IDEtapa', how='left')
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 365).round().astype(int)
    merged_df['Meses'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 12).round().astype(int)

    # Calcular montos agrupados y montos acumulados incluyendo IDDesembolso
    result_df = merged_df.groupby(['IDEtapa', 'Ano', 'Meses', 'IDDesembolso'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['IDEtapa'])['Monto'].cumsum().reset_index(drop=True)
    result_df['Porcentaje del Monto'] = result_df.groupby(['IDEtapa'])['Monto'].apply(lambda x: x / x.sum() * 100).reset_index(drop=True)
    result_df['Porcentaje del Monto Acumulado'] = result_df.groupby(['IDEtapa'])['Monto Acumulado'].apply(lambda x: x / x.max() * 100).reset_index(drop=True)

    # Asignar países
    country_map = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brasil', 'PY': 'Paraguay', 'UR': 'Uruguay'}
    result_df['Pais'] = result_df['IDEtapa'].str[:2].map(country_map).fillna('Desconocido')
    
    return result_df

def run():
    st.set_page_config(
        page_title="Desembolsos",
        page_icon="👋",
    )

    st.write("Bienvenido aquí analizaremos tus Datos! 👋")

    # Load the Excel file using Streamlit
    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")
    if uploaded_file:
        result_df = process_dataframe(uploaded_file)
        st.write(result_df)

        # Create a dropdown selectbox to select the country
        selected_country = st.selectbox('Choose a country:', result_df['IDEtapa'].unique())

        # Filter the dataframe based on the selected country
        filtered_df = result_df[result_df['IDEtapa'] == selected_country]

        # Create dataframes for the plots
        df_monto = filtered_df.groupby('Ano')["Monto"].sum().reset_index()
        df_monto_acumulado = filtered_df.groupby('Ano')["Monto Acumulado"].last().reset_index()
        df_porcentaje_monto_acumulado = filtered_df.groupby('Ano')["Porcentaje del Monto Acumulado"].last().reset_index()

        # Concatenate the dataframes into a single dataframe
        combined_df = pd.concat([df_monto, df_monto_acumulado["Monto Acumulado"], df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"]], axis=1)

        # Display the combined dataframe in Streamlit
        st.write(combined_df)

        # ... (rest of the code remains unchanged)

    st.sidebar.success("Select a demo above.")
    st.markdown(
        """
    """
    )

if __name__ == "__main__":
    run()

