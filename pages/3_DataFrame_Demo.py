import io
import base64
import altair as alt
import pandas as pd
import streamlit as st

def get_table_download_link(df, filename="data.xlsx", text="Download Excel file"):
    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)  
    b64 = base64.b64encode(towrite.read()).decode()  
    button_html = f"""<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="streamlit-btn primary-button">{text}</a>"""
    return button_html

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

        # Añadir el botón de descarga después de mostrar el dataframe
        st.markdown(get_table_download_link(result_df), unsafe_allow_html=True)

        selected_country = st.selectbox('Selecciona el País:', result_df['Pais'].unique())
        filtered_df = result_df[result_df['Pais'] == selected_country]

        df_monto = filtered_df.groupby('Ano')["Monto"].mean().reset_index()
        df_monto_acumulado = filtered_df.groupby('Ano')["Monto Acumulado"].mean().reset_index()
        df_porcentaje_monto_acumulado = filtered_df.groupby('Ano')["Porcentaje del Monto Acumulado"].mean().reset_index()
        df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"] = df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"].round(2)

        combined_df = pd.concat([df_monto, df_monto_acumulado["Monto Acumulado"], df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"]], axis=1)
        st.write("Resumen de Datos:")
        st.write(combined_df)

        chart_monto = alt.Chart(df_monto).mark_line(point=True, color='blue').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Monto:Q',
            tooltip=['Ano', 'Monto']
        ).properties(
            title=f'Promedio de Monto por año para {selected_country}',
            width=600,
            height=400
        )
        st.altair_chart(chart_monto, use_container_width=True)

        chart_monto_acumulado = alt.Chart(df_monto_acumulado).mark_line(point=True, color='purple').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Monto Acumulado:Q',
            tooltip=['Ano', 'Monto Acumulado']
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
