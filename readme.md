# Ciencia de datos - Configuración del entorno de desarrollo

Repositorio con los tres laboratorios del curso de Ciencia de Datos. Cada laboratorio contiene un notebook de Jupyter con su estudio de caso; el laboratorio 3 además incluye una tablero hecho con Streamlit.

---

## Contenido

1. [Estructura del proyecto](#estructura-del-proyecto)
2. [Requisitos previos](#requisitos-previos)
3. [Instalación paso a paso](#instalación-paso-a-paso)
4. [Cómo usar el proyecto](#cómo-usar-el-proyecto)
5. [Comandos útiles](#comandos-útiles)

---

## Estructura del proyecto

```
Ciencia de datos/
├── laboratorio_1/
│   ├── data/                        
│   └── Estudio_de_caso_Parte1.ipynb
├── laboratorio_2/
│   ├── data/                       
│   └── Estudio_de_caso_Parte2.ipynb
├── laboratorio_3/
│   ├── data/                        
│   ├── figuras/                    
│   ├── app.py                       
│   ├── resumen.py                  
│   └── Estudio_de_caso_Parte3.ipynb
├── requirements.txt               
├── .gitignore
└── README.md
```
---

## Instalación paso a paso

### 1. Obtener el proyecto

Elige **una** de las dos opciones:

**Opción A: Descargar el ZIP desde GitHub**
1. En la página del repositorio, haz clic en **Code → Download ZIP**.
2. Descomprime el archivo.
3. Abre una terminal dentro de la carpeta descomprimida.

**Opción B: Clonar con Git**
```bash
git clone https://github.com/Juandamunozs/Ciencia-de-datos.git
```

### 2. Verificar la versión de Python

```bash
python --version
```

### 3. Crear el entorno virtual

El entorno virtual es una carpeta aislada (`.venv`) donde se instalan las librerías del proyecto sin afectar si tienes otros proyectos con otra version de la libreria. **Solo se crea la primera vez.**

```bash
python -m venv .venv
```

### 4. Activar el entorno virtual

Debes activarlo **cada vez que abras una terminal nueva** para trabajar en el proyecto.

| Terminal | Comando |
|---|---|
| Windows (CMD o PowerShell) | `.venv\Scripts\activate` |
| Git Bash | `source .venv/Scripts/activate` |
| macOS / Linux | `source .venv/bin/activate` |

Sabrás que funcionó porque verás `(.venv)` al inicio de la línea de la terminal.

### 5. Actualizar pip

```bash
python -m pip install --upgrade pip
```

### 6. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Este comando instala todas las librerías que necesita el proyecto. Puede tardar unos minutos.

---

## Cómo usar el proyecto

### Abrir los notebooks (Jupyter)

Con el entorno virtual activado ejecutar en la consola:

```bash
python -m jupyter notebook
```

Se abrirá el navegador. Entra a la carpeta del laboratorio que quieras y abre su archivo `.ipynb`:

- `laboratorio_1/Estudio_de_caso_Parte1.ipynb`
- `laboratorio_2/Estudio_de_caso_Parte2.ipynb`
- `laboratorio_3/Estudio_de_caso_Parte3.ipynb`

Ejecuta las celdas en orden.

### Ejecutar la aplicación Streamlit (laboratorio 3)

> **El notebook `Estudio_de_caso_Parte3.ipynb` ya lanza la aplicación en la ultima celda.** Solo necesitas este comando si quieres ejecutarla por separado.

```bash
cd laboratorio_3
python -m streamlit run app.py
```

Streamlit abrirá la aplicación en tu navegador.

### Cerrar todo al terminar

1. Detén Jupyter o Streamlit con `Ctrl + C` en la terminal.
2. Desactiva el entorno virtual:

```bash
deactivate
```

---

## Comandos útiles

### Actualizar `requirements.txt`

> **No es necesario si ya existe el archivo.** Solo hazlo si agregas o cambias librerías.

```bash
pip freeze > requirements.txt
```