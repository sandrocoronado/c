import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import threading

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def process_dataframe(xls_path):
    with _lock:
        xls = pd.ExcelFile(xls_path, engine='openpyxl')
        desembolsos = xls.parse('Desembolsos')
        operaciones = xls.parse('Operaciones')

    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia', 'AporteFonplata']], on='IDEtapa', how='left')
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 366).astype(int)
    merged_df['Meses'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 30).astype(int)

    result_df = merged_df.groupby(['IDEtapa', 'Ano', 'Meses', 'IDDesembolso', 'AporteFonplata'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['IDEtapa'])['Monto'].cumsum().reset_index(drop=True)
    result_df['Porcentaje del Monto'] = result_df['Monto'] / result_df['AporteFonplata'] * 100
    result_df['Porcentaje del Monto Acumulado'] = result_df['Monto Acumulado'] / result_df['AporteFonplata'] * 100

    country_map = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brasil', 'PY': 'Paraguay', 'UR': 'Uruguay'}
    result_df['Pais'] = result_df['IDEtapa'].str[:2].map(country_map).fillna('Desconocido')
    
    return result_df

def run():
    st.set_page_config(
        page_title="Desembolsos",
        page_icon="👋",
    )

    st.title("Análisis de Desembolsos 👋")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos.")
    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")
    
    if uploaded_file:
        result_df = process_dataframe(uploaded_file)
        st.write(result_df)
        selected_country = st.selectbox('Selecciona el Proyecto:', result_df['IDEtapa'].unique())
        filtered_df = result_df[result_df['IDEtapa'] == selected_country]
        df_monto = filtered_df.groupby('Ano')["Monto"].sum().reset_index()
        df_monto_acumulado = filtered_df.groupby('Ano')["Monto Acumulado"].last().reset_index()
        df_porcentaje_monto_acumulado = filtered_df.groupby('Ano')["Porcentaje del Monto Acumulado"].last().reset_index()
        df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"] = df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"].round(2)
        combined_df = pd.concat([df_monto, df_monto_acumulado["Monto Acumulado"], df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"]], axis=1)
        st.write("Resumen de Datos:")
        st.write(combined_df)
        chart_monto = alt.Chart(df_monto).mark_line(point=True, color='blue').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Monto:Q',
            tooltip=['Ano', 'Monto']
        ).properties(
            title=f'Monto por año para {selected_country}',
            width=600,
            height=400
        )
        st.altair_chart(chart_monto, use_container_width=True)
        chart_monto_acumulado = alt.Chart(df_monto_acumulado).mark_line(point=True, color='purple').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Monto Acumulado:Q',
            tooltip=['Ano', 'Monto Acumulado']
        ).properties(
            title=f'Monto Acumulado por año para {selected_country}',
            width=600,
            height=400
        )
        st.altair_chart(chart_monto_acumulado, use_container_width=True)
        chart_porcentaje = alt.Chart(df_porcentaje_monto_acumulado).mark_line(point=True, color='green').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Porcentaje del Monto Acumulado:Q',
            tooltip=['Ano', 'Porcentaje del Monto Acumulado']
        ).properties(
            title=f'Porcentaje del Monto Acumulado por año para {selected_country}',
            width=600,
            height=400
        )
        st.altair_chart(chart_porcentaje, use_container_width=True)

    st.sidebar.info("Selecciona un proyecto para visualizar las métricas.")

if __name__ == "__main__":
    run()

