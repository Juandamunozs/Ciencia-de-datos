import sys
from pathlib import Path

import numpy as np
import pandas as pd

ALFA = 0.05
SEMILLA = 42


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


def lectura_ic(lo, hi):
    if lo > 0:
        return "mejora distinguible del ruido"
    if hi < 0:
        return "empeora"
    return "no se distingue del ruido"


#  formato
def num(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


def signed(x, d=3):
    return f"{x:+.{d}f}".replace(".", ",")


def miles(x):
    return f"{int(x):,}".replace(",", ".")


def pct(x, d=0):
    return f"{x * 100:.{d}f} %".replace(".", ",")


#  resumen
def construir_resumen(carpeta, n_boot=2000):
    """Devuelve (texto_markdown, tabla_de_verificacion). Lanza FileNotFoundError si falta un archivo esencial."""
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
        fila = met[met["Modelo"].str.startswith(prefijo)].iloc[0]
        return float(fila["MAE prueba"])

    b0, b1, b2, m1, m2 = (reg(f"MAE de prueba {p}", mae(p), "metricas_modelos.csv") for p in ["B0", "B1", "B2", "M1", "M2"])
    r2_m2 = reg("R² de prueba M2", float(met[met["Modelo"].str.startswith("M2")]["R² prueba"].iloc[0]), "metricas_modelos.csv")
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
    reg("Δ MAE por clima normal (M1 vs B2)", float(f_clima["Δ MAE (ref − modelo)"]), "predicciones_prueba.csv (bootstrap)")
    reg("Δ MAE por anomalías del año (M2 vs M1)", float(f_anio["Δ MAE (ref − modelo)"]), "predicciones_prueba.csv (bootstrap)")

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

    # ------------------------------------------------------------------ 1. respuesta
    if n_resp == 0 and n_parc == 0:
        respuesta = ("**Con los datos disponibles, no se pudo comprobar.** Ninguna de las cinco hipótesis planteadas tiene respaldo "
                     "suficiente y saber cómo fue la temperatura del año no mejora de forma comprobable la predicción del rendimiento. "
                     "Esto **no demuestra que la temperatura no importe**: indica que estos datos (pocos municipios con estación) "
                     "no alcanzan para detectarlo.")
    else:
        lista = "; ".join(f"{r['Hipótesis'].split('·')[0].strip()} ({r['Veredicto'].lower()})" for _, r in con_apoyo.iterrows())
        partes = []
        if n_resp:
            partes.append(f"{n_resp} con respaldo en las dos pruebas (estadística y de modelo)")
        if n_parc:
            partes.append(f"{n_parc} con respaldo en solo una")
        respuesta = (f"**Hay señales, pero limitadas.** De cinco hipótesis, {' y '.join(partes)}: {lista}. "
                     "Una señal estadística no prueba que la temperatura *cause* el cambio de rendimiento (véase Limitaciones).")

    # ------------------------------------------------------------------ 3. hallazgos
    if b1 < mejor_mae:
        h_pred = (f"Repetir lo que pasó el año anterior (error de {num(b1)}) predijo **mejor** que cualquier modelo (el mejor, "
                  f"{mejor_nombre.split('·')[0].strip()}, tuvo {num(mejor_mae)}).")
    else:
        h_pred = (f"El mejor modelo ({mejor_nombre.split('·')[0].strip()}) tuvo un error de {num(mejor_mae)} y superó a repetir el año anterior "
                  f"({num(b1)}).")
    hallazgos = [
        (f"**Qué tan bien se predice.** El modelo con clima completo (M2) se equivoca, en promedio, en {num(m2)} veces el rendimiento típico del cultivo "
         f"(un {pct(m2)}); predecir siempre \"lo normal\" da {num(b0)} y el mismo modelo sin datos del IDEAM, {num(b2)}. {h_pred}"),
        (f"**Qué aporta la temperatura.** Conocer el *clima normal* del municipio cambia el error en {signed(f_clima['Δ MAE (ref − modelo)'], 4)} "
         f"({f_clima['Lectura']}); conocer *cómo fue el año frente a lo normal* lo cambia en {signed(f_anio['Δ MAE (ref − modelo)'], 4)} "
         f"({f_anio['Lectura']}). Es decir, ayuda más saber **dónde** está el cultivo que **cómo fue el año**."
         if f_clima["Lectura"] != f_anio["Lectura"] else
         f"**Qué aporta la temperatura.** Conocer el clima normal del municipio cambia el error en {signed(f_clima['Δ MAE (ref − modelo)'], 4)} "
         f"y conocer cómo fue el año frente a lo normal en {signed(f_anio['Δ MAE (ref − modelo)'], 4)}; en ambos casos {f_anio['Lectura']}."),
        (f"**Las cinco hipótesis.** {n_resp} respaldadas por las dos pruebas, {n_parc} con respaldo parcial y {n_sin} sin respaldo. "
         f"La prueba estadística usó {miles(n_inf)} registros de {n_mun_inf} municipios; el modelo, {miles(n_test)} registros de prueba de {n_mun} municipios."),
        (f"**Qué usa el modelo.** La variable más usada es *{str(top['etiqueta']).lower()}*. Las variables del IDEAM suman "
         f"{pct(cuota_ideam)} de la importancia total."),
    ]
    if len(sig):
        nombres = ", ".join(f"{r['cultivo']} (ρ = {signed(r['rho'], 2)})" for _, r in sig.iterrows())
        hallazgos.append(f"**Cultivos con señal.** Tras corregir por comparaciones múltiples, {len(sig)} de {len(evid)} cultivos muestran asociación: "
                         f"{nombres}. Es evidencia exploratoria.")
    elif evid is not None and len(evid):
        hallazgos.append(f"**Cultivos con señal.** Ninguno de los {len(evid)} cultivos analizados por separado mantiene una asociación significativa "
                         "tras corregir por comparaciones múltiples.")

    # ------------------------------------------------------------------ 4. recomendaciones
    recs = [f"**Ampliar la red de estaciones.** Hoy el análisis describe solo {n_mun} municipios con estación y años de prueba {a0}-{a1}; "
            "sumar estaciones (y mantenerlas en el tiempo) aumentaría la capacidad de detectar un efecto, si existe."]
    if f_anio["Lectura"] != "mejora distinguible del ruido":
        recs.append("**Incorporar lluvia, riego y plagas.** La temperatura sola no mejoró la predicción; las sequías, inundaciones y el manejo del "
                    "cultivo pueden pesar más y no están en los datos.")
    if b1 < mejor_mae:
        recs.append("**Usar la historia propia de cada cultivo como referencia de planeación.** Mientras ningún modelo supere al rendimiento del año anterior, "
                    "esa referencia simple es más confiable que un modelo con clima.")
    if len(sig):
        recs.append(f"**Monitorear primero {', '.join(sig['cultivo'].head(3))}**, los cultivos con asociación más clara, antes de generalizar.")
    recs.append("**Medir a escala más fina.** Con rendimientos mensuales o por finca (y temperatura por etapa del cultivo) se podría ver lo que un promedio anual esconde.")

    texto = f"""# Resumen ejecutivo
**Temperatura y rendimiento de los cultivos del Valle del Cauca** · Ciencia de Datos con Python (IGS38), Parte 3

## 1. Pregunta y respuesta
¿Los años más cálidos de lo normal reducen el rendimiento de los cultivos del Valle del Cauca, y sirve esa información para anticiparlo?

{respuesta}

## 2. Qué se hizo
Se unieron los rendimientos agrícolas (Gobernación del Valle del Cauca) con la temperatura de las estaciones del IDEAM por municipio y año (código DIVIPOLA). El rendimiento de cada cultivo se midió **frente a lo normal de su propio municipio**. Los modelos aprendieron con años hasta {anio_tr} y se evaluaron en {a0}-{a1}, años que no habían visto. Cada modelo se comparó con referencias simples (predecir "lo normal" y repetir el año anterior), para saber si la temperatura realmente agrega algo. Una cifra de error de 0,35 significa equivocarse en un 35 % del rendimiento típico del cultivo.

## 3. Hallazgos
""" + "\n".join(f"{i}. {h}" for i, h in enumerate(hallazgos, 1)) + """

## 4. Recomendaciones
""" + "\n".join(f"{i}. {r}" for i, r in enumerate(recs, 1)) + f"""

## 5. Limitaciones
- **Sesgo de cobertura.** Solo hay temperatura en municipios con estación del IDEAM (y con historia suficiente); los resultados describen a esos {n_mun} municipios y **no se extienden al resto del Valle**. Las estaciones no se reparten al azar, y la estación puede estar a otra altitud que las zonas agrícolas.
- **Falacia ecológica.** Los datos son municipales: describen municipios, no fincas ni personas. Lo que se observa en el promedio de un municipio no tiene por qué ocurrir en cada productor.
- **Correlación no es causalidad.** Que una variable ayude a predecir no demuestra que cause el cambio de rendimiento; el rendimiento también depende de lluvia, riego, plagas, tecnología y precios, que no están en el modelo.
- **Incertidumbre.** Pocos años de prueba y pocos municipios: las cifras tienen intervalos de confianza amplios, y varias comparaciones se hicieron a la vez (por eso se corrigieron).

*Fuentes: Gobernación del Valle del Cauca (cultivos) e IDEAM (temperatura del aire, conjunto sbwg-7ju4), vía datos.gov.co; fechas de consulta en la tabla de linaje de la Parte 2. Todas las cifras se generaron desde los archivos del tablero (véase `verificacion_cifras.csv`).*
"""
    return texto, pd.DataFrame(cifras)


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else encontrar_carpeta()
    if not carpeta:
        sys.exit("No se encontró la carpeta del tablero (data/procesados/tablero). Pásala como argumento.")
    texto, cifras = construir_resumen(carpeta)
    Path("resumen_ejecutivo.md").write_text(texto, encoding="utf-8")
    cifras.to_csv("verificacion_cifras.csv", index=False, encoding="utf-8-sig")
    print(f"Escrito resumen_ejecutivo.md ({len(texto.split())} palabras) y verificacion_cifras.csv ({len(cifras)} cifras)")