# Version de python
python --version

# Crear entorno
python -m venv venv

# Activar entorno
source venv/Scripts/activate

# Instalar las librerías
python -m pip install --upgrade pip
pip install jupyter pandas numpy matplotlib seaborn sodapy

# Abrir jupiter
python -m jupyter notebook