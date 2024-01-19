import streamlit as st
import pandas as pd
import calendar
import altair as alt
import matplotlib.pyplot as plt
import numpy as np

# Función para cargar datos desde Google Sheets
def load_data():
    url_operaciones = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFmOu4IjdEt7gLuAqjJTMvcpelmTr_IsL1WRy238YgRPDGLxsW74iMVUhYM2YegUblAKbLemfMxpW8/pub?gid=0&single=true&output=csv"
    url_proyecciones = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFmOu4IjdEt7gLuAqjJTMvcpelmTr_IsL1WRy238YgRPDGLxsW74iMVUhYM2YegUblAKbLemfMxpW8/pub?gid=81813189&single=true&output=csv"
    url_proyecciones_iniciales = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFmOu4IjdEt7gLuAqjJTMvcpelmTr_IsL1WRy238YgRPDGLxsW74iMVUhYM2YegUblAKbLemfMxpW8/pub?gid=1798498183&single=true&output=csv"

    data_operaciones = pd.read_csv(url_operaciones, parse_dates=['FechaEfectiva'])
    data_proyecciones = pd.read_csv(url_proyecciones, parse_dates=['Fecha'], dayfirst=True)
    data_proyecciones_iniciales = pd.read_csv(url_proyecciones_iniciales, parse_dates=['FechaProgramada'], dayfirst=True)

    data_operaciones['Monto'] = pd.to_numeric(data_operaciones['Monto'], errors='coerce')
    data_proyecciones['Monto'] = pd.to_numeric(data_proyecciones['Monto'], errors='coerce')
    data_operaciones['Ejecutados'] = data_operaciones['Monto']
    data_proyecciones['Proyectados'] = data_proyecciones['Monto']
    data_proyecciones_iniciales['Monto'] = pd.to_numeric(data_proyecciones_iniciales['Monto'], errors='coerce')
    data_proyecciones_iniciales['ProyeccionesIniciales'] = data_proyecciones_iniciales['Monto']

    data_operaciones['Year'] = data_operaciones['FechaEfectiva'].dt.year
    data_operaciones['Month'] = data_operaciones['FechaEfectiva'].dt.month
    data_proyecciones['Year'] = data_proyecciones['Fecha'].dt.year
    data_proyecciones['Month'] = data_proyecciones['Fecha'].dt.month
    data_proyecciones_iniciales['Year'] = data_proyecciones_iniciales['FechaProgramada'].dt.year
    data_proyecciones_iniciales['Month'] = data_proyecciones_iniciales['FechaProgramada'].dt.month

    # Agregar la columna 'Pais' basándonos en las dos primeras letras de 'IDOperacion'
    data_operaciones['Pais'] = data_operaciones['IDOperacion'].str[:2].map({'AR': 'ARGENTINA', 'BO': 'BOLIVIA', 'BR': 'BRASIL', 'PY': 'PARAGUAY', 'UR': 'URUGUAY'})
    data_proyecciones['Pais'] = data_proyecciones['IDOperacion'].str[:2].map({'AR': 'ARGENTINA', 'BO': 'BOLIVIA', 'BR': 'BRASIL', 'PY': 'PARAGUAY', 'UR': 'URUGUAY'})
    data_proyecciones_iniciales['Pais'] = data_proyecciones_iniciales['IDOperacion'].str[:2].map({'AR': 'ARGENTINA', 'BO': 'BOLIVIA', 'BR': 'BRASIL', 'PY': 'PARAGUAY', 'UR': 'URUGUAY'})

    grouped_operaciones = data_operaciones.groupby(['Pais', 'IDOperacion', 'Year', 'Month']).agg({'Monto': 'sum'}).rename(columns={'Monto': 'Ejecutados'}).reset_index()
    grouped_proyecciones = data_proyecciones.groupby(['Pais', 'IDOperacion', 'Year', 'Month']).agg({'Monto': 'sum'}).rename(columns={'Monto': 'Proyectados'}).reset_index()
    # Agrupa data_proyecciones_iniciales por los campos necesarios
    grouped_proyecciones_iniciales = data_proyecciones_iniciales.groupby(['Pais', 'IDOperacion', 'Year', 'Month']).agg({'ProyeccionesIniciales': 'sum'}).reset_index()

    # Combina los tres conjuntos de datos: operaciones, proyecciones y proyecciones iniciales
    merged_data = pd.merge(grouped_operaciones, grouped_proyecciones, on=['Pais', 'IDOperacion', 'Year', 'Month'], how='outer')
    merged_data = pd.merge(merged_data, grouped_proyecciones_iniciales, on=['Pais', 'IDOperacion', 'Year', 'Month'], how='outer').fillna(0)

    # Conversiones finales y ajustes de escala
    merged_data['Ejecutados'] = (merged_data['Ejecutados'] / 1000000).round(2)
    merged_data['Proyectados'] = (merged_data['Proyectados'] / 1000000).round(2)
    merged_data['ProyeccionesIniciales'] = (merged_data['ProyeccionesIniciales'] / 1000000).round(2)

    st.write(merged_data)
    return merged_data


def get_monthly_data(data, year):
    data_year = data[data['Year'] == year]

    # Agrupar los datos por mes y sumar los montos
    grouped_data = data_year.groupby('Month').agg({'Proyectados': 'sum', 'Ejecutados': 'sum', 'ProyeccionesIniciales': 'sum'}).reset_index()

    # Reemplazar el número del mes con el nombre del mes en español
    spanish_months = [calendar.month_name[i].capitalize() for i in range(1, 13)]
    grouped_data['Month'] = grouped_data['Month'].apply(lambda x: spanish_months[x - 1])

    # Transponer el DataFrame para que los meses sean columnas y 'Proyectados' y 'Ejecutados' sean las filas
    transposed_data = grouped_data.set_index('Month').T

    # Calcular los totales para cada fila
    transposed_data['Totales'] = transposed_data.sum(axis=1)

    return transposed_data

def create_line_chart_with_labels(data):
    # Eliminar la columna 'Totales' del DataFrame para evitar que se muestre en el gráfico
    if 'Totales' in data.columns:
        data = data.drop(columns=['Totales'])

    # Melt the DataFrame to long format
    long_df = data.reset_index().melt('index', var_name='Month', value_name='Amount')

    # Define the correct order for months in español
    month_order_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    # Create a line chart
    line = alt.Chart(long_df).mark_line(point=True).encode(
        x=alt.X('Month:N', sort=month_order_es),  # Use the order for months in español
        y=alt.Y('Amount:Q', title='Amount'),
        color='index:N',
        tooltip=['Month', 'Amount', 'index']
    ).properties(
        width=600,
        height=500
    )

    # Add text labels for the data points
    text = line.mark_text(
        align='left',
        baseline='middle',
        dx=12,
        dy=12 
    ).encode(
        text='Amount:Q'
    )

    return (line + text)


def create_comparison_bar_chart(filtered_data, year):
    # Filtrar los datos para el año seleccionado
    data_year = filtered_data[filtered_data['Year'] == year]

    # Agrupar los datos por 'Pais' y calcular la suma de 'Ejecutados' y 'Proyectados', redondeando a un decimal
    grouped_data = data_year.groupby('Pais', as_index=False).agg({
        'Ejecutados': lambda x: round(x.sum(), 1),
        'Proyectados': lambda x: round(x.sum(), 1)
    })

    # Configurar las posiciones y ancho de las barras
    bar_width = 0.35
    index = np.arange(len(grouped_data['Pais']))

    # Iniciar la creación del gráfico
    fig, ax = plt.subplots()

    # Crear las barras para 'Ejecutados'
    bars1 = ax.bar(index - bar_width/2, grouped_data['Ejecutados'], bar_width, label='Ejecutados', color='r')

    # Crear las barras para 'Proyectados'
    bars2 = ax.bar(index + bar_width/2, grouped_data['Proyectados'], bar_width, label='Proyectados', color='b')

    # Añadir las etiquetas de los datos en las barras
    ax.bar_label(bars1, padding=3, fmt='%.1f')
    ax.bar_label(bars2, padding=3, fmt='%.1f')

    # Ajustar las etiquetas y títulos
    ax.set_xlabel('País')
    ax.set_ylabel('Monto (en millones)')
    ax.set_title('Ejecutados y Proyectados por País')
    ax.set_xticks(index)
    ax.set_xticklabels(grouped_data['Pais'], rotation=45)
    ax.legend()

    # Ajuste final para asegurar que la disposición de las etiquetas sea legible
    fig.tight_layout()

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)

# Función principal de la aplicación Streamlit
def main():
    # Título de la aplicación
    st.title("Seguimiento de Pronóstico de Desembolsos Proyectados")

    # Cargar datos
    data = load_data()

    # Obtener lista de años únicos basados en los datos filtrados
    unique_years = data['Year'].unique().tolist()

    # Filtrar por Pais con selección múltiple
    selected_countries = st.multiselect("Selecciona país(es)", ["Todos"] + data['Pais'].unique().tolist())

    if "Todos" in selected_countries:
        filtered_data = data
    else:
        # Filtrar por países seleccionados
        filtered_data = data[data['Pais'].isin(selected_countries)]

    # Convertir los valores de año a enteros y obtener la lista ordenada
    unique_years_filtered = sorted(filtered_data['Year'].astype(int).unique())

    # Asegurarse de que haya años disponibles
    if unique_years_filtered:
        # Seleccionar el año mediante un slider
        year = st.slider("Selecciona el año", min_value=unique_years_filtered[0], max_value=unique_years_filtered[-1], value=unique_years_filtered[0])
    else:
        st.error("No hay datos disponibles para mostrar basados en la selección de país.")
        return # Finaliza la ejecución de la función si no hay años para mostrar


    # Filtrar por IDOperacion después de obtener los datos mensuales
    selected_project = st.selectbox("Selecciona proyecto", ["Todos"] + filtered_data['IDOperacion'].unique().tolist())

    if selected_project == "Todos":
        filtered_data = filtered_data
    else:
        # Filtrar por IDOperacion
        filtered_data = filtered_data[filtered_data['IDOperacion'] == selected_project]

    # Obtener datos mensuales para el año seleccionado
    monthly_data = get_monthly_data(filtered_data, year)

    # Mostrar los datos en Streamlit
    st.write(f"Desembolsos Mensuales para {year} - País(es) seleccionado(s): {', '.join(selected_countries)} - Proyecto seleccionado: {selected_project}")
    st.write(monthly_data)

    # Crear y mostrar el gráfico de líneas con etiquetas
    chart = create_line_chart_with_labels(monthly_data)
    st.altair_chart(chart, use_container_width=True)

    create_comparison_bar_chart(filtered_data, year)

if __name__ == "__main__":
    main()