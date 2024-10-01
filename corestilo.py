import streamlit as st
import requests
import json
import re
import difflib
from html import escape

# Configuración de la página
st.set_page_config(
    page_title="Corrector de Texto con Together API",
    page_icon="📝",
    layout="wide",
)

# Título de la aplicación
st.title("📝 Corrector de Texto: Ortografía, Gramática y Estilo")
st.write(
    """
    Esta aplicación permite corregir la ortografía, gramática y estilo de un texto de hasta **1000 palabras** utilizando la API de Together.
    **Nota:** El texto encerrado entre comillas (citas textuales) y las notas a pie de página no serán alterados durante la corrección.
    """
)

# Función para contar palabras
def contar_palabras(texto):
    palabras = re.findall(r'\b\w+\b', texto)
    return len(palabras)

# Función para extraer citas textuales y reemplazarlas por marcadores
def extraer_citas(texto):
    """
    Encuentra todas las citas textuales en el texto y las reemplaza por marcadores únicos.
    Retorna el texto modificado y un diccionario de marcadores a citas.
    """
    citas_unicas = {}
    texto_modificado = texto
    marcador_idx = 1

    # Patrón para encontrar texto entre comillas dobles o simples
    patron_citas = r'(["\'])(?:(?=(\\?))\2.)*?\1'

    # Encontrar todas las citas
    for match in re.finditer(patron_citas, texto):
        cita_completa = match.group(0)
        marcador = f"__QUOTE_{marcador_idx}__"
        citas_unicas[marcador] = cita_completa
        texto_modificado = texto_modificado.replace(cita_completa, marcador, 1)
        marcador_idx += 1

    return texto_modificado, citas_unicas

# Función para extraer notas a pie de página y reemplazarlas por marcadores
def extraer_pies(texto):
    """
    Encuentra todas las referencias y definiciones de notas a pie de página en el texto y las reemplaza por marcadores únicos.
    Retorna el texto modificado y un diccionario de marcadores a pies de página.
    """
    pies_unicos = {}
    texto_modificado = texto
    marcador_ref_idx = 1
    marcador_def_idx = 1

    # Patrón para referencias de notas a pie de página, por ejemplo: [^1], [^a], etc.
    patron_referencias = r'\[\^[^\]]+\]'
    referencias = re.finditer(patron_referencias, texto)

    # Reemplazar referencias
    for match in referencias:
        ref = match.group(0)
        marcador = f"__FOOTNOTE_REF_{marcador_ref_idx}__"
        pies_unicos[marcador] = ref
        texto_modificado = texto_modificado.replace(ref, marcador, 1)
        marcador_ref_idx += 1

    # Patrón para definiciones de notas a pie de página, por ejemplo: [^1]: Texto de la nota
    # Incluye múltiples líneas si están indentadas
    patron_definiciones = r'\[\^[^\]]+\]:\s*.*(?:\n\s+.*)*'
    definiciones = re.finditer(patron_definiciones, texto_modificado, re.MULTILINE)

    # Reemplazar definiciones
    for match in definiciones:
        defn = match.group(0)
        marcador = f"__FOOTNOTE_DEF_{marcador_def_idx}__"
        pies_unicos[marcador] = defn
        texto_modificado = texto_modificado.replace(defn, marcador, 1)
        marcador_def_idx += 1

    return texto_modificado, pies_unicos

# Función para reintegrar citas textuales en el texto corregido
def reintegrar_citas(texto_corregido, citas_unicas):
    """
    Reemplaza los marcadores en el texto corregido por las citas originales.
    """
    for marcador, cita in citas_unicas.items():
        texto_corregido = texto_corregido.replace(marcador, cita)
    return texto_corregido

# Función para reintegrar pies de página en el texto corregido
def reintegrar_pies(texto_corregido, pies_unicos):
    """
    Reemplaza los marcadores en el texto corregido por las notas a pie de página originales.
    """
    for marcador, pie in pies_unicos.items():
        texto_corregido = texto_corregido.replace(marcador, pie)
    return texto_corregido

# Función para resaltar diferencias con colores específicos
def resaltar_diferencias(original, corregido):
    """
    Resalta las diferencias entre el texto original y el corregido.
    - Rojo para eliminaciones
    - Verde para adiciones
    - Amarillo para modificaciones
    """
    matcher = difflib.SequenceMatcher(None, original, corregido)
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.append(escape(corregido[j1:j2]))
        elif tag == 'delete':
            # Eliminaciones: Mostrar texto eliminado en rojo con tachado
            eliminado = escape(original[i1:i2])
            result.append(f"<span style='color:red;text-decoration:line-through;'>{eliminado}</span>")
        elif tag == 'insert':
            # Adiciones: Mostrar texto añadido en verde
            añadido = escape(corregido[j1:j2])
            result.append(f"<span style='color:green;'>{añadido}</span>")
        elif tag == 'replace':
            # Modificaciones: Mostrar texto original en rojo tachado y el nuevo en amarillo
            original_text = escape(original[i1:i2])
            corregido_text = escape(corregido[j1:j2])
            result.append(f"<span style='color:red;text-decoration:line-through;'>{original_text}</span> <span style='background-color:yellow;'>{corregido_text}</span>")
    # Unir todas las partes
    return ''.join(result)

# Entrada de texto por el usuario
texto_usuario = st.text_area(
    "Ingrese el texto que desea corregir (máximo 1000 palabras):",
    height=300,
)

# Mostrar el contador de palabras
num_palabras = contar_palabras(texto_usuario)
st.write(f"**Número de palabras:** {num_palabras}/1000")

# Botón para enviar el texto
if st.button("Corregir Texto"):
    if num_palabras == 0:
        st.error("Por favor, ingrese algún texto para corregir.")
    elif num_palabras > 1000:
        st.error("El texto excede el límite de 1000 palabras. Por favor, reduzca el tamaño.")
    else:
        with st.spinner("Procesando..."):
            try:
                # Extraer citas y obtener el texto sin alterar las citas
                texto_sin_citas, citas_unicas = extraer_citas(texto_usuario)

                # Extraer pies de página y obtener el texto sin alterar las notas
                texto_sin_citas_pies, pies_unicos = extraer_pies(texto_sin_citas)

                # Obtener la clave de API de los secretos de Streamlit
                api_key = st.secrets["TOGETHER_API_KEY"]

                # Definir la URL de la API
                url = "https://api.together.xyz/v1/chat/completions"

                # Configurar los encabezados
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                # Crear el mensaje para la API
                prompt = (
                    "Por favor, corrige el siguiente texto mejorando la ortografía, gramática y estilo, manteniendo intactas las citas textuales y las notas a pie de página:\n\n"
                    f"{texto_sin_citas_pies}"
                )

                # Configurar el payload
                payload = {
                    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "messages": [
                        {"role": "system", "content": "Eres un asistente que corrige textos."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2512,
                    "temperature": 0.7,
                    "top_p": 0.7,
                    "top_k": 50,
                    "repetition_penalty": 1,
                    "stop": ["<|eot_id|>"],
                    "stream": False,  # Usar False para simplificar la respuesta
                }

                # Realizar la solicitud POST a la API
                response = requests.post(url, headers=headers, data=json.dumps(payload))

                # Verificar si la solicitud fue exitosa
                if response.status_code == 200:
                    respuesta_json = response.json()
                    # Extraer el contenido de la respuesta
                    mensaje_corregido = respuesta_json.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # Reintegrar las notas a pie de página originales en el texto corregido
                    mensaje_corregido_con_pies = reintegrar_pies(mensaje_corregido, pies_unicos)

                    # Reintegrar las citas originales en el texto corregido con pies
                    mensaje_corregido_final = reintegrar_citas(mensaje_corregido_con_pies, citas_unicas)

                    # Mostrar el texto corregido en dos columnas
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Texto Corregido:")
                        st.markdown(mensaje_corregido_final)

                    with col2:
                        st.subheader("Cambios Realizados:")
                        # Resaltar diferencias entre el texto original y el corregido con citas y pies reintegrados
                        diff_html = resaltar_diferencias(texto_usuario, mensaje_corregido_final)
                        # Mostrar el HTML de las diferencias
                        st.markdown(diff_html, unsafe_allow_html=True)
                else:
                    st.error(f"Error en la solicitud: {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
