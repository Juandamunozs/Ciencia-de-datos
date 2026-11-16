from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import resumen as R

st.set_page_config(page_title="Temperatura y rendimiento · Valle del Cauca", page_icon="🌾", layout="wide")

# datos
CARPETA_DEFECTO = R.encontrar_carpeta() or "data/procesados/tablero"
st.sidebar.title("🌾 Valle del Cauca")
st.sidebar.caption("Rendimiento de cultivos y temperatura (IDEAM)")
carpeta = st.sidebar.text_input("Carpeta con los CSV del notebook", CARPETA_DEFECTO)
if not (Path(carpeta) / "metricas_modelos.csv").exists():
    st.error(f"No encuentro `metricas_modelos.csv` en `{carpeta}`. Ejecuta el notebook completo (sección 11) o corrige la ruta en la barra lateral.")
    st.stop()


@st.cache_data(show_spinner=False)
def cargar(carpeta, nombre, con_municipio=False):
    return R.leer(carpeta, nombre, dtype={"id_municipio": str} if con_municipio else None)


@st.cache_data(show_spinner="Calculando intervalos de confianza…")
def boot(carpeta):
    return R.comparaciones_bootstrap(cargar(carpeta, "predicciones_prueba.csv", True))


@st.cache_data(show_spinner=False)
def resumen_texto(carpeta):
    return R.construir_resumen(carpeta)


met = cargar(carpeta, "metricas_modelos.csv")
pred = cargar(carpeta, "predicciones_prueba.csv", True)
base = cargar(carpeta, "base_modelado.csv", True)
hip = cargar(carpeta, "hipotesis_resultados.csv")
comp = cargar(carpeta, "hipotesis_complementarias.csv")
kw = cargar(carpeta, "kruskal_wallis_clima.csv")
abl = cargar(carpeta, "ablacion_hipotesis.csv")
dsub = cargar(carpeta, "delta_por_subgrupo.csv")
sint = cargar(carpeta, "sintesis_hipotesis.csv")
imp = cargar(carpeta, "importancia_permutacion.csv")
shap_r = cargar(carpeta, "shap_resumen.csv")
evid = cargar(carpeta, "evidencia_cultivo.csv")
clus = cargar(carpeta, "clusters_municipios.csv", True)

PAGINAS = ["Resumen", "¿Qué tan bien predice?", "Hipótesis H1 a H5", "¿Qué usa el modelo?", "Explorador", "Limitaciones"]
pagina = st.sidebar.radio("Sección", PAGINAS)
st.sidebar.divider()
st.sidebar.caption("Todas las cifras salen de los archivos del notebook; ningún modelo de lenguaje es fuente de datos.")


def tabla(df, formatos=None, **kw_):
    st.dataframe(df.style.format(formatos or {}, na_rep="—"), hide_index=True, width="stretch", **kw_)


def mae(prefijo):
    return float(met.loc[met["Modelo"].str.startswith(prefijo), "MAE prueba"].iloc[0])


# RESUMEN
if pagina == "Resumen":
    st.title("¿Los años más cálidos reducen el rendimiento de los cultivos del Valle?")
    st.caption("Resumen para público no técnico · generado desde los resultados del notebook")
    texto, cifras = resumen_texto(carpeta)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Error si repite el año anterior (B1)", f"{mae('B1'):.3f}")
    c2.metric("Error sin datos del IDEAM (B2)", f"{mae('B2'):.3f}")
    c3.metric("Error con clima completo (M2)", f"{mae('M2'):.3f}", delta=f"{mae('M2') - mae('B2'):+.3f} vs B2", delta_color="inverse")
    if sint is not None:
        n_ok = int(sint["Veredicto"].fillna("").str.startswith("Respaldada").sum())
        c4.metric("Hipótesis respaldadas (de 5)", n_ok)
    st.caption("El error se mide como fracción del rendimiento típico del cultivo: 0,30 = equivocarse en un 30 %. Menor es mejor.")
    st.divider()
    st.markdown(texto)
    col_a, col_b = st.columns(2)
    col_a.download_button("⬇️ Descargar resumen (.md)", texto, file_name="resumen_ejecutivo.md", mime="text/markdown")
    col_b.download_button("⬇️ Descargar verificación de cifras (.csv)", cifras.to_csv(index=False).encode("utf-8-sig"),
                          file_name="verificacion_cifras.csv", mime="text/csv")
    with st.expander("Verificación: de dónde sale cada cifra del resumen"):
        tabla(cifras)

# PREDICCIÓN
elif pagina == "¿Qué tan bien predice?":
    st.title("¿Qué tan bien se predice el rendimiento?")
    st.write("Los modelos se entrenaron con años pasados y se evalúan en años que **no habían visto**. "
             "Un modelo solo vale si supera a las referencias simples (B0, B1, B2).")
    m = met.copy()
    m["Rol"] = np.where(m["Tipo"] == "Línea base", "Referencia", "Modelo")
    orden = m.sort_values("MAE prueba")["Modelo"].tolist()
    graf = (alt.Chart(m).mark_bar().encode(
        x=alt.X("MAE prueba:Q", title="Error absoluto medio en prueba (menor es mejor)"),
        y=alt.Y("Modelo:N", sort=orden, title=None),
        color=alt.Color("Rol:N", scale=alt.Scale(domain=["Referencia", "Modelo"], range=["#9A9A9A", "#4C78A8"])),
        tooltip=["Modelo", alt.Tooltip("MAE prueba:Q", format=".4f"), alt.Tooltip("R² prueba:Q", format=".3f")]).properties(height=300))
    st.altair_chart(graf, width="stretch")
    with st.expander("Tabla completa de métricas"):
        tabla(met, {c: "{:.4f}" for c in met.columns if met[c].dtype.kind == "f"})

    st.subheader("¿La mejora es real o ruido?")
    st.write("Diferencia de error entre dos modelos con intervalo de confianza del 95 % (*bootstrap* por municipio-año). "
             "**Si el intervalo cruza el 0, no se distingue del ruido.**")
    b = boot(carpeta)
    tabla(b, {"Δ MAE (ref − modelo)": "{:+.5f}", "IC95 inferior": "{:+.5f}", "IC95 superior": "{:+.5f}"})
    g_b = alt.Chart(b).mark_errorbar(ticks=True).encode(
        y=alt.Y("Comparación:N", title=None), x=alt.X("IC95 inferior:Q", title="Reducción del error (a la derecha del 0 el modelo mejora)"),
        x2="IC95 superior:Q")
    p_b = alt.Chart(b).mark_point(filled=True, size=70).encode(y="Comparación:N", x="Δ MAE (ref − modelo):Q")
    r0 = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="black").encode(x="x:Q")
    st.altair_chart((g_b + p_b + r0).properties(height=150), width="stretch")

    st.subheader("Predicho frente a real")
    c1, c2, c3 = st.columns(3)
    etiquetas = {"pred_B2": "B2 · sin datos del IDEAM", "pred_M1": "M1 · con clima normal", "pred_M2": "M2 · con clima completo"}
    col_pred = c1.selectbox("Modelo", list(etiquetas), index=2, format_func=etiquetas.get)
    grupos = c2.multiselect("Tipo de cultivo", sorted(pred["grupo"].unique()), default=sorted(pred["grupo"].unique()))
    anios = c3.multiselect("Año", sorted(pred["anio"].unique()), default=sorted(pred["anio"].unique()))
    d = pred[pred["grupo"].isin(grupos) & pred["anio"].isin(anios)]
    if len(d):
        lim = float(np.nanpercentile(np.r_[d["y_real"], d[col_pred]], 99))
        lim0 = float(np.nanpercentile(np.r_[d["y_real"], d[col_pred]], 1))
        pts = alt.Chart(d.sample(min(len(d), 4000), random_state=1)).mark_circle(opacity=0.45, size=30).encode(
            x=alt.X("y_real:Q", title="Real (anomalía del rendimiento relativo)", scale=alt.Scale(domain=[lim0, lim])),
            y=alt.Y(f"{col_pred}:Q", title="Predicho", scale=alt.Scale(domain=[lim0, lim])),
            color="grupo:N", tooltip=["municipio", "cultivo", "anio", alt.Tooltip("y_real:Q", format=".3f"), alt.Tooltip(f"{col_pred}:Q", format=".3f")])
        diag = alt.Chart(pd.DataFrame({"v": [lim0, lim]})).mark_line(color="black", strokeDash=[4, 4]).encode(x="v:Q", y="v:Q")
        e1, e2 = st.columns(2)
        e1.altair_chart((pts + diag).properties(height=330), width="stretch")
        err = d.assign(error=(d["y_real"] - d[col_pred]).abs()).groupby("anio", as_index=False)["error"].mean()
        e2.altair_chart(alt.Chart(err).mark_bar().encode(x=alt.X("anio:O", title="Año"), y=alt.Y("error:Q", title="Error absoluto medio"),
                                                          tooltip=["anio", alt.Tooltip("error:Q", format=".3f")]).properties(height=330), width="stretch")
        st.caption(f"{len(d):,} registros. La línea punteada es la predicción perfecta.".replace(",", "."))
    else:
        st.info("Selecciona al menos un tipo de cultivo y un año.")

# HIPÓTESIS
elif pagina == "Hipótesis H1 a H5":
    st.title("Las cinco hipótesis del Laboratorio 2")
    st.write("Cada hipótesis se probó **dos veces**: con una prueba estadística de asociación y con el modelo de aprendizaje automático. "
             "Está *respaldada* solo si ambas coinciden.")
    if sint is None:
        st.warning("Falta `sintesis_hipotesis.csv`: vuelve a ejecutar el notebook completo.")
        st.stop()
    resumen_h = sint[["ID", "Hipótesis", "Veredicto"]]
    tabla(resumen_h)
    st.divider()
    en_claro = {"H1": "Si un año es más cálido que lo normal en su municipio, el cultivo rinde menos de lo habitual.",
                "H2": "Ese efecto es más fuerte en cultivos de ciclo corto (transitorios) que en permanentes.",
                "H3": "Un año cálido pesa más en municipios que ya son cálidos que en los fríos.",
                "H4": "La temperatura del año anterior también se asocia con el rendimiento, sobre todo en cultivos permanentes.",
                "H5": "Cuando la diferencia entre el día y la noche es mayor que lo normal, el rendimiento baja."}
    hid = st.selectbox("Elige una hipótesis", sint["ID"].tolist(), format_func=lambda i: sint.set_index("ID").loc[i, "Hipótesis"])
    fila = sint.set_index("ID").loc[hid]
    st.markdown(f"**En palabras simples:** {en_claro.get(hid, '')}")
    v = str(fila["Veredicto"])
    (st.success if v.startswith("Respaldada") else st.warning if v.startswith("Respaldo parcial") else st.info)(f"**Veredicto:** {v}")
    if v.startswith("Sin respaldo"):
        st.caption("«Sin respaldo» no significa que el efecto no exista: estos datos no logran distinguirlo del ruido.")
    c1, c2 = st.columns(2)
    c1.markdown("**Prueba estadística**"); c1.write(fila["Prueba estadística"])
    c2.markdown("**Prueba con modelo**"); c2.write(fila["Prueba con modelo"])

    st.subheader("Tablas de apoyo")
    ids_hip = {"H1": ["H1"], "H2": ["H2"], "H3": ["H3"], "H4": ["H4a", "H4b"], "H5": ["H5"]}[hid]
    if hip is not None:
        st.markdown("**Contraste principal (errores agrupados por municipio, corrección de Holm)**")
        tabla(hip[hip["ID"].isin(ids_hip)], {"β": "{:+.4f}", "IC95 inf": "{:+.4f}", "IC95 sup": "{:+.4f}", "p bilateral": "{:.3g}",
                                              "p unilateral (Ha: β<0)": "{:.3g}", "p Holm": "{:.3g}", "N": "{:,.0f}"})
    if comp is not None and (comp["ID"] == hid).any():
        st.markdown("**Pruebas complementarias**")
        tabla(comp[comp["ID"] == hid], {"Estimador": "{:+.4f}", "IC95 inf": "{:+.4f}", "IC95 sup": "{:+.4f}", "p bilateral": "{:.3g}",
                                         "ΔR² por el rezago": "{:+.5f}"})
    if hid == "H3" and kw is not None and len(kw):
        st.markdown("**Kruskal-Wallis entre climas**")
        tabla(kw, {c: "{:+.4f}" for c in kw.columns if c.startswith("mediana")} | {"H de Kruskal-Wallis": "{:.2f}", "p": "{:.3g}"})
    if hid in ("H1", "H4", "H5") and abl is not None:
        st.markdown("**Prueba con modelo: ¿empeora la predicción si se quita la variable?**")
        tabla(abl[abl["Hipótesis"] == hid], {"Δ MAE (sin − con)": "{:+.5f}", "IC95 inferior": "{:+.5f}", "IC95 superior": "{:+.5f}"})
    if hid in ("H2", "H3") and dsub is not None:
        st.markdown("**Prueba con modelo: ¿ayudan más las anomalías del año en este subgrupo?**")
        tabla(dsub[dsub["Hipótesis"] == hid], {"Δ MAE (M1 − M2)": "{:+.5f}", "IC95 inferior": "{:+.5f}", "IC95 superior": "{:+.5f}"})

# INTERPRETACIÓN
elif pagina == "¿Qué usa el modelo?":
    st.title("¿Qué variables usa el modelo?")
    st.write("**Importancia por permutación:** cuánto empeora el error al desordenar una variable, medido en años de prueba. "
             "Rojo = variables que vienen de la integración con el IDEAM.")
    g1 = alt.Chart(imp).mark_bar().encode(
        x=alt.X("aumento_MAE:Q", title="Aumento del error al desordenar la variable"),
        y=alt.Y("etiqueta:N", sort="-x", title=None),
        color=alt.Color("origen:N", scale=alt.Scale(domain=["Integración (IDEAM)", "Cultivos (Parte 1)"], range=["#E45756", "#4C78A8"]), title="Origen"),
        tooltip=["etiqueta", alt.Tooltip("aumento_MAE:Q", format=".5f"), alt.Tooltip("desv:Q", format=".5f")]).properties(height=300)
    st.altair_chart(g1, width="stretch")
    if shap_r is not None:
        st.write("**Valores SHAP:** cuánto empuja cada variable la predicción, registro a registro (promedio del valor absoluto).")
        st.altair_chart(alt.Chart(shap_r).mark_bar(color="#F58518").encode(
            x=alt.X("mean_abs_shap:Q", title="Efecto medio sobre la predicción (|SHAP|)"), y=alt.Y("etiqueta:N", sort="-x", title=None),
            tooltip=["etiqueta", alt.Tooltip("mean_abs_shap:Q", format=".5f")]).properties(height=300), width="stretch")
    dir_fig = next((p for p in ["figuras", "../figuras", str(Path(carpeta).parents[1] / "figuras") if len(Path(carpeta).parents) > 1 else "figuras"]
                    if (Path(p) / "shap_beeswarm.png").exists()), None)
    if dir_fig:
        with st.expander("Figuras SHAP del notebook"):
            for f in ["shap_beeswarm.png", "shap_dependencia_t_anom.png"]:
                if (Path(dir_fig) / f).exists():
                    st.image(str(Path(dir_fig) / f))
    st.warning("**Cuidado al interpretar.** La importancia mide cuánto *usa* el modelo una variable, no que *cause* el rendimiento. "
               "Además, la temperatura normal del municipio identifica al municipio: parte de su importancia es geografía, no clima del año.")

# EXPLORADOR
elif pagina == "Explorador":
    st.title("Explorador: anomalía de temperatura frente a rendimiento")
    st.write("Cada punto es un cultivo en un municipio y año. Eje X: cuánto se desvió la temperatura de lo normal del municipio. "
             "Eje Y: cuánto se desvió el rendimiento de lo normal de ese cultivo en ese municipio.")
    c1, c2, c3 = st.columns(3)
    muns = c1.multiselect("Municipio", sorted(base["municipio"].unique()))
    grp = c2.multiselect("Tipo de cultivo", sorted(base["grupo"].unique()), default=sorted(base["grupo"].unique()))
    cult = c3.multiselect("Cultivo", sorted(base["cultivo"].unique()))
    d = base[base["grupo"].isin(grp)]
    if muns:
        d = d[d["municipio"].isin(muns)]
    if cult:
        d = d[d["cultivo"].isin(cult)]
    if len(d) < 5:
        st.info("Muy pocos registros con esos filtros.")
    else:
        rho = d[["t_anom", "y"]].corr(method="spearman").iloc[0, 1]
        k1, k2 = st.columns(2); k1.metric("Registros", f"{len(d):,}".replace(",", ".")); k2.metric("Correlación de Spearman", f"{rho:+.3f}")
        pts = alt.Chart(d.sample(min(len(d), 4000), random_state=1)).mark_circle(opacity=0.35, size=25).encode(
            x=alt.X("t_anom:Q", title="Anomalía de temperatura (°C)"), y=alt.Y("y:Q", title="Anomalía del rendimiento relativo"),
            color="grupo:N", tooltip=["municipio", "cultivo", "anio", alt.Tooltip("t_anom:Q", format=".2f"), alt.Tooltip("y:Q", format=".3f")])
        linea = pts.transform_regression("t_anom", "y").mark_line(color="black")
        st.altair_chart((pts + linea).properties(height=380), width="stretch")
        st.caption("La línea es un ajuste lineal simple, solo descriptivo. Una correlación cercana a 0 indica que no hay asociación visible.")
    if evid is not None:
        st.subheader("Asociación por cultivo (exploratoria)")
        e = evid.copy(); e["¿Significativa tras FDR?"] = np.where(e["p_FDR"] < R.ALFA, "Sí", "No")
        st.altair_chart(alt.Chart(e).mark_bar().encode(
            x=alt.X("rho:Q", title="Correlación de Spearman (temperatura vs rendimiento)"), y=alt.Y("cultivo:N", sort="x", title=None),
            color=alt.Color("¿Significativa tras FDR?:N", scale=alt.Scale(domain=["Sí", "No"], range=["#E45756", "#BBBBBB"])),
            tooltip=["cultivo", "n", alt.Tooltip("rho:Q", format="+.3f"), alt.Tooltip("p_FDR:Q", format=".3g")]).properties(height=max(300, 18 * len(e))),
            width="stretch")
    if clus is not None:
        with st.expander("Perfil climático de los municipios (clústeres)"):
            tabla(clus, {c: "{:.2f}" for c in ["t_hist", "amp_hist", "var_t", "var_amp"] if c in clus.columns})

# LIMITACIONES
else:
    st.title("Limitaciones: qué no dice este análisis")
    st.markdown("""
- **Sesgo de cobertura.** Solo hay temperatura en municipios con estación del IDEAM y con historia suficiente. Los resultados **no se extienden al resto del Valle**; además las estaciones no están repartidas al azar y pueden estar a otra altitud que los cultivos.
- **Falacia ecológica.** Los datos son municipales: describen municipios, **no fincas ni personas**. Lo que ocurre en el promedio de un municipio no tiene por qué ocurrir en cada productor.
- **Correlación no es causalidad.** Que una variable ayude a predecir (o aparezca importante en SHAP) no demuestra que cause el cambio de rendimiento. Faltan lluvia, riego, plagas, tecnología y precios.
- **Incertidumbre.** Pocos años de prueba y pocos municipios; por eso se reportan intervalos de confianza y se corrigen las comparaciones múltiples.
- **Una estación por municipio y cambios de estación** entre años pueden mezclarse con el clima real.
- **Periodos distintos:** transitorios hasta 2022 y permanentes hasta 2023.
""")
    st.subheader("Uso de modelos de lenguaje")
    st.write("El resumen ejecutivo y este tablero **no usan un modelo de lenguaje como fuente de datos**: las cifras se leen directamente de los CSV "
             "del notebook y cada una queda registrada en la tabla de verificación (sección *Resumen*). Si se usa un modelo de lenguaje para pulir la "
             "redacción, cada número debe verificarse contra esa tabla.")