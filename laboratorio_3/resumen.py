import html
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ALFA = 0.05
SEMILLA = 42
MAX_PALABRAS = 850

#  lectura
def leer(carpeta, nombre, **kw):
    ruta = Path(carpeta) / nombre
    return pd.read_csv(ruta, **kw) if ruta.exists() else None


def encontrar_carpeta(candidatos=None):
    candidatos = candidatos or ["data/procesados/tablero", "../data/procesados/tablero", "tablero", "."]
    for c in candidatos:
        if (Path(c) / "metricas_modelos.csv").exists():
            return str(c)
    return None


#  bootstrap (idéntico al del notebook, sección 7)
def bootstrap_delta(y, p_ref, p_mod, clusters, n=2000, seed=SEMILLA):
    d = np.abs(y - p_ref) - np.abs(y - p_mod)                 # > 0: el modelo mejora
    g = pd.DataFrame({"c": clusters, "d": d}).groupby("c")["d"].agg(["sum", "count"])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(n, len(g)))
    boots = g["sum"].to_numpy()[idx].sum(1) / g["count"].to_numpy()[idx].sum(1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi)


def lectura_ic(lo, hi):
    if lo > 0:
        return "mejora distinguible del ruido"
    if hi < 0:
        return "empeora"
    return "no se distingue del ruido"


def comparaciones_bootstrap(pred, n=2000):
    y = pred["y_real"].to_numpy()
    cl = (pred["id_municipio"].astype(str) + "_" + pred["anio"].astype(str)).to_numpy()
    filas = []
    for etiqueta, ref, mod in [("M1 vs B2 (clima normal del municipio)", "pred_B2", "pred_M1"),
                               ("M2 vs M1 (cómo fue el año frente a lo normal)", "pred_M1", "pred_M2"),
                               ("M2 vs B2 (toda la información del IDEAM)", "pred_B2", "pred_M2")]:
        d, lo, hi = bootstrap_delta(y, pred[ref].to_numpy(), pred[mod].to_numpy(), cl, n=n)
        filas.append({"Comparación": etiqueta, "Δ MAE (ref − modelo)": d, "IC95 inferior": lo, "IC95 superior": hi,
                      "Lectura": lectura_ic(lo, hi)})
    return pd.DataFrame(filas)


#  formato (coma decimal, punto de miles)
def num(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


def signed(x, d=3):
    return f"{x:+.{d}f}".replace(".", ",")


def miles(x):
    return f"{int(x):,}".replace(",", ".")


def pct(x, d=0):
    return f"{x * 100:.{d}f} %".replace(".", ",")


def corto(nombre):
    """'H1 · Anomalía…' -> 'H1'."""
    return str(nombre).split("·")[0].strip()


def limitaciones(n_mun):
    return [
        ("Sesgo de cobertura", f"Solo hay temperatura en municipios con estación del IDEAM y con historia suficiente: los resultados describen "
         f"a esos {n_mun} municipios y **no se extienden al resto del Valle**. Las estaciones no se reparten al azar y pueden estar a otra "
         "altitud que las zonas agrícolas."),
        ("Falacia ecológica", "Los datos son municipales: describen municipios, no fincas ni personas. Lo que se observa en el promedio de "
         "un municipio no tiene por qué ocurrir en cada productor."),
        ("Correlación no es causalidad", "Que una variable ayude a predecir no demuestra que cause el cambio de rendimiento; este también depende "
         "de lluvia, riego, plagas, tecnología y precios, que no están en el modelo."),
        ("Incertidumbre", "Pocos años de prueba y pocos municipios: los intervalos de confianza son amplios y las comparaciones múltiples se corrigieron."),
    ]


#  construcción del resumen
def construir_partes(carpeta, n_boot=2000):
    """Devuelve un diccionario con todas las partes del resumen y la tabla de verificación de cifras."""
    cifras = []

    def reg(descripcion, valor, fuente):
        cifras.append({"Cifra": descripcion, "Valor": valor, "Archivo de origen": fuente})
        return valor

    met = leer(carpeta, "metricas_modelos.csv")
    pred = leer(carpeta, "predicciones_prueba.csv", dtype={"id_municipio": str})
    base = leer(carpeta, "base_modelado.csv", dtype={"id_municipio": str})
    hip = leer(carpeta, "hipotesis_resultados.csv")
    sint = leer(carpeta, "sintesis_hipotesis.csv")
    imp = leer(carpeta, "importancia_permutacion.csv")
    evid = leer(carpeta, "evidencia_cultivo.csv")
    esenciales = {"metricas_modelos.csv": met, "predicciones_prueba.csv": pred, "base_modelado.csv": base,
                  "hipotesis_resultados.csv": hip, "sintesis_hipotesis.csv": sint, "importancia_permutacion.csv": imp}
    faltan = [k for k, v in esenciales.items() if v is None]
    if faltan:
        raise FileNotFoundError(f"Faltan archivos en {carpeta}: {faltan}. Ejecuta el notebook completo (sección 11).")

    def mae(prefijo):
        return float(met[met["Modelo"].str.startswith(prefijo)].iloc[0]["MAE prueba"])

    b0, b1, b2, m1, m2 = (reg(f"MAE de prueba {p}", mae(p), "metricas_modelos.csv") for p in ["B0", "B1", "B2", "M1", "M2"])
    reg("R² de prueba M2", float(met[met["Modelo"].str.startswith("M2")]["R² prueba"].iloc[0]), "metricas_modelos.csv")
    modelos = met[met["Tipo"] == "Modelo"].sort_values("MAE prueba")
    mejor_nombre, mejor_mae = modelos.iloc[0]["Modelo"], float(modelos.iloc[0]["MAE prueba"])

    a0, a1 = int(pred["anio"].min()), int(pred["anio"].max())
    n_test = reg("Registros de prueba", len(pred), "predicciones_prueba.csv")
    n_mun = reg("Municipios del modelo", int(base["id_municipio"].nunique()), "base_modelado.csv")
    anio_tr = int(base.loc[base["split"] == "entrenamiento", "anio"].max())
    n_inf = reg("Registros de la prueba estadística", int(hip["N"].max()), "hipotesis_resultados.csv")
    n_mun_inf = reg("Municipios de la prueba estadística", int(hip["Municipios"].max()), "hipotesis_resultados.csv")

    boot = comparaciones_bootstrap(pred, n=n_boot)
    f_clima, f_anio = boot.iloc[0], boot.iloc[1]
    d_clima = reg("Δ MAE por clima normal (M1 vs B2)", float(f_clima["Δ MAE (ref − modelo)"]), "predicciones_prueba.csv (bootstrap)")
    d_anio = reg("Δ MAE por anomalías del año (M2 vs M1)", float(f_anio["Δ MAE (ref − modelo)"]), "predicciones_prueba.csv (bootstrap)")

    veredictos = sint["Veredicto"].fillna("")
    n_resp = reg("Hipótesis respaldadas por ambas pruebas", int(veredictos.str.startswith("Respaldada").sum()), "sintesis_hipotesis.csv")
    n_parc = reg("Hipótesis con respaldo parcial", int(veredictos.str.startswith("Respaldo parcial").sum()), "sintesis_hipotesis.csv")
    n_sin = len(sint) - n_resp - n_parc
    con_apoyo = sint[~veredictos.str.startswith("Sin respaldo")]

    integ = imp["origen"].astype(str).str.contains("IDEAM")
    pos = imp["aumento_MAE"].clip(lower=0)
    cuota_ideam = reg("Importancia de las variables del IDEAM", float(pos[integ].sum() / max(pos.sum(), 1e-12)), "importancia_permutacion.csv")
    top = imp.sort_values("aumento_MAE", ascending=False).iloc[0]

    sig = pd.DataFrame()
    if evid is not None and len(evid):
        sig = evid[evid["p_FDR"] < ALFA].sort_values("rho")
        reg("Cultivos con asociación significativa tras FDR", len(sig), "evidencia_cultivo.csv")

    # 1. respuesta
    if n_resp == 0 and n_parc == 0:
        tono = "info"
        respuesta = ("**Con los datos disponibles, no se pudo comprobar.** Ninguna de las cinco hipótesis tiene respaldo suficiente y saber cómo "
                     "fue la temperatura del año no mejora de forma comprobable la predicción del rendimiento. Esto **no demuestra que la "
                     "temperatura no importe**: indica que estos datos (pocos municipios con estación) no alcanzan para detectarlo.")
    else:
        tono = "ok" if n_resp else "warn"
        lista = "; ".join(f"{corto(r['Hipótesis'])} ({r['Veredicto'].lower()})" for _, r in con_apoyo.iterrows())
        partes = []
        if n_resp:
            partes.append(f"{n_resp} con respaldo en las dos pruebas (estadística y de modelo)")
        if n_parc:
            partes.append(f"{n_parc} con respaldo en solo una")
        respuesta = (f"**Hay señales, pero limitadas.** De cinco hipótesis, {' y '.join(partes)}: {lista}. "
                     "Una señal estadística no prueba que la temperatura *cause* el cambio de rendimiento (véase Limitaciones).")

    # 3. hallazgos
    if b1 < mejor_mae:
        h_pred = (f"Repetir lo que pasó el año anterior (error de {num(b1)}) predijo **mejor** que cualquier modelo (el mejor, "
                  f"{corto(mejor_nombre)}, tuvo {num(mejor_mae)}).")
    else:
        h_pred = f"El mejor modelo ({corto(mejor_nombre)}) tuvo un error de {num(mejor_mae)} y superó a repetir el año anterior ({num(b1)})."
    if f_clima["Lectura"] != f_anio["Lectura"]:
        h_temp = (f"**Qué aporta la temperatura.** Conocer el *clima normal* del municipio cambia el error en {signed(d_clima, 4)} "
                  f"({f_clima['Lectura']}); conocer *cómo fue el año frente a lo normal* lo cambia en {signed(d_anio, 4)} "
                  f"({f_anio['Lectura']}).")
        if f_clima["Lectura"].startswith("mejora") and not f_anio["Lectura"].startswith("mejora"):
            h_temp += " Es decir, ayuda más saber **dónde** está el cultivo que **cómo fue el año**."
    else:
        h_temp = (f"**Qué aporta la temperatura.** Conocer el clima normal del municipio cambia el error en {signed(d_clima, 4)} y conocer cómo "
                  f"fue el año frente a lo normal en {signed(d_anio, 4)}; en ambos casos {f_anio['Lectura']}.")
    hallazgos = [
        (f"**Qué tan bien se predice.** El modelo con clima completo (M2) se equivoca, en promedio, en {num(m2)} veces el rendimiento típico del "
         f"cultivo (un {pct(m2)}); predecir siempre \"lo normal\" da {num(b0)} y el mismo modelo sin datos del IDEAM, {num(b2)}. {h_pred}"),
        h_temp,
        (f"**Las cinco hipótesis.** {n_resp} respaldadas por las dos pruebas, {n_parc} con respaldo parcial y {n_sin} sin respaldo. "
         f"La prueba estadística usó {miles(n_inf)} registros de {n_mun_inf} municipios; el modelo, {miles(n_test)} registros de prueba de {n_mun} municipios."),
        (f"**Qué usa el modelo.** La variable más usada es *{str(top['etiqueta']).lower()}*. Las variables del IDEAM suman {pct(cuota_ideam)} "
         "de la importancia total."),
    ]
    if len(sig):
        nombres = ", ".join(f"{r['cultivo']} (ρ = {signed(r['rho'], 2)})" for _, r in sig.iterrows())
        hallazgos.append(f"**Cultivos con señal.** Tras corregir por comparaciones múltiples, {len(sig)} de {len(evid)} cultivos muestran "
                         f"asociación: {nombres}. Es evidencia exploratoria.")
    elif evid is not None and len(evid):
        hallazgos.append(f"**Cultivos con señal.** Ninguno de los {len(evid)} cultivos analizados por separado mantiene una asociación "
                         "significativa tras corregir por comparaciones múltiples.")

    # 4. recomendaciones
    recs = [f"**Ampliar la red de estaciones.** Hoy el análisis describe solo {n_mun} municipios con estación y años de prueba {a0}-{a1}; "
            "sumar estaciones (y mantenerlas en el tiempo) aumentaría la capacidad de detectar un efecto, si existe."]
    if f_anio["Lectura"] != "mejora distinguible del ruido":
        recs.append("**Incorporar lluvia, riego y plagas.** La temperatura sola no mejoró la predicción; las sequías, inundaciones y el manejo del "
                    "cultivo pueden pesar más y no están en los datos.")
    if b1 < mejor_mae:
        recs.append("**Usar la historia propia de cada cultivo como referencia de planeación.** Mientras ningún modelo supere al rendimiento del "
                    "año anterior, esa referencia simple es más confiable que un modelo con clima.")
    if len(sig):
        recs.append(f"**Monitorear primero {', '.join(sig['cultivo'].head(3))}**, los cultivos con asociación más clara, antes de generalizar.")
    recs.append("**Medir a escala más fina.** Con rendimientos mensuales o por finca (y temperatura por etapa del cultivo) se podría ver lo que "
                "un promedio anual esconde.")

    metodo = (f"Se unieron los rendimientos agrícolas (Gobernación del Valle del Cauca) con la temperatura de las estaciones del IDEAM por municipio "
              f"y año (código DIVIPOLA). El rendimiento de cada cultivo se midió **frente a lo normal de su propio municipio**. Los modelos aprendieron "
              f"con años hasta {anio_tr} y se evaluaron en {a0}-{a1}, años que no habían visto, y cada uno se comparó con referencias simples "
              "(predecir \"lo normal\" y repetir el año anterior) para saber si la temperatura realmente agrega algo. "
              "Un error de 0,35 significa equivocarse en un 35 % del rendimiento típico del cultivo.")

    kpis = [
        {"etiqueta": "Error si repite el año anterior (B1)", "valor": num(b1), "nota": "referencia simple", "tono": "gris"},
        {"etiqueta": "Error sin datos del IDEAM (B2)", "valor": num(b2), "nota": "referencia con cultivo y municipio", "tono": "gris"},
        {"etiqueta": "Error con clima completo (M2)", "valor": num(m2), "nota": f"{signed(m2 - b2)} frente a B2 · menor es mejor",
         "tono": "ok" if m2 < b2 else "warn"},
        {"etiqueta": "Hipótesis respaldadas (de 5)", "valor": f"{n_resp}", "nota": f"+ {n_parc} con respaldo parcial · {n_sin} sin respaldo",
         "tono": "ok" if n_resp else ("warn" if n_parc else "info")},
    ]
    pregunta = "¿Los años más cálidos de lo normal reducen el rendimiento de los cultivos del Valle del Cauca, y sirve esa información para anticiparlo?"
    return {"pregunta": pregunta, "respuesta": respuesta, "tono": tono, "metodo": metodo, "hallazgos": hallazgos, "recs": recs,
            "limites": limitaciones(n_mun), "kpis": kpis, "cifras": pd.DataFrame(cifras), "anios": (anio_tr, a0, a1),
            "met": met, "boot": boot, "sint": sint}


FUENTES = ("Fuentes: Gobernación del Valle del Cauca (cultivos) e IDEAM (temperatura del aire, conjunto sbwg-7ju4), vía datos.gov.co; "
           "fechas de consulta en la tabla de linaje de la Parte 2. Todas las cifras se generaron desde los archivos del tablero "
           "(véase `verificacion_cifras.csv`).")
TITULO = "Temperatura y rendimiento de los cultivos del Valle del Cauca"
SUBTITULO = "Resumen ejecutivo · Ciencia de Datos con Python (IGS38) · Caso de estudio, Parte 3"


def a_markdown(p):
    lim = "\n".join(f"- **{t}.** {d}" for t, d in p["limites"])
    return (f"# {TITULO}\n*{SUBTITULO}*\n\n"
            f"## 1. Pregunta y respuesta\n{p['pregunta']}\n\n{p['respuesta']}\n\n"
            f"## 2. Qué se hizo\n{p['metodo']}\n\n"
            "## 3. Hallazgos\n" + "\n".join(f"{i}. {h}" for i, h in enumerate(p["hallazgos"], 1)) +
            "\n\n## 4. Recomendaciones\n" + "\n".join(f"{i}. {r}" for i, r in enumerate(p["recs"], 1)) +
            f"\n\n## 5. Limitaciones\n{lim}\n\n*{FUENTES}*\n")


def construir_resumen(carpeta, n_boot=2000):
    """Compatibilidad: devuelve (texto_markdown, tabla_de_verificacion)."""
    p = construir_partes(carpeta, n_boot)
    return a_markdown(p), p["cifras"]


#  versión HTML (imprimible a PDF en 2 páginas A4)
def _inline(t):
    t = html.escape(str(t), quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


CSS_RESUMEN = """
:root{--verde:#1F5F46;--verde2:#2E7D5B;--crema:#F7F4EC;--tinta:#1E2A25;--gris:#6B7770;--linea:#DAD5C5;--ambar:#C98A0A;--tierra:#B4533A}
*{box-sizing:border-box}
body{margin:0;background:#EDEAE0;color:var(--tinta);font:10.2pt/1.45 'Inter','Segoe UI',Helvetica,Arial,sans-serif}
.hoja{max-width:820px;margin:18px auto;background:#fff;padding:26px 34px;box-shadow:0 2px 14px rgba(0,0,0,.12)}
header{background:linear-gradient(120deg,var(--verde),var(--verde2));color:#fff;border-radius:10px;padding:16px 20px;margin-bottom:12px}
header h1{margin:0 0 3px;font-size:17pt;line-height:1.15;font-weight:700}
header p{margin:0;font-size:9pt;opacity:.85}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:0 0 12px}
.kpi{border:1px solid var(--linea);border-top:4px solid var(--gris);border-radius:8px;padding:7px 9px;background:var(--crema)}
.kpi.ok{border-top-color:var(--verde2)}.kpi.warn{border-top-color:var(--ambar)}.kpi.info{border-top-color:#4C78A8}
.kpi b{display:block;font-size:17pt;line-height:1.1;color:var(--verde)}
.kpi span{display:block;font-size:7.6pt;color:var(--gris);line-height:1.25}.kpi .e{font-weight:600;color:var(--tinta);font-size:7.8pt}
h2{font-size:11.5pt;color:var(--verde);margin:12px 0 4px;padding-bottom:2px;border-bottom:2px solid var(--linea)}
h2 i{font-style:normal;display:inline-block;background:var(--verde);color:#fff;border-radius:50%;width:19px;height:19px;text-align:center;font-size:8.5pt;line-height:19px;margin-right:6px}
p{margin:4px 0}
.pregunta{font-style:italic;color:var(--gris)}
.respuesta{border-left:5px solid var(--verde2);background:#EAF4EE;padding:7px 11px;border-radius:0 8px 8px 0;margin:6px 0}
.respuesta.warn{border-color:var(--ambar);background:#FBF3DF}.respuesta.info{border-color:#4C78A8;background:#E8EFF7}
ol,ul{margin:4px 0;padding-left:20px}li{margin:3px 0}
.lim li::marker{color:var(--tierra)}
footer{margin-top:10px;padding-top:6px;border-top:1px solid var(--linea);font-size:7.6pt;color:var(--gris)}
code{background:var(--crema);padding:0 3px;border-radius:3px}
.figs{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0 0 8px}
.fig{border:1px solid var(--linea);border-radius:8px;padding:6px 8px;background:#fff}
.fig svg{width:100%;height:auto;display:block}
.fig .cap{font-size:7.6pt;color:var(--gris);margin-top:2px;line-height:1.3}
.chips{display:flex;gap:5px;align-items:center;flex-wrap:wrap;margin:0 0 4px;font-size:8pt}
.chips .t{color:var(--gris);margin-right:2px}
.chip{border-radius:10px;padding:1px 9px;color:#fff;font-size:7.8pt}
.chip.ok{background:var(--verde2)}.chip.warn{background:var(--ambar)}.chip.mal{background:var(--tierra)}
@page{size:A4;margin:11mm}
@media print{body{background:#fff;font-size:9pt}.hoja{box-shadow:none;margin:0;padding:0;max-width:none}header,.kpi,.respuesta,.chip,.fig svg{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


_SVG_ATTR = 'xmlns="http://www.w3.org/2000/svg" font-family="Inter,Segoe UI,Arial,sans-serif"'


def _svg_mae(met, w=400, h=170):
    """Barras verticales del MAE de prueba por modelo (gris: línea base; verde: modelo)."""
    m = met.sort_values("MAE prueba").reset_index(drop=True)
    vmax = float(m["MAE prueba"].max()) * 1.2 or 1.0
    arr, aba, lado = 14, 36, 10
    paso = (w - 2 * lado) / len(m)
    bw = paso * 0.6
    sv = [f'<svg viewBox="0 0 {w} {h}" {_SVG_ATTR} role="img" aria-label="Error de cada modelo en prueba">']
    for i, r in m.iterrows():
        v = float(r["MAE prueba"])
        alto = (h - arr - aba) * v / vmax
        x, y = lado + i * paso + (paso - bw) / 2, h - aba - alto
        col = "#9AA3AE" if r["Tipo"] == "Línea base" else "#2E7D5B"
        sv.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{alto:.1f}" fill="{col}" rx="2"/>'
                  f'<text x="{x + bw / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle" font-size="10" fill="#1E2A25">{num(v)}</text>'
                  f'<text x="{x + bw / 2:.1f}" y="{h - aba + 13:.1f}" text-anchor="middle" font-size="10" fill="#1E2A25">{html.escape(corto(r["Modelo"])[:14])}</text>')
    sv.append(f'<line x1="{lado}" y1="{h - aba}" x2="{w - lado}" y2="{h - aba}" stroke="#6B7770"/>')
    sv.append(f'<rect x="{lado}" y="{h - 11}" width="9" height="9" fill="#9AA3AE" rx="1"/><text x="{lado + 13}" y="{h - 3}" font-size="9" fill="#6B7770">Línea base</text>'
              f'<rect x="{lado + 80}" y="{h - 11}" width="9" height="9" fill="#2E7D5B" rx="1"/><text x="{lado + 93}" y="{h - 3}" font-size="9" fill="#6B7770">Modelo</text></svg>')
    return "".join(sv)


def _svg_boot(boot, w=400, h=170):
    """Δ MAE con IC 95 % (bootstrap); a la derecha del 0 el modelo con más información mejora."""
    lo_m, hi_m = min(float(boot["IC95 inferior"].min()), 0.0), max(float(boot["IC95 superior"].max()), 0.0)
    pad = (hi_m - lo_m) * 0.12 or 0.01
    lo_m, hi_m = lo_m - pad, hi_m + pad
    izq, der, arr, aba = 92, 16, 12, 38
    sx = lambda v: izq + (v - lo_m) / (hi_m - lo_m) * (w - izq - der)
    paso = (h - arr - aba) / len(boot)
    colores = {"mejora distinguible del ruido": "#2E7D5B", "empeora": "#B4533A"}
    sv = [f'<svg viewBox="0 0 {w} {h}" {_SVG_ATTR} role="img" aria-label="Aporte de la temperatura con intervalo de confianza">',
          f'<line x1="{sx(0):.1f}" y1="{arr}" x2="{sx(0):.1f}" y2="{h - aba}" stroke="#1E2A25" stroke-dasharray="4 3"/>']
    for i, r in boot.reset_index(drop=True).iterrows():
        yc = arr + paso * (i + 0.5)
        col = colores.get(r["Lectura"], "#9AA3AE")
        sv.append(f'<line x1="{sx(r["IC95 inferior"]):.1f}" y1="{yc:.1f}" x2="{sx(r["IC95 superior"]):.1f}" y2="{yc:.1f}" stroke="{col}" stroke-width="5" stroke-linecap="round"/>'
                  f'<circle cx="{sx(r["Δ MAE (ref − modelo)"]):.1f}" cy="{yc:.1f}" r="4.5" fill="#1E2A25"/>'
                  f'<text x="{izq - 8}" y="{yc + 3.5:.1f}" text-anchor="end" font-size="10" fill="#1E2A25">{html.escape(str(r["Comparación"]).split(" (")[0])}</text>')
    for v, anc in [(lo_m, "start"), (0.0, "middle"), (hi_m, "end")]:
        sv.append(f'<text x="{sx(v):.1f}" y="{h - aba + 13}" text-anchor="{anc}" font-size="9" fill="#6B7770">{"0" if v == 0 else signed(v, 3)}</text>')
    sv.append(f'<line x1="{izq}" y1="{h - aba}" x2="{w - der}" y2="{h - aba}" stroke="#6B7770"/>'
              f'<text x="10" y="{h - 4}" font-size="8.5" fill="#6B7770">Δ MAE (referencia − modelo): a la derecha del 0 el modelo mejora</text></svg>')
    return "".join(sv)


def _figuras(p):
    if p.get("met") is None or p.get("boot") is None:
        return ""
    chips = ""
    for _, r in p["sint"].iterrows():
        v = str(r["Veredicto"])
        k = "ok" if v.startswith("Respaldada") else "warn" if v.startswith("Respaldo parcial") else "mal"
        txt = {"ok": "respaldada", "warn": "parcial", "mal": "sin respaldo"}[k]
        chips += f'<span class="chip {k}"><b>{html.escape(str(r["ID"]))}</b> {txt}</span>'
    return (f'<div class="figs"><div class="fig">{_svg_mae(p["met"])}<div class="cap"><b>Figura 1.</b> Error (MAE) en años no vistos; menor es mejor.</div></div>'
            f'<div class="fig">{_svg_boot(p["boot"])}<div class="cap"><b>Figura 2.</b> Aporte de la temperatura con IC 95 % (bootstrap por municipio-año).</div></div></div>'
            f'<div class="chips"><span class="t">Hipótesis:</span>{chips}</div>')


def a_html(p):
    kp = "".join(f'<div class="kpi {k["tono"]}"><span class="e">{_inline(k["etiqueta"])}</span><b>{k["valor"]}</b>'
                 f'<span>{_inline(k["nota"])}</span></div>' for k in p["kpis"])
    li = lambda xs: "".join(f"<li>{_inline(x)}</li>" for x in xs)
    lim = "".join(f"<li><strong>{_inline(t)}.</strong> {_inline(d)}</li>" for t, d in p["limites"])
    sec = lambda n, t: f"<h2><i>{n}</i>{t}</h2>"
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{TITULO}</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><style>{CSS_RESUMEN}</style></head><body><div class="hoja">
<header><h1>{TITULO}</h1><p>{SUBTITULO}</p></header>
<div class="kpis">{kp}</div>
{_figuras(p)}
{sec(1, "Pregunta y respuesta")}<p class="pregunta">{_inline(p["pregunta"])}</p><div class="respuesta {p["tono"] if p["tono"] != "ok" else ""}">{_inline(p["respuesta"])}</div>
{sec(2, "Qué se hizo")}<p>{_inline(p["metodo"])}</p>
{sec(3, "Hallazgos")}<ol>{li(p["hallazgos"])}</ol>
{sec(4, "Recomendaciones")}<ol>{li(p["recs"])}</ol>
{sec(5, "Limitaciones")}<ul class="lim">{lim}</ul>
<footer>{_inline(FUENTES)}</footer></div></body></html>"""


def construir_html(carpeta, n_boot=2000):
    return a_html(construir_partes(carpeta, n_boot))


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else encontrar_carpeta()
    if not carpeta:
        sys.exit("No se encontró la carpeta del tablero (data/procesados/tablero). Pásala como argumento.")
    partes = construir_partes(carpeta)
    texto = a_markdown(partes)
    Path("resumen_ejecutivo.md").write_text(texto, encoding="utf-8")
    Path("resumen_ejecutivo.html").write_text(a_html(partes), encoding="utf-8")
    partes["cifras"].to_csv("verificacion_cifras.csv", index=False, encoding="utf-8-sig")
    n = len(texto.split())
    print(f"Escrito resumen_ejecutivo.md / .html ({n} palabras) y verificacion_cifras.csv ({len(partes['cifras'])} cifras)")
    if n > MAX_PALABRAS:
        print(f"⚠ {n} palabras: puede pasar de 2 páginas. Abre el .html y comprueba la vista previa de impresión (A4).")
    else:
        print("Ábrelo en el navegador → Imprimir → Guardar como PDF (A4, márgenes predeterminados).")