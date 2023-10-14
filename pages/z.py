import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import threading
import io

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

def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
    output.seek(0)
    return output

def run():
    st.set_page_config(
        page_title="Desembolsos por País",
        page_icon="🌍",
    )

    st.title("Análisis de Desembolsos por País 🌍")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos por país.")

    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")

    if uploaded_file:
        result_df = process_dataframe(uploaded_file)
        st.write(result_df)

        selected_country = st.selectbox('Selecciona el País:', result_df['Pais'].unique())

        filtered_df = result_df[result_df['Pais'] == selected_country]

        df_monto = filtered_df.groupby('Ano')["Monto"].sum().reset_index(name='Suma de Monto').round(2)
        df_monto_promedio = filtered_df.groupby('Ano')["Monto"].mean().reset_index(name='Promedio de Monto').round(2)
        df_desembolsos_count = filtered_df.groupby('Ano').size().reset_index(name='Cantidad Desembolsos')
        df_monto_acumulado = filtered_df.groupby('Ano')["Monto Acumulado"].mean().reset_index(name='Promedio de Monto Acumulado').round(2)
        df_porcentaje_monto_acumulado = filtered_df.groupby('Ano')["Porcentaje del Monto Acumulado"].mean().reset_index(name='Porcentaje del Monto Acumulado').round(2)

        combined_df = pd.merge(df_monto, df_desembolsos_count, on='Ano')
        combined_df = pd.merge(combined_df, df_monto_promedio, on='Ano')
        combined_df = pd.merge(combined_df, df_monto_acumulado, on='Ano')
        combined_df = pd.merge(combined_df, df_porcentaje_monto_acumulado, on='Ano')

        # Añadir la columna 'IDEtapa' al DataFrame 'combined_df'
        combined_df['IDEtapa'] = filtered_df['IDEtapa'].unique()[0]

        st.write("Resumen de Datos:")
        st.write(combined_df)

        # Mover el botón de descarga debajo de "Resumen de Datos"
        excel_bytes = dataframe_to_excel_bytes(result_df)
        st.download_button(
            label="Descargar resultados como Excel",
            data=excel_bytes,
            file_name="resultados_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        chart_monto = alt.Chart(df_monto).mark_line(point=True, color='blue').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Suma de Monto:Q',
            tooltip=['Ano', 'Suma de Monto']
        ).properties(
            title=f'Suma de Monto por año para {selected_country}',
            width=600,
            height=400
        )
        st.altair_chart(chart_monto, use_container_width=True)

        chart_monto_acumulado = alt.Chart(df_monto_acumulado).mark_line(point=True, color='purple').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Promedio de Monto Acumulado:Q',
            tooltip=['Ano', 'Promedio de Monto Acumulado']
        ).properties(
            title=f'Promedio de Monto Acumulado por año para {selected_country}',
            width=600,
            height=400
        )
        st.altair_chart(chart_monto_acumulado, use_container_width=True)

        chart_porcentaje = alt.Chart(df_porcentaje_monto_acumulado).mark_line(point=True, color='green').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Porcentaje del Monto Acumulado:Q',
            tooltip=['Ano', 'Porcentaje del Monto Acumulado']
        ).properties(
            title=f'Promedio del Porcentaje del Monto Acumulado por año para {selected_country}',
            width=600,
            height=400
        )
        st.altair_chart(chart_porcentaje, use_container_width=True)

    st.sidebar.info("Selecciona un país para visualizar las métricas.")

if __name__ == "__main__":
    run()


