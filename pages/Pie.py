import streamlit as st
import pandas as pd
import altair as alt

def process_data_for_pie_chart_v3(xls_path):
    xls = pd.ExcelFile(xls_path, engine='openpyxl')
    desembolsos = xls.parse('Desembolsos')
    operaciones = xls.parse('Operaciones')

    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia', 'SECTOR']], on='IDEtapa', how='left')
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 366).astype(int)
    
    # Group by SECTOR, Ano and sum the Monto
    pie_data = merged_df.groupby(['SECTOR', 'Ano'])['Monto'].sum().reset_index()
    
    return pie_data

def run_for_pie_chart_and_table():
    st.set_page_config(
        page_title="Desembolsos por Sector y Año",
        page_icon="🌍",
    )

    st.title("Análisis de Desembolsos por Sector y Año 🌍")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos por sector y año.")

    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")

    if uploaded_file:
        pie_data = process_data_for_pie_chart_v3(uploaded_file)
        
        selected_year = st.selectbox('Selecciona el Año:', pie_data['Ano'].unique())

        chart_data = pie_data[pie_data['Ano'] == selected_year].copy()
        total_monto = chart_data['Monto'].sum()
        chart_data['Porcentaje del Monto'] = (chart_data['Monto'] / total_monto) * 100

        # Display the table
        st.write("Tabla de Desembolsos por Sector:")
        st.write(chart_data)

        pie_chart = alt.Chart(chart_data).mark_arc().encode(
            alt.Theta('Monto:Q', stack=True),
            alt.Color('SECTOR:N', legend=alt.Legend(title='Sectores'))
        ).properties(
            title=f'Distribución de Montos por Sector en el año {selected_year}',
            width=400,
            height=400
        )

        st.altair_chart(pie_chart, use_container_width=True)

if __name__ == "__main__":
    run_for_pie_chart_and_table()
