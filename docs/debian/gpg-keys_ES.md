# Tutorial Completo: Claves GPG para Debian Packaging

## 📋 Prerrequisitos
- Tener una cuenta en [mentors.debian.net](https://mentors.debian.net)
- Tener `gpg` instalado (viene por defecto en Debian)

---

## 1. **Crear una clave GPG (si no tienes una)**

### Método Interactivo:
```bash
gpg --full-generate-key
```
**Selecciones:**
- Tipo de clave: **1** (RSA y RSA)
- Tamaño: **4096**
- Validez: **2y** (2 años)
- Nombre y email: **Tu nombre completo y email**

### Método Automático (batch):
```bash
gpg --batch --generate-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: Tu Nombre Completo
Name-Email: tu-email@dominio.com
Expire-Date: 2y
%commit
EOF
```

---

## 2. **Verificar las claves existentes**

```bash
gpg --list-keys
```
**Salida esperada:**
```
pub   rsa4096 2024-01-01 [SC] [expires: 2026-01-01]
      0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
uid           [ultimate] Tu Nombre <tu-email@dominio.com>
sub   rsa4096 2024-01-01 [E] [expires: 2026-01-01]
```

---

## 3. **Exportar la clave pública en formato requerido**

```bash
gpg --export --export-options export-minimal --armor 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
```

**Copia TODO el output** (incluyendo las líneas `-----BEGIN` y `-----END`)

---

## 4. **Configurar la clave en mentors.debian.net**

1. Ve a [mentors.debian.net](https://mentors.debian.net)
2. Inicia sesión
3. Ve a tu perfil
4. Pega la clave completa en "Clave OpenGPG"
5. Guarda los cambios

---

## 5. **Subir la clave a keyservers (recomendado)**

```bash
gpg --send-keys 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
```

---

## 6. **Configurar el entorno para empaquetado**

### Configurar Git para usar GPG:
```bash
git config --global user.signingkey 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
git config --global commit.gpgsign true
```

### Configurar debuild para firmar paquetes:
Asegúrate de que tu `~/.devscripts` contenga:
```
DEBSIGN_KEYID=0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
```

---

## 7. **Comandos útiles de gestión GPG**

### Ver información detallada de una clave:
```bash
gpg --list-secret-keys --keyid-format LONG
```

### Exportar clave para backup:
```bash
gpg --export-secret-keys --armor 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5 > mi-clave-privada.asc
```

### Importar una clave:
```bash
gpg --import mi-clave-privada.asc
```

### Renovar expiración:
```bash
gpg --edit-key 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
# Luego escribir: expire
```

---

## 8. **Verificar que todo funciona**

```bash
echo "test" | gpg --clearsign
```

---

## 🚨 **Buenas Prácticas**

1. **Backup**: Guarda tu clave privada en un lugar seguro
2. **Expiración**: Usa 1-2 años de expiración para claves de empaquetado
3. **Seguridad**: Protege tu clave con una contraseña fuerte
4. **Revocación**: Crea un certificado de revocación por si pierdes la clave

---

## 🔧 **Solución de Problemas Comunes**

### Si gpg no encuentra la clave:
```bash
export GPG_TTY=$(tty)
```

### Si hay problemas de permisos:
```bash
chmod 700 ~/.gnupg
```

### Para verificar la firma de un paquete:
```bash
debsigs --verify mi-paquete.deb
```
