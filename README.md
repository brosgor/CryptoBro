# CryptoBro

CryptoBro es una herramienta desarrollada en Python para encriptar y desencriptar archivos de forma segura. Utiliza estándares de criptografía robustos para proteger tu información, permitiéndote además gestionar las claves de encriptación mediante una base de datos local protegida por contraseña.

## Características

*   **Encriptación de Archivos**: Cifra cualquier tipo de archivo utilizando fernet (implementación de AES simétrico).
*   **Gestión de Claves**:
    *   Genera claves seguras a partir de una contraseña proporcionada por el usuario (usando PBKDF2HMAC con SHA256).
    *   Opción para almacenar la clave de desencriptación y la extensión original del archivo en una base de datos local (`secure.db`).
    *   Recuperación de claves mediante un "passphrase" (frase de contraseña) cuyo hash sirve como índice de búsqueda.
*   **Ofuscación de Extensión**: Los archivos encriptados pasan a tener la extensión `.bros`, ocultando el tipo de archivo original. La extensión original se cifra y se guarda para restaurar el archivo correctamente.

## Requisitos

*   Python 3.x
*   Las dependencias listadas en `requirements.txt`

## Instalación

1.  **Clona el repositorio:**

    ```bash
    git clone http://localhost:3000/brosgor/CryptoBro.git
    cd CryptoBro
    ```

2.  **Crea un entorno virtual (Recomendado):**

    ```bash
    python -m venv venv
    
    # En Linux/MacOS
    source venv/bin/activate
    
    # En Windows
    .\venv\Scripts\activate
    ```

3.  **Instala las dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

## Uso

Para iniciar la aplicación, ejecuta el script principal desde la raíz del proyecto:

```bash
python src/main.py
```

### Menú Principal

Al ejecutar el programa, verás las siguientes opciones:

1.  **Encrypt a file (Encriptar un archivo):**
    *   Te pedirá la ruta del archivo.
    *   Te pedirá una clave (contraseña) para encriptarlo.
    *   Te pedirá una frase de contraseña (opcional) para generar un hash identificador.
    *   Al finalizar, te preguntará si deseas guardar la clave en la base de datos. Si aceptas, podrás recuperar la clave más tarde usando la frase de contraseña.
    *   El archivo resultante tendrá la extensión `.bros`.

2.  **Decrypt a file (Desencriptar un archivo):**
    *   Te pedirá la ruta del archivo `.bros`.
    *   Te preguntará si deseas recuperar la clave desde la base de datos:
        *   **Sí (`y`):** Debes ingresar la frase de contraseña que usaste al encriptar. Si es correcta, el sistema recuperará la clave y la extensión original automáticamente.
        *   **No (`n`):** Deberás ingresar manualmente la clave de desencriptación. *Nota: Si lo haces manualmente y no se conoce la extensión, el archivo se guardará con una extensión por defecto o tendrás que renombrarlo manualmente.*

3.  **View all stored keys (Ver claves almacenadas):**
    *   Muestra una lista de los registros guardados en la base de datos local (hashes, claves encriptadas, extensiones).

4.  **Exit:** Salir de la aplicación.

## Estructura del Proyecto

*   `src/main.py`: Punto de entrada de la aplicación.
*   `src/cli/`: Contiene la lógica de la interfaz de usuario actual.
*   `src/domain/`: Lógica de negocio y criptografía (CryptoBro).
*   `src/repository/`: Manejo de la base de datos SQLite.
*   `src/service/`: Capa de servicio que conecta la interfaz con el dominio.
*   `data/`: Carpeta donde se almacenan la base de datos (`secure.db`) y archivos de prueba.

## Tecnologías Utilizadas

*   **Python**: Lenguaje principal.
*   **Cryptography (Fernet)**: Para encriptación simétrica segura.
*   **SQLite**: Para el almacenamiento local de claves.

---
*Nota: Este proyecto es para fines educativos y de protección personal de datos.*  