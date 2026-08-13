#!/bin/bash
# ==============================================================================
# GRÁFICOS VICTORTRUCKS - VPS Deployment Script (Ubuntu / Debian)
# ==============================================================================
# Este script configura automáticamente el servidor VPS para alojar la API.
# Ejecútalo en tu VPS con: sudo bash setup_vps.sh

set -e

DOMAIN="api.victortrucks.com"
APP_DIR="/opt/victortrucks"
DATA_DIR="$APP_DIR/data"
STORAGE_DIR="$DATA_DIR/storage"

echo "=================================================================="
echo "  GRÁFICOS VICTORTRUCKS - Instala Servidor API VPS ($DOMAIN)"
echo "=================================================================="

# 1. Actualizar sistema e instalar paquetes básicos
echo "\n[1/6] Actualizando sistema e instalando dependencias..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw git curl

# 2. Crear usuario de sistema dedicado sin acceso shell
if ! id -u victortrucks >/dev/null 2>&1; then
    echo "\n[2/6] Creando usuario victortrucks..."
    sudo useradd -r -s /bin/false victortrucks
fi

# 3. Preparar directorios de la aplicación
echo "\n[3/6] Configurando directorios de la aplicación en $APP_DIR..."
sudo mkdir -p "$APP_DIR" "$STORAGE_DIR"
sudo chown -R victortrucks:victortrucks "$APP_DIR"

# Copiar archivos del proyecto si se ejecuta desde el repo clonado
if [ -f "backend/server.py" ]; then
    sudo cp -r backend "$APP_DIR/"
    sudo cp deploy/requirements_server.txt "$APP_DIR/"
    sudo chown -R victortrucks:victortrucks "$APP_DIR"
fi

# 4. Crear entorno virtual Python e instalar requerimientos
echo "\n[4/6] Creando virtualenv e instalando librerías Python..."
sudo -u victortrucks python3 -m venv "$APP_DIR/venv"
sudo -u victortrucks "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u victortrucks "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements_server.txt"

# 5. Configurar servicio Systemd
echo "\n[5/6] Instalando y activando servicio systemd..."
sudo cp deploy/victortrucks-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable victortrucks-api
sudo systemctl restart victortrucks-api

# 6. Configurar Nginx y Firewall
echo "\n[6/6] Configurando Nginx y Firewall (UFW)..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable || true

sudo cp deploy/nginx_victortrucks.conf /etc/nginx/sites-available/victortrucks
sudo ln -sf /etc/nginx/sites-available/victortrucks /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo "=================================================================="
echo "  ¡INSTALACIÓN DE INFRAESTRUCTURA COMPLETADA!"
echo "=================================================================="
echo ""
echo "Siguiente paso importante:"
echo "1. Asegúrate de haber apuntado el registro DNS A de $DOMAIN a la IP de este VPS."
echo "2. Genera el certificado SSL gratis ejecutando:"
echo "   sudo certbot --nginx -d $DOMAIN"
echo ""
