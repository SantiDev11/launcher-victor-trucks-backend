# 🚀 Guía de Despliegue de API Central en VPS (Opción A)

Esta guía explica paso a paso cómo montar el servidor central en un VPS (DigitalOcean, Hetzner, AWS, Linode, Vultr, etc.) para que **`https://api.victortrucks.com`** funcione perfectamente desde cualquier computador con Internet.

---

## 📋 Requisitos Previos

1. **Un servidor VPS** con **Ubuntu 22.04 LTS** o **24.04 LTS** (Mínimo: 1 CPU, 2 GB RAM, 25 GB SSD).
2. **Tu dominio registrado** (`victortrucks.com`) en tu proveedor (GoDaddy, Cloudflare, Namecheap, etc.).
3. Acceso SSH al VPS (`ssh root@ip_de_tu_vps`).

---

## 🌐 Paso 1: Configurar el DNS del Dominio

Ingresa al panel de control de tu dominio (`victortrucks.com`) y agrega la siguiente entrada DNS:

| Tipo | Nombre | Valor / Destino | TTL |
| :--- | :--- | :--- | :--- |
| **A** | `api` | `IP_PUBLICA_DE_TU_VPS` (Ej: `167.99.123.45`) | Auto / 300 |

*Esto vinculará `api.victortrucks.com` con la IP pública de tu VPS.*

---

## 📂 Paso 2: Subir el Proyecto al VPS

Desde la terminal de tu computador local, copia los archivos necesarios al VPS:

```bash
# Copia la carpeta del proyecto a tu VPS
scp -r backend deploy root@IP_DE_TU_VPS:/root/
```

---

## ⚙️ Paso 3: Ejecutar la Instalación Automática en el VPS

Conéctate por SSH a tu VPS:

```bash
ssh root@IP_DE_TU_VPS
```

Ejecuta el script de instalación automática que configurará Python, FastAPI, Nginx, UFW Firewall y el servicio systemd:

```bash
cd /root
chmod +x deploy/setup_vps.sh
./deploy/setup_vps.sh
```

---

## 🔒 Paso 4: Activar Certificado SSL HTTPS Gratis con Certbot

Una vez que el DNS ya haya propagado (puedes verificar en [dnschecker.org](https://dnschecker.org/#A/api.victortrucks.com)), ejecuta en el VPS:

```bash
sudo certbot --nginx -d api.victortrucks.com
```

Certbot emitirá e instalará el certificado SSL de Let's Encrypt automáticamente.

---

## 🔍 Paso 5: Verificar que la API responda

Prueba desde cualquier navegador o terminal en cualquier PC del mundo:

```bash
curl https://api.victortrucks.com/api/health
```

Debe responder:
`{"status": "ok", "version": "2.0.0"}`

---

## 🎯 ¡Listo!
Una vez completado estos pasos, el ejecutable `dist/Launcher_Victor_Trucks.exe` funcionará **en cualquier PC con Internet del planeta** conectándose de forma segura a `https://api.victortrucks.com`.
