import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

pagina = st.sidebar.radio(
    "Menú",
    ["Precio Bolsa", "Precio Oferta"]
)

if pagina == "Precio Bolsa":
    st.title("Precio de Bolsa Nacional - XM")
    st.subheader("Precio de bolsa diario: promedio, mínimo y máximo ($/kWh)")


    BASE_DIR = Path(__file__).resolve().parent.parent
    ruta_datos = BASE_DIR / "data" / "processed" / "precio_bolsa_limpio.csv"

    df = pd.read_csv(ruta_datos)

    df["fecha"] = pd.to_datetime(df["fecha"])

    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    # Dropdowns
    col_inicio, col_fin = st.columns(2)

    with col_inicio:
        fecha_inicio = st.date_input(
            "Fecha inicial",
            value=fecha_min,
            min_value=fecha_min,
            max_value=fecha_max
        )

    with col_fin:
        fecha_fin = st.date_input(
            "Fecha final",
            value=fecha_max,
            min_value=fecha_min,
            max_value=fecha_max
        )

    if fecha_inicio > fecha_fin:
        st.error("La fecha inicial no puede ser mayor que la fecha final")
        st.stop()


    df_filtrado = df[
        (df["fecha"] >= pd.to_datetime(fecha_inicio)) &
        (df["fecha"] <= pd.to_datetime(fecha_fin))
    ]

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
    **Promedio periodo**  
    {df_filtrado['precio'].mean():,.2f} $/kWh
    """)

    col2.markdown(f"""
    **Máximo periodo**  
    {df_filtrado['precio'].max():,.2f} $/kWh
    """)

    col3.markdown(f"""
    **Mínimo periodo**  
    {df_filtrado['precio'].min():,.2f} $/kWh
    """)

    col4.markdown(f"""
    **Días analizados**  
    {df_filtrado['fecha'].nunique()}
    """)

    df_resultado = (
        df_filtrado
        .groupby("fecha", as_index=False)
        .agg(
            precio_promedio=("precio", "mean"),
            precio_minimo=("precio", "min"),
            precio_maximo=("precio", "max")
        )
    )

    df_resultado = df_resultado.rename(columns={
        "precio_promedio": "Precio Promedio",
        "precio_minimo": "Precio Mínimo",
        "precio_maximo": "Precio Máximo"
    })

    fig = go.Figure()

    # Promedio (línea principal)
    fig.add_trace(go.Scatter(
        x=df_resultado["fecha"],
        y=df_resultado["Precio Promedio"],
        mode='lines',
        name='Precio Promedio',
        line=dict(color="#1f77b4", width=3)
    ))

    # Máximo (secundario)
    fig.add_trace(go.Scatter(
        x=df_resultado["fecha"],
        y=df_resultado["Precio Máximo"],
        mode='lines',
        name='Precio Máximo',
        line=dict(color="#ffbf00", width=2),
        opacity=0.7
    ))

    # Mínimo (secundario)
    fig.add_trace(go.Scatter(
        x=df_resultado["fecha"],
        y=df_resultado["Precio Mínimo"],
        mode='lines',
        name='Precio Mínimo',
        line=dict(color="#9ecae1", width=2),
        opacity=0.7
    ))

    fig.update_layout(
        title="Precio de Bolsa Nacional",
        xaxis=dict(
            title="Fecha",
            tickformat="%d-%b",
            tickangle=30
        ),
        yaxis=dict(
            title="Precio ($/kWh)"
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="%d-%b-%Y",
            tickangle=315
        )
    )


    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Mapa de calor horario (últimos 30 días)")

    # Últimos 30 días respecto a la fecha final seleccionada
    fecha_fin_dt = pd.to_datetime(fecha_fin)
    fecha_inicio_heatmap = fecha_fin_dt - pd.Timedelta(days=30)

    df_heatmap_base = df_filtrado[
        (df_filtrado["fecha"] >= fecha_inicio_heatmap) &
        (df_filtrado["fecha"] <= fecha_fin_dt)
    ].copy()

    # Crear matriz: filas = fecha, columnas = hora
    df_heatmap = df_heatmap_base.pivot_table(
        index="fecha",
        columns="hora",
        values="precio",
        aggfunc="mean"
    )

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=df_heatmap.values,
            x=df_heatmap.columns,
            y=df_heatmap.index,

            # 🎨 Gradiente continuo limpio
            colorscale=[
            [0.00, "#006837"],   # verde bajo
            [0.20, "#66bd63"],   # verde medio
            [0.40, "#d9ef8b"],   # verde/amarillo hasta 400 aprox
            [0.41, "#fee08b"],   # alerta desde 400
            [0.70, "#f46d43"],   # naranja
            [1.00, "#a50026"],   # rojo alto
        ],

            zmin=0,
            zmax=1000,

            colorbar=dict(title="$/kWh"),

            # Cuadrícula
            xgap=1,
            ygap=1
        )
    )

    fig_heatmap.update_layout(
        xaxis_title="Hora",
        yaxis_title="Fecha",
        height=650,
        plot_bgcolor="white",
        paper_bgcolor="white",
    xaxis=dict(
        title="Hora",
        tickmode="array",
        tickvals=list(range(24)),
        ticktext=[str(h) for h in range(24)]
    )
    )

    st.caption(f"Última fecha disponible: {df['fecha'].max()}")
    st.plotly_chart(fig_heatmap, use_container_width=True)

    df_diario = (
        df_filtrado
        .groupby("fecha", as_index=False)["precio"]
        .mean()
    )

    df_diario["mes"] = df_diario["fecha"].dt.to_period("M").dt.to_timestamp()

    df_mensual = (
        df_diario
        .groupby("mes")
        .agg(
            minimo=("precio", "min"),
            p25=("precio", lambda x: x.quantile(0.25)),
            mediana=("precio", "median"),
            media=("precio", "mean"),
            p75=("precio", lambda x: x.quantile(0.75)),
            maximo=("precio", "max")
        )
        .reset_index()
    )

    fig_box = go.Figure()

    fig_box.add_trace(go.Candlestick(
        x=df_mensual["mes"],
        open=df_mensual["p25"],
        high=df_mensual["maximo"],
        low=df_mensual["minimo"],
        close=df_mensual["p75"],
        name="Rango mensual (P25 - P75)",
        increasing_line_color="#1f77b4",
        decreasing_line_color="#1f77b4",
        increasing_fillcolor="rgba(31,119,180,0.35)",
        decreasing_fillcolor="rgba(31,119,180,0.35)"
    ))

    fig_box.add_trace(go.Scatter(
        x=df_mensual["mes"],
        y=df_mensual["media"],
        mode="lines+markers",
        name="Media",
        line=dict(color="rgba(255,165,0,0.35)", width=2),
        marker=dict(color="rgba(255,165,0,0.35)", size=5)
    ))

    fig_box.add_trace(go.Scatter(
        x=df_mensual["mes"],
        y=df_mensual["mediana"],
        mode="lines+markers",
        name="Mediana",
        line=dict(color="rgba(0,128,0,0.35)", width=2),
        marker=dict(color="rgba(0,128,0,0.35)", size=5)
    ))

    fig_box.update_layout(
        title="Distribución mensual del precio promedio diario",
        
        xaxis=dict(
            title="Mes",
            tickformat="%b-%Y",
            tickangle=30,
            rangeslider=dict(visible=False)
        ),
        
        yaxis=dict(
            title="Precio ($/kWh)"
        ),
        
        legend=dict(
            orientation="h",
            y=1.08,
            x=1,
            xanchor="right"
        ),
        
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=550
    )

    st.plotly_chart(fig_box, use_container_width=True)

    st.dataframe(df_resultado)

elif pagina == "Precio Oferta":

    st.title("Precio de Oferta - XM")

    # cargar datos
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent
    ruta = BASE_DIR / "data" / "processed" / "precio_oferta_limpio.csv"

    df = pd.read_csv(ruta)
    df["fecha"] = pd.to_datetime(df["fecha"])

    # filtro de fechas
    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()

    fecha_inicio, fecha_fin = st.date_input(
        "Selecciona el rango de fechas",
        value=(fecha_max - pd.Timedelta(days=30), fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    df_filtrado = df[
        (df["fecha"] >= pd.to_datetime(fecha_inicio)) &
        (df["fecha"] <= pd.to_datetime(fecha_fin))
    ]

    # agrupación simple
    # Filtro de planta
    plantas = sorted(df_filtrado["NombreUnidad"].dropna().unique())

    plantas_seleccionadas = st.multiselect(
        "Filtrar plantas",
        options=plantas,
        default=[]
    )

    if plantas_seleccionadas:
        df_filtrado = df_filtrado[
            df_filtrado["NombreUnidad"].isin(plantas_seleccionadas)
        ]

    # Promedio diario por planta
    df_diario_oferta = (
        df_filtrado
        .groupby(["CodigoPlanta", "NombreUnidad", "fecha"], as_index=False)["precio_oferta"]
        .mean()
    )

    # Ordenar plantas por precio promedio descendente
    orden_plantas = (
        df_diario_oferta
        .groupby(["CodigoPlanta", "NombreUnidad"], as_index=False)["precio_oferta"]
        .mean()
        .sort_values("precio_oferta", ascending=False)
    )

    # Tabla matriz: filas = plantas, columnas = días
    tabla_matriz = df_diario_oferta.pivot_table(
        index=["CodigoPlanta", "NombreUnidad"],
        columns="fecha",
        values="precio_oferta",
        aggfunc="mean"
    )

    # Reordenar filas según precio promedio
    orden_index = list(
        orden_plantas.set_index(["CodigoPlanta", "NombreUnidad"]).index
    )

    tabla_matriz = tabla_matriz.reindex(orden_index)

    # Redondear a enteros
    tabla_matriz = tabla_matriz.round(0).astype("Int64")

    # Formato de columnas de fecha
    tabla_matriz.columns = [
        col.strftime("%Y-%m-%d") for col in tabla_matriz.columns
    ]

    st.subheader("Precio de oferta por planta y día")

    st.dataframe(
    tabla_matriz.style.background_gradient(
        cmap="RdYlGn_r",
        axis=None
    ),
    use_container_width=True
)