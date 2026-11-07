## Configuración del entorno de desarrollo

### 1. Verificar la versión de Python
python --version

### 2. Crear el entorno virtual
python -m venv .venv

### 3. Activar el entorno virtual

**Windows (CMD o PowerShell):**
.venv\Scripts\activate

**Git Bash:**
source .venv/Scripts/activate

### 4. Actualizar pip
python -m pip install --upgrade pip

### 5. Instalar las dependencias
pip install -r requirements.txt

### 6. Registrar las versiones instaladas
Si agregan o modifican dependencias y deseas actualizar el archivo:
pip freeze > requirements.txt

### 7. Abrir Jupyter Notebook
python -m jupyter notebook

### 8. Desactivar el entorno virtual
deactivate