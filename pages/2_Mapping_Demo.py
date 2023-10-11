import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import threading

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def process_dataframe_for_sector_and_country(xls_path):
    with _lock:
        xls = pd.ExcelFile(xls_path, engine='openpyxl')
        desembolsos = xls.parse('Desembolsos')
        operaciones = xls.parse('Operaciones')

    # Map to assign countries
    country_map = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brasil', 'PY': 'Paraguay', 'UR': 'Uruguay'}
    operaciones['Pais'] = operaciones['IDEtapa'].str[:2].map(country_map).fillna('Desconocido')

    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia', 'SECTOR', 'Pais']], on='IDEtapa', how='left')
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 366).astype(int)
    merged_df['Meses'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 30).astype(int)
    
    result_df = merged_df.groupby(['SECTOR', 'Pais', 'Ano', 'Meses', 'IDDesembolso'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['SECTOR', 'Pais'])['Monto'].cumsum().reset_index(drop=True)
    result_df['Porcentaje del Monto'] = result_df.groupby(['SECTOR', 'Pais'])['Monto'].apply(lambda x: x / x.sum() * 100).reset_index(drop=True)
    result_df['Porcentaje del Monto Acumulado'] = result_df.groupby(['SECTOR', 'Pais'])['Monto Acumulado'].apply(lambda x: x / x.max() * 100).reset_index(drop=True)

    return result_df

def run_for_sector_and_country():
    st.set_page_config(
        page_title="Desembolsos por Sector y País",
        page_icon="🌍",
    )

    st.title("Análisis de Desembolsos por Sector y País 🌍")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos por sector y país.")

    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")

    if uploaded_file:
        result_df = process_dataframe_for_sector_and_country(uploaded_file)
        st.write(result_df)

        selected_sector = st.selectbox('Selecciona el Sector:', result_df['SECTOR'].unique())
        selected_country = st.selectbox('Selecciona el País:', result_df['Pais'].unique())

        filtered_df = result_df[(result_df['SECTOR'] == selected_sector) & (result_df['Pais'] == selected_country)]

        df_monto = filtered_df.groupby('Ano')["Monto"].mean().reset_index()
        df_monto_acumulado = filtered_df.groupby('Ano')["Monto Acumulado"].mean().reset_index()
        df_porcentaje_monto_acumulado = filtered_df.groupby('Ano')["Porcentaje del Monto Acumulado"].mean().reset_index()
        df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"] = df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"].round(2)

        combined_df = pd.concat([df_monto, df_monto_acumulado["Monto Acumulado"], df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"]], axis=1)
        st.write("Resumen de Datos:")
        st.write(combined_df)

        # ... (charts will remain the same, just changing the titles to reflect the sector and country) ...

    st.sidebar.info("Selecciona un sector y un país para visualizar las métricas.")

if __name__ == "__main__":
    run_for_sector_and_country()

