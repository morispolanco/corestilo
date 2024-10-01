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
    """
)

# Función para contar palabras
def contar_palabras(texto):
    palabras = re.findall(r'\b\w+\b', texto)
    return len(palabras)

# Función para resaltar diferencias
def resaltar_diferencias(original, corregido):
    # Escapar HTML para evitar problemas de formato
    original_esc = escape(original)
    corregido_esc = escape(corregido)
    
    # Crear un objeto Differ
    differ = difflib.HtmlDiff()
    
    # Generar la tabla de diferencias
    diff_html = differ.make_table(original_esc.splitlines(), corregido_esc.splitlines(), fromdesc='Original', todesc='Corregido', context=True, numlines=2)
    
    return diff_html

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
                    "Por favor, corrige el siguiente texto mejorando la ortografía, gramática y estilo:\n\n"
                    f"{texto_usuario}"
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
                    mensaje = respuesta_json.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # Mostrar el texto corregido en dos columnas
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Texto Corregido:")
                        st.write(mensaje)

                    with col2:
                        st.subheader("Cambios Realizados:")
                        diff_html = resaltar_diferencias(texto_usuario, mensaje)
                        # Mostrar el HTML de las diferencias
                        st.markdown(diff_html, unsafe_allow_html=True)
                else:
                    st.error(f"Error en la solicitud: {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
