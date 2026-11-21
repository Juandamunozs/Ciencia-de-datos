from datetime import datetime
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import resumen as R

st.set_page_config(page_title="Temperatura y rendimiento · Valle del Cauca", page_icon="📊", layout="wide")

AUTOR, DOCENTE = "Juan David Muñoz Sotelo", "Edison Ferney Enríquez Ceballos"
NAVY, AZUL, ORO, GRIS, ROJO, VERDE = "#14213D", "#3A5BA0", "#A67C00", "#9AA3AE", "#8C2F39", "#2F6B4F"
TONOS = {"ok": VERDE, "warn": ORO, "info": AZUL, "gris": GRIS, "mal": ROJO}

#  tema
def _tema():
    return {"config": {"view": {"stroke": "transparent"}, "background": "transparent",
                       "axis": {"labelColor": "#333", "titleColor": "#333", "gridColor": "#E4E6EA", "domainColor": "#BFC4CC",
                                "labelFontSize": 11, "titleFontSize": 11, "titleFontWeight": "normal"},
                       "legend": {"labelFontSize": 11, "titleFontSize": 11, "orient": "bottom"},
                       "title": {"fontSize": 12, "font": "Georgia", "anchor": "start", "color": NAVY},
                       "range": {"category": [AZUL, ORO, VERDE, ROJO, "#6B5B95", "#4A9BA8", "#8C6D46"]}}}


try:
    alt.theme.register("academico", enable=True)(_tema)
except AttributeError:
    alt.themes.register("academico", _tema)
    alt.themes.enable("academico")

CSS = """
<style>
.block-container{padding-top:1.2rem;max-width:1180px}
html,body,[class*="css"]{font-family:'Source Sans Pro','Segoe UI',Helvetica,Arial,sans-serif}
h1,h2,h3,h4{font-family:Georgia,'Times New Roman',serif!important;color:NAVY;font-weight:700}
[data-testid=stSidebar]{background:#F3F4F6;border-right:1px solid #D9DCE1}
.stMarkdown p,.stMarkdown li{text-align:justify;line-height:1.6}
.banda{background:NAVY;color:#fff;border-radius:4px;padding:10px 18px;margin-bottom:14px;display:flex;justify-content:space-between;font-size:.8rem;letter-spacing:.03em}
.banda b{font-family:Georgia,serif;font-size:.9rem;letter-spacing:0}
.titulo{border-bottom:3px solid ORO;padding-bottom:6px;margin:0 0 4px}
.titulo h1{margin:0;font-size:1.7rem;line-height:1.25}
.subt{color:#5B6470;font-size:.92rem;margin-bottom:16px}
.sec{font-family:Georgia,serif;color:NAVY;font-size:1.25rem;margin:26px 0 6px;padding-bottom:3px;border-bottom:1px solid #CDD1D8}
.sec span{color:ORO;margin-right:8px}
.ley{font-size:.82rem;color:#3d4550;margin:10px 0 4px;font-weight:600}
.fuente{font-size:.75rem;color:#6B7480;margin:2px 0 14px;font-style:italic}
.kpi{background:#fff;border:1px solid #D9DCE1;border-left:5px solid GRIS;border-radius:4px;padding:10px 14px;height:100%}
.kpi .e{font-size:.74rem;color:#5B6470;text-transform:uppercase;letter-spacing:.04em;min-height:2.3em}
.kpi .v{font-family:Georgia,serif;font-size:1.9rem;color:NAVY;line-height:1.2}
.kpi .n{font-size:.73rem;color:#7A838F}
.caja{border:1px solid #D9DCE1;border-left:5px solid AZUL;background:#F7F9FC;border-radius:4px;padding:12px 16px;margin:10px 0}
.caja.ok{border-left-color:VERDE;background:#F2F8F5}.caja.warn{border-left-color:ORO;background:#FBF7EA}.caja.mal{border-left-color:ROJO;background:#FAF1F2}
.caja .t{font-family:Georgia,serif;font-weight:700;color:NAVY;margin-bottom:3px}
.hip{border:1px solid #D9DCE1;border-radius:4px;padding:12px 16px;background:#fff;margin:6px 0}
.badge{display:inline-block;border-radius:3px;padding:1px 9px;font-size:.72rem;font-weight:700;color:#fff;letter-spacing:.04em}
.portada{border:1px solid #CDD1D8;border-top:6px solid NAVY;padding:26px 30px;background:#fff;margin-bottom:16px}
.portada .u{font-size:.82rem;letter-spacing:.08em;text-transform:uppercase;color:#5B6470}
.portada h1{font-size:1.9rem;line-height:1.25;margin:8px 0 6px}
.portada .s{color:#4A5360;font-size:1rem;margin-bottom:12px}
.portada table{font-size:.88rem;border-collapse:collapse}.portada td{padding:2px 16px 2px 0;vertical-align:top}.portada td:first-child{color:#6B7480}
.caja,.hip,.kpi{color:#1E2A25}
.idea{border:1px solid #D9DCE1;border-left:5px solid ORO;background:#FFFDF6;border-radius:4px;padding:10px 16px;margin:4px 0 14px;color:#1E2A25}
.idea b{display:block;font-family:Georgia,serif;color:ORO;font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;margin-bottom:2px}
.paso{border:1px solid #D9DCE1;border-top:4px solid AZUL;border-radius:4px;background:#fff;padding:10px 14px;height:100%;color:#1E2A25}
.paso .n{font-family:Georgia,serif;font-size:1.6rem;color:AZUL;line-height:1}
.paso .t{font-weight:700;color:NAVY;margin:2px 0}
.paso .d{font-size:.85rem;color:#4A5360;line-height:1.45}
.pie{text-align:center;color:#6B7480;font-size:.78rem;padding-top:8px}
@media print{[data-testid=stSidebar],[data-testid=stToolbar],header{display:none!important}.block-container{max-width:100%}}
</style>
""".replace("NAVY", NAVY).replace("AZUL", AZUL).replace("ORO", ORO).replace("GRIS", GRIS).replace("ROJO", ROJO).replace("VERDE", VERDE)
st.markdown(CSS, unsafe_allow_html=True)

#  utilidades de presentación
CONT = {"pg": 0, "t": 0, "f": 0}


def encabezado(num, titulo, subtitulo=""):
    CONT.update(pg=num, t=0, f=0)
    st.markdown(f'<div class="banda"><b>Universidad Santiago de Cali · Facultad de Ingeniería</b>'
                f'<span>Ciencia de Datos con Python (IGS38) · Caso de estudio, Parte 3</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="titulo"><h1>{num}. {titulo}</h1></div><div class="subt">{subtitulo}</div>', unsafe_allow_html=True)


def encabezado_libre(titulo, subtitulo=""):
    st.markdown('<div class="banda"><b>Universidad Santiago de Cali · Facultad de Ingeniería</b>'
                '<span>Ciencia de Datos con Python (IGS38) · Caso de estudio, Parte 3</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="titulo"><h1>{titulo}</h1></div><div class="subt">{subtitulo}</div>', unsafe_allow_html=True)


def seccion(sub, titulo):
    st.markdown(f'<div class="sec"><span>{CONT["pg"]}.{sub}</span>{titulo}</div>', unsafe_allow_html=True)


def leyenda(tipo, texto):
    k = "t" if tipo == "Tabla" else "f"
    CONT[k] += 1
    st.markdown(f'<div class="ley">{tipo} {CONT["pg"]}.{CONT[k]}. {texto}</div>', unsafe_allow_html=True)


def fuente(texto="Elaboración propia a partir de los archivos del tablero generados por el notebook."):
    st.markdown(f'<div class="fuente">Fuente: {texto}</div>', unsafe_allow_html=True)


def kpi(col, etiqueta, valor, nota="", tono="gris"):
    col.markdown(f'<div class="kpi" style="border-left-color:{TONOS[tono]}"><div class="e">{etiqueta}</div>'
                 f'<div class="v">{valor}</div><div class="n">{nota}</div></div>', unsafe_allow_html=True)


def caja(titulo, texto, tono="info"):
    st.markdown(f'<div class="caja {"" if tono == "info" else tono}"><div class="t">{titulo}</div>{R._inline(texto)}</div>', unsafe_allow_html=True)


def badge(texto, tono):
    return f'<span class="badge" style="background:{TONOS[tono]}">{texto}</span>'


def tono_veredicto(v):
    v = str(v)
    return "ok" if v.startswith("Respaldada") else "warn" if v.startswith("Respaldo parcial") else "mal"


def limpio(t):
    return str(t).replace("**", "").replace("*", "")


def _color_celda(v):
    t = str(v)
    if t == "Cumple" or t.startswith("Respaldada"):
        return "background-color:#E3F1E9;color:#1F5A3F;font-weight:600"
    if t == "No verificable" or t.startswith("Respaldo parcial"):
        return "background-color:#FBF1D6;color:#7A5A00;font-weight:600"
    if t in ("No cumple", "No se cumple") or t.startswith("Sin respaldo"):
        return "background-color:#F6E1E3;color:#7A2530;font-weight:600"
    return ""


def tabla(df, formatos=None, alto=None):
    fmt = {k: v for k, v in (formatos or {}).items() if k in df.columns}
    for c in df.columns:
        if c not in fmt and df[c].dtype.kind == "f":
            fmt[c] = "{:.4f}"
    sty = df.style.format(fmt, na_rep="—")
    cols = [c for c in df.columns if c in ("Estado", "Resultado", "Veredicto")]
    if cols:
        sty = (sty.map if hasattr(sty, "map") else sty.applymap)(_color_celda, subset=cols)
    kw_ = {"height": alto} if alto else {}
    st.dataframe(sty, hide_index=True, width="stretch", **kw_)


def idea(texto):
    st.markdown(f'<div class="idea"><b>Idea clave</b>{R._inline(texto)}</div>', unsafe_allow_html=True)


def forest(etq, est, lo, hi, x_titulo, altura=None):
    """Estimación puntual con intervalo de confianza; línea punteada en 0."""
    d = pd.DataFrame({"Etiqueta": list(etq), "Estimación": list(est), "IC inf": list(lo), "IC sup": list(hi)}).dropna()
    d["Lectura"] = np.where((d["IC inf"] > 0) | (d["IC sup"] < 0), "El IC excluye el 0", "El IC incluye el 0")
    esc = alt.Scale(domain=["El IC excluye el 0", "El IC incluye el 0"], range=[AZUL, GRIS])
    ey = alt.Y("Etiqueta:N", sort=None, title=None, axis=alt.Axis(labelLimit=380))
    rg = alt.Chart(d).mark_rule(strokeWidth=4).encode(y=ey, x=alt.X("IC inf:Q", title=x_titulo), x2="IC sup:Q", color=alt.Color("Lectura:N", scale=esc, title=None))
    pt = alt.Chart(d).mark_point(filled=True, size=100, color=NAVY).encode(y=ey, x="Estimación:Q", tooltip=["Etiqueta", alt.Tooltip("Estimación:Q", format="+.5f"),
                                                                           alt.Tooltip("IC inf:Q", format="+.5f"), alt.Tooltip("IC sup:Q", format="+.5f")])
    cero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=NAVY, strokeDash=[5, 4]).encode(x="x:Q")
    return (rg + pt + cero).properties(height=altura or max(110, 38 * len(d)))


def forest_tabla(d, est, x_titulo, pie):
    lo, hi = "IC95 inferior", "IC95 superior"
    if d is None or d.empty or not {est, lo, hi}.issubset(d.columns):
        return
    txt = [c for c in d.columns if not pd.api.types.is_numeric_dtype(d[c]) and c != "Hipótesis"]
    etq = d[txt].astype(str).agg(" · ".join, axis=1) if txt else pd.Series([str(i + 1) for i in range(len(d))], index=d.index)
    etq = etq.reset_index(drop=True)
    if etq.duplicated().any():
        etq = etq + " (" + (etq.groupby(etq).cumcount() + 1).astype(str) + ")"
    leyenda("Figura", pie)
    st.altair_chart(forest(etq, d[est], d[lo], d[hi], x_titulo), width="stretch")


#  datos
CARPETA_DEFECTO = R.encontrar_carpeta() or "data/procesados/tablero"
PAGINAS = ["Inicio", "Pregunta general · Evolución y temperatura", "1. Presentación", "2. Planteamiento", "3. Datos y fuentes", "4. Metodología", "5. Resultados del modelo",
           "6. Contraste de hipótesis", "7. Interpretación del modelo", "8. Análisis exploratorio",
           "9. Discusión y conclusiones", "10. Limitaciones y validez"]
if "pagina" not in st.session_state:
    st.session_state["pagina"] = PAGINAS[0]


def _ir(delta):
    i = PAGINAS.index(st.session_state["pagina"]) + delta
    st.session_state["pagina"] = PAGINAS[max(0, min(i, len(PAGINAS) - 1))]


st.sidebar.markdown("### Contenido")
pagina = st.sidebar.radio("Sección", PAGINAS, key="pagina", label_visibility="collapsed")
idx_pag = PAGINAS.index(pagina)
st.sidebar.progress(idx_pag / (len(PAGINAS) - 1), text=["Inicio", "Pregunta general"][idx_pag] if idx_pag < 2 else f"Sección {idx_pag - 1} de {len(PAGINAS) - 2}")
st.sidebar.divider()
with st.sidebar.expander("📖 Glosario rápido"):
    st.markdown("**MAE:** error absoluto medio; cuánto se equivoca el modelo en promedio (menor es mejor).  \n"
                "**Anomalía:** diferencia entre el valor de un año y lo normal del municipio.  \n"
                "**Línea base:** referencia simple (promedio o repetir el año anterior) contra la que se compara el modelo.  \n"
                "**Intervalo de confianza (IC):** rango plausible del efecto; si incluye el 0, no se distingue del ruido.  \n"
                "**Bootstrap:** remuestreo para estimar la incertidumbre.  \n"
                "**Fuga de datos:** usar información del futuro al entrenar.  \n"
                "**SHAP / permutación:** formas de medir cuánto usa el modelo cada variable.")
with st.sidebar.expander("⚙️ Origen de los datos"):
    carpeta = st.text_input("Carpeta con los CSV del notebook", CARPETA_DEFECTO)
    st.caption("Las cifras provienen de los CSV del notebook. Ningún modelo de lenguaje se usa como fuente de datos.")
if not (Path(carpeta) / "metricas_modelos.csv").exists():
    st.error(f"No se encontró `metricas_modelos.csv` en `{carpeta}`. Ejecute el notebook completo (sección 11) o corrija la ruta en la barra lateral.")
    st.stop()


@st.cache_data(show_spinner=False)
def cargar(carpeta, nombre, con_municipio=False):
    return R.leer(carpeta, nombre, dtype={"id_municipio": str} if con_municipio else None)


@st.cache_data(show_spinner="Calculando intervalos de confianza…")
def boot(carpeta):
    return R.comparaciones_bootstrap(cargar(carpeta, "predicciones_prueba.csv", True))


@st.cache_data(show_spinner=False)
def partes_resumen(carpeta):
    return R.construir_partes(carpeta)


met, pred, base = (cargar(carpeta, "metricas_modelos.csv"), cargar(carpeta, "predicciones_prueba.csv", True), cargar(carpeta, "base_modelado.csv", True))
hip, comp, kw = cargar(carpeta, "hipotesis_resultados.csv"), cargar(carpeta, "hipotesis_complementarias.csv"), cargar(carpeta, "kruskal_wallis_clima.csv")
abl, dsub, sint = cargar(carpeta, "ablacion_hipotesis.csv"), cargar(carpeta, "delta_por_subgrupo.csv"), cargar(carpeta, "sintesis_hipotesis.csv")
imp, shap_r, evid = cargar(carpeta, "importancia_permutacion.csv"), cargar(carpeta, "shap_resumen.csv"), cargar(carpeta, "evidencia_cultivo.csv")
clus, vif, clf = cargar(carpeta, "clusters_municipios.csv", True), cargar(carpeta, "vif_multicolinealidad.csv"), cargar(carpeta, "metricas_clasificacion.csv")
if any(x is None for x in (pred, base, hip, sint, imp)):
    st.error("Faltan archivos esenciales del tablero. Ejecute el notebook completo (sección 11).")
    st.stop()

P = partes_resumen(carpeta)
B = boot(carpeta)
ANIO_TR, A0, A1 = P["anios"]
f_clima, f_anio, f_todo = B.iloc[0], B.iloc[1], B.iloc[2]
n_mun, n_test = int(base["id_municipio"].nunique()), len(pred)
n_resp = int(sint["Veredicto"].fillna("").str.startswith("Respaldada").sum())
n_parc = int(sint["Veredicto"].fillna("").str.startswith("Respaldo parcial").sum())
n_sin = len(sint) - n_resp - n_parc
inconcluso = (n_resp + n_parc) == 0

# with st.sidebar.expander("⬇️ Descargas"):
#     st.download_button("Resumen ejecutivo (HTML)", R.a_html(P), file_name="resumen_ejecutivo.html", mime="text/html", width="stretch")
#     st.download_button("Resumen ejecutivo (Markdown)", R.a_markdown(P), file_name="resumen_ejecutivo.md", mime="text/markdown", width="stretch")
#     st.download_button("Verificación de cifras (CSV)", P["cifras"].to_csv(index=False).encode("utf-8-sig"), file_name="verificacion_cifras.csv", mime="text/csv", width="stretch")
#     st.caption("Para el PDF de 2 páginas: abrir el HTML en el navegador, Imprimir y Guardar como PDF (A4).")

def mae(prefijo):
    return float(met.loc[met["Modelo"].str.startswith(prefijo), "MAE prueba"].iloc[0])


B0, B1, B2, M1, M2 = (mae(p) for p in ["B0", "B1", "B2", "M1", "M2"])


EN_CLARO = {"H1": ("t_anomalia", "Un año más cálido que lo normal de su municipio se asocia con un menor rendimiento relativo."),
            "H2": ("t_anomalia × grupo", "La asociación negativa es más fuerte en cultivos transitorios (ciclo corto) que en permanentes."),
            "H3": ("t_anomalia × clima", "Un año cálido pesa más en municipios cuyo clima normal ya es cálido."),
            "H4": ("t_anomalia_prev", "La temperatura del año anterior también se asocia con el rendimiento, sobre todo en cultivos permanentes."),
            "H5": ("amplitud_anomalia", "Una amplitud térmica mayor que la normal se asocia con un menor rendimiento.")}

#   INICIO · RESUMEN PARA CUALQUIER PERSONA
if pagina == PAGINAS[0]:
    CONT.update(pg=0, t=0, f=0)
    st.markdown('<div class="portada"><div class="u">Valle del Cauca · Datos abiertos (datos.gov.co)</div>'
                '<h1>¿Los años más calurosos de lo normal afectan lo que producen los cultivos?</h1>'
                '<div class="s">Informe</div></div>', unsafe_allow_html=True)

    # Respuesta corta, calculada desde los resultados
    if inconcluso:
        caja("La respuesta corta", "**Con estos datos no pudimos comprobar que el calor fuera de lo normal explique la producción.** "
             "No quiere decir que no influya: significa que la información disponible no alcanza para afirmarlo con seguridad.", "warn")
    else:
        caja("La respuesta corta", f"**Sí encontramos señales** de que el calor fuera de lo normal se relaciona con la producción "
             f"({n_resp} de {len(sint)} ideas respaldadas y {n_parc} con respaldo parcial). Son relaciones, no pruebas de causa.", "ok")

    # Tres cifras grandes
    c1, c2, c3 = st.columns(3)
    kpi(c1, "Error del modelo con temperatura", R.pct(M2), "de equivocación sobre el rendimiento típico (menor es mejor)", "info")
    kpi(c2, "Error si solo repetimos el año anterior", R.pct(B1), "referencia muy simple", "gris")
    kpi(c3, "Ideas con respaldo", f"{n_resp + n_parc} de {len(sint)}", "hipótesis sobre el efecto de la temperatura", "ok" if not inconcluso else "warn")

    # Un solo gráfico
    st.markdown("#### ¿Qué tanto se equivoca cada forma de predecir?")
    sencillo = pd.DataFrame({"Forma de predecir": ["Adivinar el promedio", "Repetir el año anterior", "Modelo sin temperatura", "Modelo con temperatura"],
                             "Error": [B0, B1, B2, M2]})
    orden = sencillo.sort_values("Error")["Forma de predecir"].tolist()
    bs = alt.Chart(sencillo).encode(y=alt.Y("Forma de predecir:N", sort=orden, title=None, axis=alt.Axis(labelLimit=300, labelFontSize=13)),
                                     x=alt.X("Error:Q", title="Error (menor es mejor)"))
    st.altair_chart((bs.mark_bar().encode(color=alt.condition(alt.datum["Forma de predecir"] == "Modelo con temperatura", alt.value(AZUL), alt.value(GRIS)))
                     + bs.mark_text(align="left", dx=4, fontSize=13).encode(text=alt.Text("Error:Q", format=".2f"))).properties(height=190), width="stretch")
    st.caption("Cada barra mide qué tanto se aleja la predicción del rendimiento real en años que el modelo no había visto.")

    # Qué significa
    st.markdown("#### ¿Qué significa esto?")
    if M2 < B1:
        lectura_b1 = "El modelo con temperatura **se equivoca menos** que repetir el año anterior."
    else:
        lectura_b1 = "Repetir lo del año anterior resultó **igual o mejor** que nuestro modelo."
    lectura_b2 = ("Agregar la temperatura **mejoró** la predicción frente al mismo modelo sin ella." if M2 < B2
                  else "Agregar la temperatura **no mejoró** la predicción frente al mismo modelo sin ella.")
    st.markdown(f"- {lectura_b1}\n- {lectura_b2}\n- Esto es un hallazgo válido: un resultado que no confirma una idea también aporta información.")

    # Recomendaciones y cuidados (ya calculadas en el resumen ejecutivo)
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("#### Qué recomendamos")
        st.markdown("\n".join(f"{i}. {limpio(r)}" for i, r in enumerate(P["recs"], 1)))
    with r2:
        st.markdown("#### Qué tener en cuenta")
        st.markdown("\n".join(f"- **{limpio(t)}.** {limpio(d)}" for t, d in P["limites"]))

    st.info("¿Quiere ver cómo cambiaron el rendimiento y la temperatura año a año? Vaya a «Pregunta general». ¿Quiere ver cómo se hizo? Las secciones 1 a 10 del menú explican los datos, el método y las pruebas.")

#   PREGUNTA GENERAL · EVOLUCIÓN Y TEMPERATURA
elif pagina == PAGINAS[1]:
    CONT.update(pg="G", t=0, f=0)
    encabezado_libre("Pregunta general: evolución del rendimiento y relación con la temperatura",
                     "La pregunta de la Parte 2, respondida con los datos de los municipios que tienen estación del IDEAM")
    caja("Pregunta general (Parte 2)", "¿Cómo ha evolucionado el rendimiento de los principales cultivos del Valle del Cauca a lo largo del tiempo y qué relación "
         "existe entre sus variaciones y la temperatura registrada en los municipios donde se producen?")
    tiene_rend = "rendimiento_t_ha" in base.columns and base["rendimiento_t_ha"].notna().any()
    tiene_t = "t_media" in base.columns and base["t_media"].notna().any()
    MIN_N = 30
    CLIMA = {0: "Más frío", 1: "Templado", 2: "Más cálido"}

    def rho(a, b):
        ok = a.notna() & b.notna()
        return float(a[ok].corr(b[ok], method="spearman")) if ok.sum() >= 5 else np.nan

    def fuerza(r):
        if np.isnan(r):
            return "no calculable"
        a = abs(r)
        return "muy débil" if a < .1 else "débil" if a < .3 else "moderada" if a < .5 else "fuerte"

    corte = alt.Chart(pd.DataFrame({"x": [ANIO_TR + .5]})).mark_rule(color=NAVY, strokeDash=[4, 4]).encode(x="x:Q")
    cero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=NAVY, strokeDash=[2, 3]).encode(y="y:Q")
    ejex = alt.X("anio:Q", title="Año", axis=alt.Axis(format="d", tickMinStep=1))

    # ---- 1. Rendimiento
    seccion(1, "¿Cómo ha evolucionado el rendimiento?")
    if tiene_rend:
        top = base.groupby("cultivo").size().sort_values(ascending=False).index.tolist()
        sel = st.multiselect("Cultivos a mostrar", sorted(base["cultivo"].unique()), default=top[:4], key="pg_cultivos")
        dd = base[base["cultivo"].isin(sel)]
        if len(dd):
            ser = dd.groupby(["anio", "cultivo"], as_index=False)["rendimiento_t_ha"].median()
            leyenda("Figura", "Rendimiento mediano por año (toneladas por hectárea) en los municipios con estación; la línea punteada marca el fin del periodo de entrenamiento")
            ln = alt.Chart(ser).mark_line(point=True).encode(x=ejex, y=alt.Y("rendimiento_t_ha:Q", title="Rendimiento mediano (t/ha)"),
                                                             color=alt.Color("cultivo:N", title=None),
                                                             tooltip=["cultivo", "anio", alt.Tooltip("rendimiento_t_ha:Q", format=".2f")])
            st.altair_chart((ln + corte).properties(height=320), width="stretch")
        else:
            st.info("Seleccione al menos un cultivo.")
    else:
        st.caption("Para ver el rendimiento en toneladas por hectárea, agregue `rendimiento_t_ha` y `t_media` a `cols_base` en la sección 11 del notebook y vuelva a ejecutarlo. "
                   "Mientras tanto se muestra el rendimiento **relativo**.")
    rel = base.groupby(["anio", "grupo"], as_index=False)["y"].mean()
    leyenda("Figura", "Rendimiento relativo a lo normal por tipo de cultivo (0 = lo normal del periodo de entrenamiento; 0,10 = 10 % por encima de la mediana del cultivo)")
    lr = alt.Chart(rel).mark_line(point=True).encode(x=ejex, y=alt.Y("y:Q", title="Rendimiento relativo medio"), color=alt.Color("grupo:N", title=None),
                                                     tooltip=["grupo", "anio", alt.Tooltip("y:Q", format="+.3f")])
    st.altair_chart((lr + cero + corte).properties(height=300), width="stretch")
    st.caption("Antes de la línea punteada el promedio queda cerca de 0 por construcción (es el periodo con el que se definió lo normal). La información nueva está después de la línea.")

    # ---- 2. Temperatura
    seccion(2, "¿Cómo ha evolucionado la temperatura?")
    temp_anual = base.drop_duplicates(["id_municipio", "anio"]).groupby("anio", as_index=False).agg(t_anom=("t_anom", "mean"))
    temp_anual["Año"] = np.where(temp_anual["t_anom"] >= 0, "Más cálido que lo normal", "Más frío que lo normal")
    leyenda("Figura", "Anomalía media de temperatura por año (°C respecto a lo normal de cada municipio)")
    st.altair_chart((alt.Chart(temp_anual).mark_bar().encode(
        x=ejex, y=alt.Y("t_anom:Q", title="Anomalía media (°C)"),
        color=alt.Color("Año:N", scale=alt.Scale(domain=["Más cálido que lo normal", "Más frío que lo normal"], range=[ROJO, AZUL]), title=None),
        tooltip=["anio", alt.Tooltip("t_anom:Q", format="+.2f")]) + cero + corte).properties(height=260), width="stretch")
    if tiene_t:
        tm = base.drop_duplicates(["id_municipio", "anio"]).groupby("anio", as_index=False)["t_media"].mean()
        leyenda("Figura", "Temperatura media anual (°C) de los municipios con estación")
        st.altair_chart((alt.Chart(tm).mark_line(point=True, color=ROJO).encode(x=ejex, y=alt.Y("t_media:Q", title="Temperatura media (°C)", scale=alt.Scale(zero=False)),
                                                                              tooltip=["anio", alt.Tooltip("t_media:Q", format=".2f")]) + corte).properties(height=240), width="stretch")

    # ---- 3. Relación
    seccion(3, "¿Qué relación hay entre ambas?")
    anual = base.groupby("anio", as_index=False).agg(y=("y", "mean"), t_anom=("t_anom", "mean"))
    rho_anual = rho(anual["t_anom"], anual["y"])
    rho_glob = rho(base["t_anom"], base["y"])
    k1, k2, k3 = st.columns(3)
    kpi(k1, "Correlación, registro a registro", f"{rho_glob:+.2f}".replace(".", ","), f"{fuerza(rho_glob)} · {R.miles(len(base))} registros", "info")
    kpi(k2, "Correlación, promedios anuales", f"{rho_anual:+.2f}".replace(".", ","), f"{fuerza(rho_anual)} · solo {len(anual)} años", "gris")
    kpi(k3, "Cómo leerla", "−1 a +1", "0 = sin relación; negativa = año cálido, menor rendimiento", "gris")
    st.write("")
    leyenda("Figura", "Cada punto es un año: anomalía media de temperatura frente a rendimiento relativo medio")
    pa = alt.Chart(anual).encode(x=alt.X("t_anom:Q", title="Anomalía media de temperatura (°C)"), y=alt.Y("y:Q", title="Rendimiento relativo medio"))
    st.altair_chart((pa.mark_circle(size=90, color=AZUL) + pa.mark_text(dy=-12, fontSize=11, color="#333").encode(text=alt.Text("anio:Q", format="d"))
                     + pa.transform_regression("t_anom", "y").mark_line(color=NAVY, strokeDash=[5, 4])).properties(height=320), width="stretch")
    st.caption("Con pocos años, un solo punto puede cambiar la línea; por eso este gráfico orienta pero no concluye.")

    filas = []
    for g in sorted(base["grupo"].unique()):
        for c, nom in CLIMA.items():
            sub = base[(base["grupo"] == g) & (base["clima_ord"] == c)]
            filas.append({"Tipo de cultivo": g, "Clima del municipio": nom, "n": len(sub), "ρ": rho(sub["t_anom"], sub["y"]) if len(sub) >= MIN_N else np.nan})
    hm = pd.DataFrame(filas)
    leyenda("Figura", f"Correlación entre anomalía de temperatura y rendimiento relativo, por tipo de cultivo y clima (solo grupos con {MIN_N} registros o más)")
    hb = alt.Chart(hm.dropna(subset=["ρ"])).encode(x=alt.X("Clima del municipio:N", sort=list(CLIMA.values()), title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("Tipo de cultivo:N", title=None))
    st.altair_chart((hb.mark_rect(stroke="white", strokeWidth=3).encode(color=alt.Color("ρ:Q", scale=alt.Scale(domain=[-.4, 0, .4], range=[ROJO, "#FFFFFF", AZUL], clamp=True), title="ρ"),
                                                                       tooltip=["Tipo de cultivo", "Clima del municipio", "n", alt.Tooltip("ρ:Q", format="+.3f")])
                     + hb.mark_text(fontSize=14, color="#1E2A25").encode(text=alt.Text("ρ:Q", format="+.2f"))).properties(height=150), width="stretch")
    st.caption("Rojo: a más calor, menor rendimiento. Azul: a más calor, mayor rendimiento. Blanco: sin relación visible.")
    with st.expander("Tabla con el número de registros de cada grupo"):
        tabla(hm, {"n": "{:,.0f}", "ρ": "{:+.3f}"})

    # ---- 4. Respuesta
    seccion(4, "Respuesta a la pregunta general")
    a_ = anual.sort_values("anio")
    if len(a_) >= 6:
        ini, fin = float(a_["y"].head(3).mean()), float(a_["y"].tail(3).mean())
        dif = fin - ini
        tend = "**subió**" if dif > .02 else "**bajó**" if dif < -.02 else "**se mantuvo estable**"
        txt_evol = (f"**Evolución.** Entre {int(a_['anio'].min())} y {int(a_['anio'].max())}, el rendimiento relativo medio {tend}: pasó de {R.signed(ini, 3)} en los primeros "
                    f"tres años a {R.signed(fin, 3)} en los últimos tres (0 = lo normal de entrenamiento).")
    else:
        txt_evol = "**Evolución.** Hay pocos años para describir una tendencia."
    sentido = "negativa (años más cálidos, menor rendimiento)" if rho_glob < 0 else "positiva (años más cálidos, mayor rendimiento)"
    txt_rel = (f"**Relación.** La asociación entre la anomalía de temperatura y el rendimiento relativo es **{fuerza(rho_glob)}** (ρ = {R.signed(rho_glob, 2)}), de sentido {sentido}. "
               + ("Las pruebas formales de la sección 6 no logran distinguirla del ruido." if inconcluso else "Las pruebas formales de la sección 6 respaldan parte de las hipótesis."))
    caja("En palabras sencillas", f"{txt_evol}\n\n{txt_rel}", "warn" if inconcluso or abs(rho_glob) < .3 else "ok")
    caja("Con cuidado", "Es una **asociación, no una causa**: otros factores (lluvia, riego, plagas, precios) cambian al mismo tiempo. Además son datos de **municipios con estación**, "
         "no de fincas, y no representan a todo el Valle. El detalle de las pruebas está en las secciones 5 y 6.", "info")

#   1. PRESENTACIÓN
elif pagina == PAGINAS[2]:
    CONT.update(pg=1, t=0, f=0)
    st.markdown(f"""<div class="portada"><div class="u">Universidad Santiago de Cali · Facultad de Ingeniería</div>
<h1>Temperatura y rendimiento de los cultivos del Valle del Cauca</h1>
<div class="s">¿Mejora la anomalía térmica anual la predicción del rendimiento agrícola? Evidencia con datos abiertos de datos.gov.co</div>
<table><tr><td>Asignatura</td><td>Ciencia de Datos con Python (IGS38)</td></tr>
<tr><td>Caso de estudio</td><td>Analítica de datos abiertos de Colombia · Parte 3: modelos de aprendizaje automático y comunicación de resultados (RA5 y RA6)</td></tr>
<tr><td>Autor</td><td>{AUTOR}</td></tr><tr><td>Docente</td><td>{DOCENTE}</td></tr>
<tr><td>Fecha de generación</td><td>{datetime.now():%d/%m/%Y}</td></tr></table></div>""", unsafe_allow_html=True)

    seccion(1, "Resumen")
    st.markdown(
        f"Este trabajo del laboratorio 3 evalúa si conocer cuánto se desvió la temperatura de un municipio respecto a su valor normal permite predecir mejor el "
        f"rendimiento relativo de sus cultivos en años no observados. Se integraron los rendimientos agrícolas de la Gobernación del Valle del Cauca con la "
        f"temperatura del aire de las estaciones del IDEAM mediante el código DIVIPOLA. Los modelos (*gradient boosting* y *Ridge*) se entrenaron con años "
        f"hasta {ANIO_TR} y se evaluaron en {A0}-{A1} ({R.miles(n_test)} registros de {n_mun} municipios), contra tres referencias: promedio, persistencia "
        f"y el mismo algoritmo sin variables del IDEAM. Cada una de las cinco hipótesis se contrastó con una prueba estadística y con una prueba basada "
        f"en el modelo. **Resultado:** {limpio(P['respuesta'])}")
    cols = st.columns(4)
    for c, k in zip(cols, P["kpis"]):
        kpi(c, k["etiqueta"], k["valor"], k["nota"], k["tono"])
    st.caption("El error (MAE) se expresa como fracción del rendimiento típico del cultivo: 0,30 equivale a equivocarse en un 30 %. Menor es mejor.")

    seccion(2, "Resultados de un vistazo")
    g1, g2 = st.columns([3, 2])
    mm = met.assign(Rol=np.where(met["Tipo"] == "Línea base", "Línea base", "Modelo"))
    with g1:
        leyenda("Figura", "Error (MAE) de cada modelo en años no vistos; menor es mejor")
        bc = alt.Chart(mm).encode(x=alt.X("MAE prueba:Q", title="MAE en prueba"), y=alt.Y("Modelo:N", sort=mm.sort_values("MAE prueba")["Modelo"].tolist(), title=None, axis=alt.Axis(labelLimit=300)))
        st.altair_chart((bc.mark_bar().encode(color=alt.Color("Rol:N", scale=alt.Scale(domain=["Línea base", "Modelo"], range=[GRIS, AZUL]), title=None),
                                              tooltip=["Modelo", alt.Tooltip("MAE prueba:Q", format=".4f")])
                         + bc.mark_text(align="left", dx=4, fontSize=11, color="#333").encode(text=alt.Text("MAE prueba:Q", format=".3f"))).properties(height=max(200, 38 * len(mm))), width="stretch")
    with g2:
        leyenda("Figura", "Veredicto de cada hipótesis")
        vd = sint.assign(Resultado=sint["Veredicto"].map(lambda v: {"ok": "Respaldada", "warn": "Respaldo parcial", "mal": "Sin respaldo"}[tono_veredicto(v)]))
        st.altair_chart(alt.Chart(vd).mark_rect(cornerRadius=5, stroke="white", strokeWidth=4).encode(
            x=alt.X("ID:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=13, orient="top")),
            color=alt.Color("Resultado:N", scale=alt.Scale(domain=["Respaldada", "Respaldo parcial", "Sin respaldo"], range=[VERDE, ORO, ROJO]), title=None),
            tooltip=[c for c in ["ID", "Hipótesis", "Veredicto"] if c in vd.columns]).properties(height=110), width="stretch")
        st.caption("«Sin respaldo» no significa que el efecto no exista: estos datos no logran distinguirlo del ruido.")
    fuente("`metricas_modelos.csv` y `sintesis_hipotesis.csv`.")

    seccion(3, "Cómo usar este tablero")
    u1, u2, u3 = st.columns(3)
    for col, (n_, t_, d_) in zip([u1, u2, u3], [
            ("1", "Navegue", "Use el menú lateral o los botones ← → al final de cada sección. Si quiere el detalle técnico, siga el orden 1 a 10."),
            ("2", "Explore", "Las figuras son interactivas: pase el cursor sobre una barra o un punto para ver el valor exacto. Las secciones 5 y 8 tienen filtros."),
            ("3", "Consulte y descargue", "El glosario y las descargas (resumen ejecutivo y tabla de verificación de cifras) están en la barra lateral.")]):
        col.markdown(f'<div class="paso"><div class="n">{n_}</div><div class="t">{t_}</div><div class="d">{d_}</div></div>', unsafe_allow_html=True)

    seccion(4, "Estructura del documento")
    leyenda("Tabla", "Contenido del tablero y su relación con los resultados de aprendizaje")
    _cont = [
        "Pregunta de investigación, objetivos e hipótesis H1 a H5 con su formulación estadística (RA4).",
        "Fuentes, llaves de cruce, cobertura y partición temporal de la base de modelado (RA1, RA3).",
        "Diseño experimental: prevención de fuga, variables, líneas base, algoritmos y métricas (RA5).",
        "Desempeño en prueba, aporte marginal de la temperatura con intervalos de confianza, errores por subgrupo (RA5).",
        "Veredicto de cada hipótesis con dos pruebas independientes (estadística y de modelo) (RA4, RA5).",
        "Importancia por permutación y valores SHAP, conectados con las hipótesis (RA5).",
        "Exploración interactiva de la anomalía térmica frente al rendimiento y perfil climático de los municipios (RA4).",
        "Respuesta a la pregunta, lectura de un resultado concluyente o no, aportes y trabajo futuro (RA6).",
        "Amenazas a la validez: sesgo de cobertura, falacia ecológica, correlación frente a causalidad (RA6)."]
    _sec = PAGINAS[3:]
    _n = max(len(_sec), len(_cont))
    _sec, _cont = _sec + [""] * (_n - len(_sec)), _cont + [""] * (_n - len(_cont))
    tabla(pd.DataFrame({"Sección": _sec, "Contenido": _cont}), alto=420)

#   2. PLANTEAMIENTO
elif pagina == PAGINAS[3]:
    encabezado(2, "Planteamiento del problema", "Pregunta de investigación, objetivos e hipótesis")
    idea("Se busca saber si conocer cuánto se desvió la temperatura de lo normal ayuda a predecir el rendimiento en años que el modelo no vio. Son **cinco hipótesis**, cada una con **dos pruebas** independientes.")
    seccion(1, "Pregunta de investigación")
    caja("Pregunta general (Parte 2)", "¿Cómo ha evolucionado el rendimiento de los principales cultivos del Valle del Cauca a lo largo del tiempo y qué relación "
         "existe entre sus variaciones y la temperatura registrada en los municipios donde se producen?")
    caja("Pregunta de la Parte 3, en términos de modelo", "¿Un modelo que conoce la anomalía térmica del año (y del año anterior) predice el rendimiento relativo de un cultivo "
         "**mejor que uno que no la conoce**, cuando se evalúa en años que no vio al entrenar?")
    seccion(2, "Objetivos")
    st.markdown("**Objetivo general.** Determinar si la información de temperatura del IDEAM mejora, de forma comprobable, la predicción del rendimiento "
                "relativo de los cultivos del Valle del Cauca.\n\n**Objetivos específicos.**\n"
                "1. Construir variables de rendimiento y temperatura **sin fuga de datos**, de modo que la validación sea temporalmente honesta.\n"
                "2. Entrenar modelos de regresión y compararlos con líneas base que aíslen el aporte de la integración con el IDEAM.\n"
                "3. Contrastar cinco hipótesis con dos pruebas independientes cada una (estadística y de modelo).\n"
                "4. Interpretar el modelo final con importancia por permutación y valores SHAP.\n"
                "5. Comunicar resultados, limitaciones y recomendaciones a un público no técnico.")
    seccion(3, "Hipótesis")
    st.markdown("Las hipótesis nacen del análisis exploratorio del Laboratorio 2. Todas predicen un coeficiente **negativo** de la variable indicada, por lo que se "
                "contrastan de forma unilateral: **H₀: β ≥ 0** frente a **Hₐ: β < 0**. Las pruebas se corrigen por comparaciones múltiples (Holm).")
    leyenda("Tabla", "Hipótesis, variable de la integración y pruebas aplicadas")
    tabla(pd.DataFrame([
        ("H1", EN_CLARO["H1"][1], "t_anomalia", "Regresión con errores agrupados, Mann-Whitney, efectos fijos", "M2 vs M1 (bootstrap), ablación sin t_anom"),
        ("H2", EN_CLARO["H2"][1], "t_anomalia, grupo", "Interacción t_anomalia × transitorio; pendientes por grupo", "ΔMAE de M2 vs M1 por grupo"),
        ("H3", EN_CLARO["H3"][1], "t_anomalia, clima_municipio", "Interacción con clima; Kruskal-Wallis", "ΔMAE de M2 vs M1 por clima"),
        ("H4", EN_CLARO["H4"][1], "t_anomalia_prev", "Interacción con permanente; ΔR² del rezago", "Ablación sin t_anom_prev; permutación"),
        ("H5", EN_CLARO["H5"][1], "amplitud_anomalia", "Regresión y Spearman", "Ablación sin amp_anom; permutación y SHAP")],
        columns=["ID", "Enunciado", "Variable de la integración", "Prueba estadística", "Prueba con modelo"]), alto=250)
    fuente("Notebook de la Parte 3, mapa de hipótesis.")
    caja("Regla de decisión", "Una hipótesis se declara **respaldada** solo si la prueba estadística rechaza H₀ tras Holm **y** la prueba con modelo mejora con un "
         "intervalo *bootstrap* por encima de 0. Con una sola prueba hay **respaldo parcial**; con ninguna, **sin respaldo con estos datos**. "
         "Esta última categoría no demuestra que el efecto no exista: indica que estos datos no logran distinguirlo del ruido.", "warn")

#   3. DATOS
elif pagina == PAGINAS[4]:
    encabezado(3, "Datos y fuentes", "Origen, integración, cobertura y partición temporal")
    idea(f"Se cruzan los rendimientos (Gobernación) con la temperatura (IDEAM) mediante el código DIVIPOLA. Solo se modelan **{n_mun} municipios** con estación; el modelo se entrena con años hasta {ANIO_TR} y se prueba en {A0}-{A1}.")
    seccion(1, "Fuentes de datos y linaje")
    leyenda("Tabla", "Fuentes empleadas y llaves de cruce")
    tabla(pd.DataFrame([
        ("Cultivos del Valle del Cauca (7 conjuntos, Parte 1)", "Gobernación del Valle del Cauca", "id_municipio, anio, id_cultivo, ciclo", "Variable objetivo y controles"),
        ("Temperatura ambiente del aire (sbwg-7ju4)", "IDEAM", "id_municipio (DIVIPOLA) y anio", "Variables de la integración")],
        columns=["Fuente", "Entidad", "Llave de cruce", "Uso en el modelo"]))
    fuente("datos.gov.co. Las fechas de consulta y el porcentaje de cruce están en la tabla de linaje de la Parte 2 (`linaje_datos.csv`).")
    lin = next((R.leer(d, "linaje_datos.csv") for d in [carpeta, str(Path(carpeta).parent), "../laboratorio_2/data/procesados", "data/procesados"]
                if R.leer(d, "linaje_datos.csv") is not None), None)
    if lin is not None:
        leyenda("Tabla", "Linaje de datos (Parte 2)")
        tabla(lin)
    st.markdown("La llave común es el **código DIVIPOLA del DANE** (texto de 5 dígitos para municipio), con el que se unen los rendimientos agrícolas "
                "y la temperatura de las estaciones. Los municipios sin estación **no se imputan**: no tienen la variable de la integración.")
    seccion(2, "Base de modelado y partición temporal")
    st.markdown("Solo se modelan registros con rendimiento positivo y temperatura de referencia. La partición respeta el orden cronológico: el conjunto de "
                "prueba se evalúa **una sola vez** con el modelo final.")
    part = base.groupby("split").agg(Registros=("anio", "size"), Municipios=("id_municipio", "nunique"), Cultivos=("cultivo", "nunique"),
                                      Desde=("anio", "min"), Hasta=("anio", "max")).reindex(["entrenamiento", "validación", "prueba"]).dropna(how="all").reset_index()
    part = part.rename(columns={"split": "Conjunto"})
    leyenda("Tabla", "Partición temporal de la base de modelado")
    tabla(part, {"Registros": "{:,.0f}", "Municipios": "{:.0f}", "Cultivos": "{:.0f}", "Desde": "{:.0f}", "Hasta": "{:.0f}"})
    fuente("`base_modelado.csv`.")
    cnt = base.groupby(["anio", "split"]).size().reset_index(name="Registros")
    leyenda("Figura", "Registros por año y conjunto: la partición respeta el orden cronológico")
    st.altair_chart(alt.Chart(cnt).mark_bar().encode(
        x=alt.X("anio:O", title="Año", axis=alt.Axis(labelAngle=0)), y=alt.Y("Registros:Q", title="Registros"),
        color=alt.Color("split:N", scale=alt.Scale(domain=["entrenamiento", "validación", "prueba"], range=[AZUL, ORO, VERDE]), title=None),
        tooltip=[alt.Tooltip("anio:O", title="Año"), alt.Tooltip("split:N", title="Conjunto"), "Registros"]).properties(height=280), width="stretch")
    fuente("`base_modelado.csv`. Azul: entrenamiento; ámbar: validación; verde: prueba.")
    seccion(3, "Auditoría de fuga temporal")
    tr = base.loc[base["split"] == "entrenamiento", "anio"]
    va = base.loc[base["split"] == "validación", "anio"]
    te = pred["anio"]
    chk = [("Los años de entrenamiento son anteriores a los de validación", (tr.max() < va.min()) if len(tr) and len(va) else None),
           ("Los años de validación son anteriores a los de prueba", (va.max() < te.min()) if len(va) else None),
           ("Ningún año aparece en entrenamiento y en prueba", set(tr).isdisjoint(set(te))),
           ("La prueba usa solo años posteriores al corte de entrenamiento", bool(te.min() > ANIO_TR))]
    leyenda("Tabla", "Comprobaciones sobre los archivos guardados")
    tabla(pd.DataFrame([{"Comprobación": a, "Resultado": "Cumple" if b else ("No verificable" if b is None else "No cumple")} for a, b in chk]))
    st.markdown("Las anomalías de la Parte 2 se calcularon con todos los años, lo cual es válido para explorar pero **no para validar**: el rendimiento de un año "
                "se compararía con un promedio que lo incluye. Por eso en la Parte 3 toda \"normal histórica\" (mediana del cultivo, promedio del municipio-cultivo, "
                "temperatura normal y terciles de clima) se **recalcula solo con años de entrenamiento**. El notebook incluye una prueba de perturbación: "
                "se destruye el periodo de prueba (rendimientos ×10, temperaturas +5 °C) y se verifica que ninguna variable de entrenamiento ni de validación cambie.")
    caja("Alcance", f"Los resultados describen a los **{n_mun} municipios con estación del IDEAM y con historia suficiente**. El modelo no se extrapola al resto del Valle.", "warn")

#   4. METODOLOGÍA
elif pagina == PAGINAS[5]:
    encabezado(4, "Metodología", "Diseño experimental y justificación de cada decisión")
    idea("Todos los modelos usan el mismo algoritmo y solo cambia la información disponible (sin IDEAM, clima normal, clima normal más anomalías del año). Así se **aísla** el aporte de la temperatura.")
    seccion(1, "Variable objetivo")
    st.markdown("El objetivo `y` es el **rendimiento relativo respecto a lo normal del municipio**: el rendimiento dividido entre la mediana del cultivo, menos el promedio "
                "del municipio-cultivo-ciclo (ambos calculados solo con entrenamiento). El modelo no aprende \"este municipio rinde más\", sino "
                "\"este año rindió más o menos de lo habitual\", que es lo que la temperatura podría explicar.")
    seccion(2, "Conjuntos de variables escalonados")
    leyenda("Tabla", "Conjuntos de variables y pregunta que responde cada uno")
    tabla(pd.DataFrame([
        ("F_BASE", "es_perm, log_ha, y_prev", "Sin datos de la integración", "¿Qué tan bien se predice sin temperatura?"),
        ("F_NIVEL", "F_BASE + t_hist, clima_ord", "Clima normal del municipio", "¿Aporta saber **dónde** está el cultivo?"),
        ("F_COMPLETO", "F_NIVEL + t_anom, t_anom_prev, amp_anom", "Anomalías del año", "¿Aporta saber **cómo fue el año**? (la hipótesis)")],
        columns=["Conjunto", "Variables", "Información que agrega", "Pregunta"]))
    st.markdown("El escalonamiento permite **aislar** el efecto de la hipótesis: la comparación M2 frente a M1 solo cambia las anomalías del año.")
    seccion(3, "Líneas base y modelos")
    leyenda("Tabla", "Líneas base y modelos comparados")
    tabla(pd.DataFrame([
        ("B0", "Línea base", "Promedio del entrenamiento (≈ 0: \"el año rinde lo normal\")", "Piso mínimo de desempeño"),
        ("B1", "Línea base", "Persistencia: repite el objetivo del año anterior", "Referencia simple y exigente para planeación"),
        ("B2", "Modelo", "Boosting con F_BASE (sin integración)", "Aísla el aporte de la integración, no del algoritmo"),
        ("M1", "Modelo", "Boosting con F_NIVEL (clima normal)", "Aporte de saber dónde está el cultivo"),
        ("M2", "Modelo", "Boosting con F_COMPLETO (clima completo)", "Modelo principal; responde a H1 y H5")],
        columns=["ID", "Tipo", "Descripción", "Para qué sirve"]))
    seccion(4, "Selección del algoritmo")
    leyenda("Tabla", "Justificación de los algoritmos")
    tabla(pd.DataFrame([
        ("Relaciones no lineales e interacciones", "Las captura sin especificarlas", "Solo lineales"),
        ("Faltantes (t_anom_prev, y_prev)", "Los maneja de forma nativa", "Requiere imputación"),
        ("Pocos datos y cola larga", "Funciona con regularización", "Estable, difícil de sobreajustar"),
        ("Interpretación", "Permutación y SHAP", "Coeficientes directos")],
        columns=["Criterio", "HistGradientBoostingRegressor (principal)", "Ridge (contraste lineal)"]))
    st.markdown("Se ajustan ambos con la **misma cantidad de búsqueda de hiperparámetros** (elegidos por MAE en validación), para que la comparación sea justa. "
                "Como complemento se estiman una regresión lineal múltiple, una polinomial, cinco clasificadores y un análisis de clústeres (capítulos 9 a 11 del libro).")
    seccion(5, "Métricas y validación estadística")
    st.markdown("- **MAE** como métrica principal: el rendimiento tiene cola derecha larga (asimetría de 3,5 en la Parte 2) y el MAE es robusto; **RMSE** y **R²** como apoyo.\n"
                "- **Bootstrap por conglomerados (municipio-año):** los cultivos de un mismo municipio y año comparten la temperatura, por lo que no son observaciones independientes.\n"
                "- **Errores estándar agrupados por municipio** y **corrección de Holm** en los contrastes de hipótesis; **FDR de Benjamini-Hochberg** en el análisis exploratorio por cultivo.\n"
                "- **Validación prospectiva año a año** (ventana creciente) en lugar de k-fold aleatorio, que mezclaría años y filtraría el futuro al pasado.")
    caja("Por qué importa esta rigurosidad", "Un modelo evaluado con fuga de datos puede parecer mejor de lo que es. Cuando el diseño es honesto, un resultado "
         "que no supera a la línea base es **creíble**, y eso es más valioso que una mejora aparente que no sobreviviría en años futuros.", "ok")

#   5. RESULTADOS DEL MODELO
elif pagina == PAGINAS[6]:
    encabezado(5, "Resultados del modelo", f"Desempeño en años no vistos ({A0}-{A1}), n = {R.miles(n_test)} registros")
    idea(f"En años no vistos, el modelo con clima completo (M2) tiene un error de **{R.num(M2)}**; repetir el año anterior (B1), **{R.num(B1)}**, y el mismo modelo sin IDEAM (B2), **{R.num(B2)}**. Lo decisivo es si la diferencia entre M2 y M1 supera el ruido (sección 5.2).")
    seccion(1, "Desempeño frente a las líneas base")
    m = met.copy()
    m["Rol"] = np.where(m["Tipo"] == "Línea base", "Línea base", "Modelo")
    orden = m.sort_values("MAE prueba")["Modelo"].tolist()
    leyenda("Figura", "Error absoluto medio (MAE) en el conjunto de prueba; menor es mejor")
    bc = alt.Chart(m).encode(x=alt.X("MAE prueba:Q", title="MAE en prueba"), y=alt.Y("Modelo:N", sort=orden, title=None, axis=alt.Axis(labelLimit=420)))
    barras = bc.mark_bar().encode(color=alt.Color("Rol:N", scale=alt.Scale(domain=["Línea base", "Modelo"], range=[GRIS, AZUL]), title=None),
                                  tooltip=["Modelo", alt.Tooltip("MAE prueba:Q", format=".4f"), alt.Tooltip("R² prueba:Q", format=".3f")])
    st.altair_chart((barras + bc.mark_text(align="left", dx=4, fontSize=11, color="#333").encode(text=alt.Text("MAE prueba:Q", format=".3f"))).properties(height=max(220, 44 * len(m))), width="stretch")
    fuente("`metricas_modelos.csv`.")
    leyenda("Tabla", "Métricas completas (validación y prueba)")
    tabla(met)
    cmp_ = pd.DataFrame([
        ("M2 frente a B0 (promedio)", B0, M2), ("M2 frente a B1 (persistencia)", B1, M2), ("M2 frente a B2 (sin integración)", B2, M2)],
        columns=["Comparación", "MAE de referencia", "MAE de M2"])
    cmp_["Diferencia relativa"] = 1 - cmp_["MAE de M2"] / cmp_["MAE de referencia"]
    cmp_["Lectura"] = np.where(cmp_["Diferencia relativa"] > 0, "M2 tiene menor error", "M2 no mejora la referencia")
    leyenda("Tabla", "Comparación puntual de M2 con cada referencia (sin considerar la incertidumbre)")
    tabla(cmp_, {"Diferencia relativa": "{:+.1%}"})
    st.markdown("Una diferencia puntual **no basta**: con miles de registros una mejora diminuta puede ser ruido. La siguiente sección cuantifica la incertidumbre.")

    seccion(2, "Aporte marginal de la temperatura con intervalos de confianza")
    st.markdown("Diferencia de error absoluto registro a registro (positiva = el modelo con más información acierta más), con intervalo de confianza del 95 % "
                "mediante *bootstrap* por municipio-año (2 000 remuestreos). **Un intervalo que contiene el 0 indica que la diferencia no se distingue del ruido.**")
    Bc = B.assign(Resultado=B["Lectura"].map({"mejora distinguible del ruido": "Mejora comprobable", "empeora": "Empeora"}).fillna("No se distingue del ruido"))
    esc = alt.Scale(domain=["Mejora comprobable", "No se distingue del ruido", "Empeora"], range=[VERDE, GRIS, ROJO])
    leyenda("Figura", "Reducción del error (Δ MAE) con IC 95 % · a la derecha del 0 el modelo con más información mejora")
    ey = alt.Y("Comparación:N", title=None, axis=alt.Axis(labelLimit=420))
    rg = alt.Chart(Bc).mark_rule(strokeWidth=4).encode(y=ey, x=alt.X("IC95 inferior:Q", title="Δ MAE (referencia − modelo)"), x2="IC95 superior:Q",
                                                       color=alt.Color("Resultado:N", scale=esc, title=None))
    pt = alt.Chart(Bc).mark_point(filled=True, size=110, color=NAVY).encode(y="Comparación:N", x="Δ MAE (ref − modelo):Q",
        tooltip=["Comparación", alt.Tooltip("Δ MAE (ref − modelo):Q", format="+.5f"), alt.Tooltip("IC95 inferior:Q", format="+.5f"), alt.Tooltip("IC95 superior:Q", format="+.5f")])
    cero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=NAVY, strokeDash=[5, 4]).encode(x="x:Q")
    st.altair_chart((rg + pt + cero).properties(height=170), width="stretch")
    leyenda("Tabla", "Intervalos bootstrap de la diferencia de error")
    tabla(B, {"Δ MAE (ref − modelo)": "{:+.5f}", "IC95 inferior": "{:+.5f}", "IC95 superior": "{:+.5f}"})
    fuente("`predicciones_prueba.csv`, remuestreo por municipio-año (semilla 42).")
    cota = float(f_anio["IC95 superior"])
    caja("Lectura de la comparación central (M2 frente a M1)",
         f"Saber cómo fue el año frente a lo normal cambia el error en **{R.signed(f_anio['Δ MAE (ref − modelo)'], 5)}** "
         f"(IC 95 %: {R.signed(f_anio['IC95 inferior'], 5)} a {R.signed(f_anio['IC95 superior'], 5)}): *{f_anio['Lectura']}*. "
         f"Aun en el escenario más favorable compatible con los datos, la mejora no superaría **{R.num(max(cota, 0), 5)}** de MAE "
         f"(≈ {R.pct(max(cota, 0) / M1, 1)} del error de M1). Esta cota superior es un argumento cuantitativo: acota el tamaño del efecto que estos datos permitirían detectar.",
         "ok" if f_anio["Lectura"].startswith("mejora") else "warn")

    seccion(3, "Predicho frente a real")
    c1, c2, c3 = st.columns(3)
    etq = {"pred_B2": "B2 · sin datos del IDEAM", "pred_M1": "M1 · con clima normal", "pred_M2": "M2 · con clima completo"}
    col_pred = c1.selectbox("Modelo", list(etq), index=2, format_func=etq.get)
    grupos = c2.multiselect("Tipo de cultivo", sorted(pred["grupo"].unique()), default=sorted(pred["grupo"].unique()))
    anios = c3.multiselect("Año", sorted(pred["anio"].unique()), default=sorted(pred["anio"].unique()))
    d = pred[pred["grupo"].isin(grupos) & pred["anio"].isin(anios)]
    if len(d):
        lim, lim0 = (float(np.nanpercentile(np.r_[d["y_real"], d[col_pred]], q)) for q in (99, 1))
        pts = alt.Chart(d.sample(min(len(d), 4000), random_state=1)).mark_circle(opacity=.45, size=30).encode(
            x=alt.X("y_real:Q", title="Real", scale=alt.Scale(domain=[lim0, lim])), y=alt.Y(f"{col_pred}:Q", title="Predicho", scale=alt.Scale(domain=[lim0, lim])),
            color=alt.Color("grupo:N", title=None), tooltip=["municipio", "cultivo", "anio", alt.Tooltip("y_real:Q", format=".3f"), alt.Tooltip(f"{col_pred}:Q", format=".3f")])
        dg = alt.Chart(pd.DataFrame({"v": [lim0, lim]})).mark_line(color=NAVY, strokeDash=[4, 4]).encode(x="v:Q", y="v:Q")
        e1, e2 = st.columns(2)
        leyenda("Figura", "Valor predicho frente a valor real (línea punteada = predicción perfecta) y error medio por año")
        e1.altair_chart((pts + dg).properties(height=320), width="stretch")
        err = d.assign(error=(d["y_real"] - d[col_pred]).abs()).groupby("anio", as_index=False)["error"].mean()
        e2.altair_chart(alt.Chart(err).mark_bar(color=AZUL).encode(x=alt.X("anio:O", title="Año", axis=alt.Axis(labelAngle=0)), y=alt.Y("error:Q", title="Error absoluto medio"),
                                                                  tooltip=["anio", alt.Tooltip("error:Q", format=".3f")]).properties(height=320), width="stretch")
    else:
        st.info("Seleccione al menos un tipo de cultivo y un año.")

    seccion(4, "¿Dónde acierta y dónde falla?")
    st.markdown("Un promedio global puede ocultar que el modelo funciona en un grupo y no en otro. Se compara el error de M2 con el de B2 por subgrupo.")
    cc1, cc2 = st.columns(2)
    for col, nombre, cont in [("grupo", "Tipo de cultivo", cc1), ("anio", "Año de prueba", cc2)]:
        t = pred.assign(err_B2=(pred["y_real"] - pred["pred_B2"]).abs(), err_M2=(pred["y_real"] - pred["pred_M2"]).abs()).groupby(col).agg(
            Registros=("y_real", "size"), MAE_B2=("err_B2", "mean"), MAE_M2=("err_M2", "mean")).reset_index().rename(columns={col: nombre})
        t["Mejora de M2 sobre B2"] = 1 - t["MAE_M2"] / t["MAE_B2"]
        with cont:
            leyenda("Tabla", f"Error por {nombre.lower()}")
            tabla(t, {"Registros": "{:,.0f}", "Mejora de M2 sobre B2": "{:+.1%}"})
            largo = t.melt(id_vars=nombre, value_vars=["MAE_B2", "MAE_M2"], var_name="Modelo", value_name="MAE")
            largo["Modelo"] = largo["Modelo"].map({"MAE_B2": "B2 · sin IDEAM", "MAE_M2": "M2 · con IDEAM"})
            leyenda("Figura", f"MAE por {nombre.lower()}: B2 frente a M2")
            st.altair_chart(alt.Chart(largo).mark_bar().encode(
                x=alt.X(f"{nombre}:N", title=None, axis=alt.Axis(labelAngle=0)), xOffset="Modelo:N", y=alt.Y("MAE:Q", title="MAE en prueba"),
                color=alt.Color("Modelo:N", scale=alt.Scale(domain=["B2 · sin IDEAM", "M2 · con IDEAM"], range=[GRIS, AZUL]), title=None),
                tooltip=[nombre, "Modelo", alt.Tooltip("MAE:Q", format=".4f")]).properties(height=250), width="stretch")

    seccion(5, "Enfoques complementarios (capítulos 9 y 10)")
    if clf is not None:
        st.markdown("Se replantea la pregunta como clasificación: ¿el año rindió **por debajo de lo normal**? Se evalúa con y sin la integración del IDEAM, con la misma partición temporal y una línea base de clase mayoritaria.")
        leyenda("Tabla", "Métricas de clasificación en prueba")
        tabla(clf)
    if vif is not None:
        st.markdown("Para los modelos lineales se diagnosticó **multicolinealidad** mediante VIF (umbral 10), conservando siempre las tres anomalías de la hipótesis.")
        leyenda("Tabla", "Factor de inflación de la varianza (entrenamiento)")
        tabla(vif)
    if clf is None and vif is None:
        st.caption("Los archivos `metricas_clasificacion.csv` y `vif_multicolinealidad.csv` no están en la carpeta; se generan en la sección 11 del notebook.")

#   6. HIPÓTESIS
elif pagina == PAGINAS[7]:
    encabezado(6, "Contraste de hipótesis H1 a H5", "Cada hipótesis se probó dos veces: con una prueba estadística y con el modelo")
    idea(f"**{n_resp}** hipótesis respaldadas por ambas pruebas, **{n_parc}** con respaldo parcial y **{n_sin}** sin respaldo con estos datos. «Sin respaldo» no equivale a «falsa».")
    seccion(1, "Síntesis")
    leyenda("Tabla", "Veredicto por hipótesis")
    tabla(sint[[c for c in ["ID", "Hipótesis", "Veredicto"] if c in sint.columns]], alto=240)
    c1, c2, c3 = st.columns(3)
    kpi(c1, "Respaldadas por ambas pruebas", n_resp, "estadística y de modelo", "ok" if n_resp else "gris")
    kpi(c2, "Con respaldo parcial", n_parc, "solo una de las dos pruebas", "warn" if n_parc else "gris")
    kpi(c3, "Sin respaldo con estos datos", n_sin, "no distinguibles del ruido", "mal" if n_sin else "gris")
    st.write("")
    caja("Cómo leer \"sin respaldo\"", "Un resultado no significativo **no demuestra** que la hipótesis sea falsa: indica que, con el tamaño muestral disponible "
         f"({n_mun} municipios y {A1 - A0 + 1} años de prueba), no es posible distinguir el efecto del ruido. La ausencia de evidencia no es evidencia de ausencia.", "warn")
    seccion(2, "Efecto estimado por hipótesis")
    st.markdown("Cada fila muestra el coeficiente β con su intervalo de confianza del 95 %. Las hipótesis predicen β < 0 (a la izquierda del 0). "
                "**Si el intervalo cruza el 0, el efecto no se distingue del ruido.**")
    if {"β", "IC95 inf", "IC95 sup"}.issubset(hip.columns):
        leyenda("Figura", "Coeficientes β por hipótesis con IC 95 % (errores agrupados por municipio)")
        st.altair_chart(forest(hip["ID"], hip["β"], hip["IC95 inf"], hip["IC95 sup"], "β (IC 95 %)"), width="stretch")
        fuente("`hipotesis_resultados.csv`.")
    seccion(3, "Detalle por hipótesis")
    tabs = st.tabs(sint["ID"].tolist())
    for tab, (_, fila) in zip(tabs, sint.iterrows()):
        hid = fila["ID"]
        with tab:
            v = str(fila["Veredicto"])
            var, txt = EN_CLARO.get(hid, ("", ""))
            st.markdown(f"**Enunciado.** {txt}  \n**Variable:** `{var}` · **Contraste:** H₀: β ≥ 0 frente a Hₐ: β < 0 (unilateral)")
            st.markdown(f"**Veredicto:** {badge(v.upper(), tono_veredicto(v))}", unsafe_allow_html=True)
            if v.startswith("Sin respaldo"):
                st.caption("«Sin respaldo» no significa que el efecto no exista: estos datos no logran distinguirlo del ruido.")
            a, b = st.columns(2)
            a.markdown(f'<div class="hip"><b>Prueba estadística</b><br>{R._inline(fila.get("Prueba estadística", ""))}</div>', unsafe_allow_html=True)
            b.markdown(f'<div class="hip"><b>Prueba con modelo</b><br>{R._inline(fila.get("Prueba con modelo", ""))}</div>', unsafe_allow_html=True)
            ids = {"H1": ["H1"], "H2": ["H2"], "H3": ["H3"], "H4": ["H4a", "H4b"], "H5": ["H5"]}.get(hid, [hid])
            F = {"β": "{:+.4f}", "IC95 inf": "{:+.4f}", "IC95 sup": "{:+.4f}", "p bilateral": "{:.3g}", "p unilateral (Ha: β<0)": "{:.3g}", "p Holm": "{:.3g}", "N": "{:,.0f}"}
            leyenda("Tabla", f"Contraste principal de {hid} (errores agrupados por municipio, corrección de Holm)")
            tabla(hip[hip["ID"].isin(ids)], F)
            if comp is not None and (comp["ID"] == hid).any():
                leyenda("Tabla", f"Pruebas complementarias de {hid}")
                tabla(comp[comp["ID"] == hid], {"Estimador": "{:+.4f}", "IC95 inf": "{:+.4f}", "IC95 sup": "{:+.4f}", "p bilateral": "{:.3g}", "ΔR² por el rezago": "{:+.5f}"})
            if hid == "H3" and kw is not None and len(kw):
                leyenda("Tabla", "Prueba de Kruskal-Wallis entre climas")
                tabla(kw, {"H de Kruskal-Wallis": "{:.2f}", "p": "{:.3g}"})
            if hid in ("H1", "H4", "H5") and abl is not None:
                leyenda("Tabla", f"Ablación: ¿empeora la predicción al quitar la variable de {hid}?")
                tabla(abl[abl["Hipótesis"] == hid], {"Δ MAE (sin − con)": "{:+.5f}", "IC95 inferior": "{:+.5f}", "IC95 superior": "{:+.5f}"})
                forest_tabla(abl[abl["Hipótesis"] == hid], "Δ MAE (sin − con)", "Δ MAE (sin − con), IC 95 %", "Ablación: a la derecha del 0, quitar la variable empeora la predicción")
            if hid in ("H2", "H3") and dsub is not None:
                leyenda("Tabla", f"¿Ayudan más las anomalías del año en los subgrupos de {hid}?")
                tabla(dsub[dsub["Hipótesis"] == hid], {"Δ MAE (M1 − M2)": "{:+.5f}", "IC95 inferior": "{:+.5f}", "IC95 superior": "{:+.5f}"})
                forest_tabla(dsub[dsub["Hipótesis"] == hid], "Δ MAE (M1 − M2)", "Δ MAE (M1 − M2), IC 95 %", "Mejora de M2 sobre M1 por subgrupo: a la derecha del 0, las anomalías del año ayudan")
    st.caption("Con pocos municipios (conglomerados) los errores agrupados son aproximados; los valores p son orientativos.")

#   7. INTERPRETACIÓN
elif pagina == PAGINAS[8]:
    encabezado(7, "Interpretación del modelo", "Importancia por permutación y valores SHAP sobre el modelo final (M2)")
    idea("La importancia mide cuánto **usa** el modelo cada variable, no cuánto la **causa**. Las barras verdes son las variables derivadas de la temperatura del IDEAM.")
    seccion(1, "Importancia por permutación")
    st.markdown("Mide cuánto **empeora el MAE** al desordenar una variable en el conjunto de prueba. Es una medida global y honesta porque usa datos no vistos.")
    leyenda("Figura", "Aumento del error al desordenar cada variable (verde: integración con el IDEAM)")
    st.altair_chart(alt.Chart(imp).mark_bar().encode(
        x=alt.X("aumento_MAE:Q", title="Aumento del MAE"), y=alt.Y("etiqueta:N", sort="-x", title=None, axis=alt.Axis(labelLimit=340)),
        color=alt.Color("origen:N", scale=alt.Scale(domain=["Integración (IDEAM)", "Cultivos (Parte 1)"], range=[VERDE, GRIS]), title=None),
        tooltip=["etiqueta", alt.Tooltip("aumento_MAE:Q", format=".5f"), alt.Tooltip("desv:Q", format=".5f")]).properties(height=max(260, 28 * len(imp))), width="stretch")
    fuente("`importancia_permutacion.csv` (30 repeticiones).")
    top = imp.sort_values("aumento_MAE", ascending=False).iloc[0]
    pos = imp["aumento_MAE"].clip(lower=0)
    anom = imp[imp["variable"].isin(["t_anom", "t_anom_prev", "amp_anom"])] if "variable" in imp.columns else imp.iloc[0:0]
    cuota_anom = float(anom["aumento_MAE"].clip(lower=0).sum() / max(pos.sum(), 1e-12))
    caja("Lectura", f"La variable más usada es *{str(top['etiqueta']).lower()}*. Las variables del IDEAM suman {R.pct(P['cifras'].loc[P['cifras']['Cifra'].str.contains('Importancia de las variables'), 'Valor'].iloc[0])} "
         f"de la importancia total y las **tres anomalías del año**, {R.pct(cuota_anom)}. Si las anomalías pesan poco, el modelo se apoya sobre todo en el historial del cultivo y en el clima normal, "
         "coherente con la lectura de la sección 5.2.")
    if shap_r is not None:
        seccion(2, "Valores SHAP")
        st.markdown("Cuánto empuja cada variable la predicción, registro a registro (promedio del valor absoluto). Complementa a la permutación porque muestra además el **sentido** del efecto.")
        leyenda("Figura", "Efecto medio de cada variable sobre la predicción (|SHAP|)")
        st.altair_chart(alt.Chart(shap_r).mark_bar(color=ORO).encode(x=alt.X("mean_abs_shap:Q", title="|SHAP| medio"),
            y=alt.Y("etiqueta:N", sort="-x", title=None, axis=alt.Axis(labelLimit=340)),
            tooltip=["etiqueta", alt.Tooltip("mean_abs_shap:Q", format=".5f")]).properties(height=max(260, 28 * len(shap_r))), width="stretch")
    dir_fig = next((q for q in ["figuras", "../figuras", str(Path(carpeta).parents[1] / "figuras") if len(Path(carpeta).parents) > 1 else "figuras"] if (Path(q) / "shap_beeswarm.png").exists()), None)
    if dir_fig:
        with st.expander("Figuras SHAP del notebook"):
            for f in ["shap_beeswarm.png", "shap_dependencia_t_anom.png"]:
                if (Path(dir_fig) / f).exists():
                    st.image(str(Path(dir_fig) / f))
    seccion(3, "Conexión con las hipótesis")
    st.markdown("- **H1** se vincula con `t_anom`; **H4**, con `t_anom_prev`; **H5**, con `amp_anom`: la ablación y la permutación miden cuánto empeora la predicción sin ellas.\n"
                "- **H2 y H3** dependen de `grupo` y `clima_ord`: se evalúan por subgrupo en la sección 6.")
    caja("Cautela interpretativa", "La importancia mide cuánto **usa** el modelo una variable, no que **cause** el rendimiento. Además, `t_hist` y `clima_ord` identifican al municipio: "
         "parte de su importancia es geografía, no clima del año.", "warn")

#   8. EXPLORADOR
elif pagina == PAGINAS[9]:
    encabezado(8, "Análisis exploratorio", "Anomalía de temperatura frente a anomalía del rendimiento")
    idea("Cada punto es un cultivo en un municipio y año. Si la nube no muestra una pendiente clara, la temperatura sola no explica las variaciones del rendimiento. Use los filtros para explorar cultivos o municipios concretos.")
    st.markdown("Cada punto es un cultivo en un municipio y año. **Eje X:** desviación de la temperatura respecto a lo normal del municipio. "
                "**Eje Y:** desviación del rendimiento respecto a lo normal de ese cultivo en ese municipio (calculadas solo con entrenamiento).")
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
        k1, k2, _ = st.columns([1, 1, 2])
        kpi(k1, "Registros", f"{len(d):,}".replace(",", "."), "con los filtros actuales")
        kpi(k2, "Correlación de Spearman", f"{rho:+.3f}".replace(".", ","), "cerca de 0 = sin asociación visible", "info")
        pts = alt.Chart(d.sample(min(len(d), 4000), random_state=1)).mark_circle(opacity=.35, size=25).encode(
            x=alt.X("t_anom:Q", title="Anomalía de temperatura (°C)"), y=alt.Y("y:Q", title="Anomalía del rendimiento relativo"), color=alt.Color("grupo:N", title=None),
            tooltip=["municipio", "cultivo", "anio", alt.Tooltip("t_anom:Q", format=".2f"), alt.Tooltip("y:Q", format=".3f")])
        leyenda("Figura", "Dispersión de anomalías con ajuste lineal descriptivo")
        st.altair_chart((pts + pts.transform_regression("t_anom", "y").mark_line(color=NAVY, strokeWidth=2.5)).properties(height=380), width="stretch")
        st.caption("La línea es un ajuste lineal simple, solo descriptivo; no establece causalidad.")
        ser = d.groupby("anio", as_index=False).agg(t=("t_anom", "mean"), y=("y", "mean"))
        leyenda("Figura", "Evolución anual de la anomalía media de temperatura (rojo) y de rendimiento (verde), con los filtros actuales")
        eje = alt.Chart(ser).encode(x=alt.X("anio:O", title="Año", axis=alt.Axis(labelAngle=0)))
        st.altair_chart(alt.layer(
            eje.mark_line(color=ROJO, point=True).encode(y=alt.Y("t:Q", title="Anomalía de temperatura media (°C)", axis=alt.Axis(titleColor=ROJO)), tooltip=["anio", alt.Tooltip("t:Q", format="+.2f")]),
            eje.mark_line(color=VERDE, point=True).encode(y=alt.Y("y:Q", title="Anomalía de rendimiento media", axis=alt.Axis(titleColor=VERDE)), tooltip=["anio", alt.Tooltip("y:Q", format="+.3f")]),
        ).resolve_scale(y="independent").properties(height=300), width="stretch")
        st.caption("Cada eje tiene su propia escala; la figura sirve para comparar el momento de los picos, no la magnitud.")
    if evid is not None:
        seccion(1, "Asociación por cultivo (exploratoria)")
        st.markdown("Estas pruebas nacieron de observar los datos por cultivo, por lo que se corrigen por comparaciones múltiples (FDR) y se leen como **descriptivas**, no como confirmación.")
        e = evid.copy()
        e["¿Significativa tras FDR?"] = np.where(e["p_FDR"] < R.ALFA, "Sí", "No")
        leyenda("Figura", "Correlación de Spearman entre anomalía de temperatura y rendimiento, por cultivo")
        st.altair_chart(alt.Chart(e).mark_bar().encode(x=alt.X("rho:Q", title="ρ de Spearman"), y=alt.Y("cultivo:N", sort="x", title=None),
            color=alt.Color("¿Significativa tras FDR?:N", scale=alt.Scale(domain=["Sí", "No"], range=[ROJO, "#C9CED6"])),
            tooltip=["cultivo", "n", alt.Tooltip("rho:Q", format="+.3f"), alt.Tooltip("p_FDR:Q", format=".3g")]).properties(height=max(300, 18 * len(e))), width="stretch")
    if clus is not None:
        seccion(2, "Perfil climático de los municipios (capítulo 11)")
        st.markdown("Con pocos municipios con estación, el análisis de clústeres (PCA, k-means, jerárquico, espectral y DBSCAN) pregunta cuántos tipos de clima existen y si coinciden con los terciles de temperatura.")
        if {"t_hist", "amp_hist", "cluster_kmeans"}.issubset(clus.columns):
            leyenda("Figura", "Municipios según temperatura y amplitud normales, coloreados por clúster de k-means")
            st.altair_chart(alt.Chart(clus).mark_circle(size=140, opacity=.85).encode(x=alt.X("t_hist:Q", title="Temperatura normal (°C)", scale=alt.Scale(zero=False)),
                y=alt.Y("amp_hist:Q", title="Amplitud térmica normal (°C)", scale=alt.Scale(zero=False)), color=alt.Color("cluster_kmeans:N", title="Clúster"),
                tooltip=[c for c in ["municipio", "t_hist", "amp_hist", "cluster_kmeans"] if c in clus.columns]).properties(height=340), width="stretch")
        with st.expander("Tabla de municipios y clústeres"):
            tabla(clus)

#   9. DISCUSIÓN
elif pagina == PAGINAS[10]:
    encabezado(9, "Discusión y conclusiones", "Respuesta a la pregunta, lectura de los resultados y aportes del trabajo")
    idea("La respuesta a la pregunta de investigación está en el cuadro de la sección 9.1; el resto de la sección explica cómo leerla y qué falta para mejorarla.")
    seccion(1, "Respuesta a la pregunta de investigación")
    caja(P["pregunta"], P["respuesta"], P["tono"] if P["tono"] != "ok" else "ok")
    seccion(2, "Síntesis de resultados")
    for i, h in enumerate(P["hallazgos"], 1):
        st.markdown(f"{i}. {h}")
    seccion(3, "Cómo interpretar un resultado no concluyente")
    if inconcluso:
        st.markdown("**Este es el caso del presente estudio:** ninguna hipótesis alcanza respaldo en las dos pruebas. Esto **no invalida el trabajo**; al contrario, "
                    "un diseño honesto debe poder reportar un resultado nulo. Los argumentos que lo sostienen son los siguientes.")
    else:
        st.markdown("Aunque parte de las hipótesis tiene respaldo, las que quedaron **sin respaldo** (y la comparación M2 frente a M1, si resultó indistinguible del ruido) se "
                    "interpretan con estos mismos argumentos.")
    st.markdown(
        "1. **Ausencia de evidencia no es evidencia de ausencia.** Un intervalo que incluye el 0 indica que el efecto no puede distinguirse del ruido con estos datos, no que sea cero. "
        f"La cota superior del IC 95 % (sección 5.2) acota cuánto podría mejorar la predicción, como máximo: {R.num(max(float(f_anio['IC95 superior']), 0), 5)} de MAE para las anomalías del año.\n"
        "2. **La validación es creíble precisamente porque es estricta.** Con partición temporal, normales recalculadas solo con entrenamiento y una prueba de perturbación, "
        "una mejora aparente no puede deberse a fuga de información del futuro. Un modelo con fuga habría \"confirmado\" la teoría con resultados que no se sostendrían en años nuevos.\n"
        "3. **Se contrastó contra referencias exigentes.** Repetir el año anterior (B1) y el mismo algoritmo sin temperatura (B2) son comparaciones difíciles de superar; "
        "que la temperatura no las mejore de forma comprobable es información sobre el problema, no un defecto del método.\n"
        "4. **Se usaron dos pruebas independientes por hipótesis** y corrección por comparaciones múltiples, lo que reduce el riesgo de falsos positivos al costo de potencia: "
        "es una decisión deliberada de rigor.\n"
        "5. **Se reportó la incertidumbre con intervalos** y no solo con valores puntuales, de modo que el lector puede juzgar el tamaño del efecto y no únicamente su significancia.")
    seccion(4, "Explicaciones alternativas plausibles")
    caja("Hipótesis para trabajo futuro (no verificadas con estos datos)",
         "- **Potencia estadística limitada:** pocos municipios con estación y pocos años de prueba hacen amplios los intervalos.\n"
         "- **Error de medición:** una estación no representa a todo el municipio (altitud, microclima), lo que atenúa cualquier efecto real.\n"
         "- **Agregación temporal:** la temperatura media anual promedia olas de calor y heladas; los eventos extremos por etapa del cultivo podrían pesar más.\n"
         "- **Variables omitidas:** lluvia, sequías, inundaciones, riego, plagas, tecnología y precios probablemente explican más variación que la temperatura.\n"
         "- **Persistencia del rendimiento:** el rendimiento del año anterior ya resume parte del entorno del cultivo, lo que deja poco margen a la temperatura.", "warn")
    seccion(5, "Aportes del trabajo, independientemente del resultado")
    st.markdown("- Una **tubería reproducible** de integración (DIVIPOLA) y modelado sin fuga, aplicable a otras variables o territorios.\n"
                "- Una **cuantificación del tamaño máximo del efecto** detectable con los datos disponibles.\n"
                "- Una **evaluación comparativa** de regresión, clasificación y clústeres con una misma partición temporal.\n"
                "- Un diagnóstico claro de **qué datos faltan** para responder la pregunta, que orienta la inversión en información.")
    seccion(6, "Recomendaciones")
    for i, r in enumerate(P["recs"], 1):
        st.markdown(f"{i}. {r}")
    seccion(7, "Conclusión")
    st.markdown(f"Con los datos abiertos disponibles para {n_mun} municipios, {A0}-{A1} como periodo de prueba y una validación libre de fuga, "
                f"{'**no se logró comprobar** que la temperatura mejore la predicción del rendimiento' if inconcluso else 'la temperatura muestra **señales parciales** sobre el rendimiento'}. "
                "El estudio establece un punto de partida metodológicamente sólido y delimita con claridad lo que falta para una respuesta definitiva.")

#   10. LIMITACIONES
elif pagina == PAGINAS[11]:
    encabezado(10, "Limitaciones y amenazas a la validez", "Qué no dice este análisis")
    idea("Qué **no** permite concluir este estudio: cobertura limitada a municipios con estación, datos municipales (no de fincas) y asociación sin causalidad.")
    seccion(1, "Limitaciones exigidas por el caso de estudio")
    for t, dsc in R.limitaciones(n_mun):
        caja(t, dsc, "warn")
    seccion(2, "Amenazas a la validez")
    leyenda("Tabla", "Clasificación de las amenazas y medidas adoptadas")
    tabla(pd.DataFrame([
        ("Interna", "Fuga de datos; dependencia entre observaciones", "Normales solo con entrenamiento y prueba de perturbación; errores agrupados y bootstrap por municipio-año"),
        ("Externa", "Solo municipios con estación; estaciones no aleatorias", "Alcance declarado; sin extrapolar al resto del Valle"),
        ("De constructo", "Una estación no equivale al municipio; cambios de estación entre años; estación oceánica de Malpelo", "Se declara el sesgo de medición; mejora prevista: anomalía por estación"),
        ("De conclusión", "Pocos años y conglomerados; comparaciones múltiples; normales con pocos años (mínimo 4)", "Intervalos de confianza, Holm, FDR y lectura prudente de los valores p")],
        columns=["Tipo de validez", "Amenaza", "Medida adoptada"]), alto=210)
    seccion(3, "Otras limitaciones")
    st.markdown("- **Solo temperatura:** el rendimiento también depende de lluvia, riego, plagas, tecnología y precios.\n"
                "- **Periodos distintos:** cultivos transitorios hasta 2022 y permanentes hasta 2023 (heredado de la Parte 1).\n"
                "- **Correlación no es causalidad:** ni la importancia ni SHAP demuestran que un año cálido *cause* menor rendimiento.")
    seccion(4, "Uso de modelos de lenguaje")
    st.markdown("El resumen ejecutivo y este tablero **no usan un modelo de lenguaje como fuente de datos**: las cifras se leen de los CSV del notebook y cada una queda registrada "
                "en la tabla de verificación de cifras (descargable desde la barra lateral). Si se usa un modelo de lenguaje para pulir la redacción, cada número debe verificarse contra esa tabla.")


#  navegación inferior
st.divider()
nav_a, nav_b, nav_c = st.columns([2, 3, 2])
if idx_pag > 0:
    nav_a.button(f"← {PAGINAS[idx_pag - 1]}", on_click=_ir, args=(-1,), width="stretch", key="nav_prev")
nav_b.markdown(f'<div class="pie">{AUTOR} · Docente: {DOCENTE}</div>', unsafe_allow_html=True)
if idx_pag < len(PAGINAS) - 1:
    nav_c.button(f"{PAGINAS[idx_pag + 1]} →", on_click=_ir, args=(1,), width="stretch", key="nav_next")