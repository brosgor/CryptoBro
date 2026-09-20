# CryptoBro Wiki

Bienvenido a la Wiki oficial de **CryptoBro**. Aquí encontrarás toda la documentación necesaria para instalar, utilizar y entender el funcionamiento de esta herramienta de seguridad.

## Índice

1. [Introducción](#introducción)
2. [Instalación y Configuración](#instalación-y-configuración)
3. [Guía de Usuario](#guía-de-usuario)
    - [Inicio de la Aplicación](#inicio-de-la-aplicación)
    - [Encriptar Archivos](#encriptar-archivos)
    - [Desencriptar Archivos](#desencriptar-archivos)
    - [Gestión de Claves](#gestión-de-claves)
4. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
5. [Tecnologías](#tecnologías)

---

## Introducción

**CryptoBro** es una aplicación de escritorio robusta diseñada para la protección de archivos mediante criptografía AES. Su filosofía es ofrecer seguridad de grado militar con una experiencia de usuario (UX) simplificada.

### Características Principales
*   **Cápsulas temporales**: cifra un archivo por X años/días/horas/min/seg; la clave no se muestra y el desbloqueo solo se habilita cuando vence el contador (bloqueo suave de UI).
*   **Bóveda cifrada**: la base SQLite solo se abre con tu master password (Scrypt + Fernet).
*   **Encriptación Fernet (AES)**: cifrado autenticado de archivos y mensajes.
*   **Gestión híbrida de claves**: recuerda tu contraseña o usa passphrases de 6 palabras.
*   **Passphrases mnemotécnicas**: frases tipo `sol-montaña-azul-...` (diccionario incluido).
*   **Archivos .bros**: contenedor con extensión original embebida.
*   **GUI**: interfaz Tkinter con tema monocromo e icono de marca.

---

## Instalación y Configuración

### Prerrequisitos
*   **Sistema Operativo**: Linux, Windows o MacOS.
*   **Python**: Versión 3.x instalada.

### Pasos de Instalación

1.  **Clonar el Repositorio**
    ```bash
    git clone http://localhost:3000/brosgor/CryptoBro.git
    cd CryptoBro
    ```

2.  **Configurar Entorno Virtual** (Altamente Recomendado)
    ```bash
    python -m venv venv
    # Linux/Mac
    source venv/bin/activate
    # Windows
    .\venv\Scripts\activate
    ```

3.  **Instalar Dependencias**
    ```bash
    pip install -r requirements.txt
    ```

---

## Guía de Usuario

### Inicio de la Aplicación
```bash
python src/main.py
```
La primera vez te pedirá **crear una bóveda** (nombre + clave de bloqueo). Puedes tener **varias bóvedas**.

En la pantalla de inicio: Nueva / Eliminar / Restaurar backup.  
En **Claves** (bóveda abierta): Cambiar clave, Vaciar, Eliminar, Exportar `.gor`.

### Encriptar Archivos
La pestaña **"Encrypt File"** es el punto de partida.

1.  **File to Encrypt**: Selecciona cualquier archivo de tu sistema.
2.  **Encryption Key**: Define una contraseña maestra para este cifrado.
3.  **Store key in database?**:
    *   ✅ **Activado (Recomendado)**:
        *   El sistema generará una **Passphrase Mnemotécnica** única.
        *   Se te ofrecerá guardar un archivo `.par` (contiene la frase y se guarda en la misma carpeta del archivo original).
        *   *Ventaja*: No necesitas recordar la `Encryption Key`, solo necesitas el archivo `.par` o recordar la frase generada.
    *   ⬜ **Desactivado (Modo Paranoico)**:
        *   No se guarda nada en la base de datos.
        *   *Advertencia*: Si olvidas la `Encryption Key`, el archivo será irrecuperable.
4.  Haz clic en **Encrypt**. El archivo original se transformará cifrado y cambiara a formato `.bros`.

### Desencriptar Archivos
Dirígete a la pestaña **"Decrypt File"**.

1.  **File to Decrypt**: Selecciona el archivo `.bros`.
2.  **Selecciona el Modo**:
    *   **Manual Key**: Si encriptaste sin guardar en la BD. Ingresa la contraseña exacta.
    *   **From Database**: Si usaste el modo gestionado.
        *   Haz clic en **"Load .par"** y selecciona tu archivo de recuperación.
        *   O escribe manualmente tu frase (ej. `gato-nube-verde`).
3.  Haz clic en **Decrypt**. El archivo recuperará su nombre y extensión originales.

### Gestión de Claves
En la pestaña **"Stored Keys"** puedes auditar tu seguridad.

*   **Tabla de Registros**: Muestra el ID, el Hash de la passphrase (por seguridad nunca se muestra la frase real) y la extensión original del archivo.
*   **Limpieza**: Puedes seleccionar registros antiguos y eliminarlos permanentemente con el botón **"Delete Selected"**.

---

## Arquitectura del Proyecto

Para desarrolladores que deseen contribuir o entender el código.

### Estructura de Directorios

| Ruta | Descripción |
| :--- | :--- |
| `src/main.py` | Entry point. Inicializa la `CryptoApp`. |
| `src/gui/` | **Presentación**. Contiene `app.py` con la lógica de Tkinter, widgets y eventos. |
| `src/service/` | **Aplicación**. `cryptoService.py` orquesta la comunicación entre la GUI y el Dominio. |
| `src/domain/` | **Dominio**. `cryptoBro.py` contiene la lógica pura de criptografía (Fernet, PBKDF2). |
| `src/models/` | **Datos**. `secure_data.py` define la estructura de los objetos (Data Classes). |
| `src/repository/` | **Persistencia**. `database.py` gestiona las conexiones SQLite. |
| `data/` | **Recursos**. Contiene `secure.db` (BD), `words.json` (diccionario) y archivos `.par` generados. |

### Flujo de Datos
`GUI` -> `Service` -> `Domain` (Cifrado) / `Repository` (Persistencia) -> `SQLite`

---

## Tecnologías

Este proyecto está construido sobre hombros de gigantes:

*   **Lenguaje**: [Python 3](https://www.python.org/)
*   **GUI Framework**: [Tkinter](https://docs.python.org/3/library/tkinter.html) (Nativo)
*   **Seguridad**: [Cryptography](https://cryptography.io/en/latest/) (Librería estándar de facto)
*   **Base de Datos**: [SQLite3](https://www.sqlite.org/index.html)

---
*CryptoBro - Seguridad accesible para todos.*  