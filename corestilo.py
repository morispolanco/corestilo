import streamlit as st
import requests
import difflib
import re

# Configuración de la página
st.set_page_config(
    page_title="Corrector de Texto",
    layout="wide",
)

# Título de la aplicación
st.title("Corrector de Ortografía, Gramática y Estilo")

# Función para contar palabras
def count_words(text):
    return len(text.split())

# Área de texto para que el usuario ingrese el texto
user_input = st.text_area(
    "Pega tu texto aquí (máximo 2000 palabras):",
    height=300,
)

# Mostrar el conteo de palabras
word_count = count_words(user_input)
st.write(f"**Conteo de palabras:** {word_count}")

# Validación del límite de palabras
if word_count > 2000:
    st.error("El texto excede el límite de 2000 palabras. Por favor, reduce la longitud.")
else:
    if st.button("Corregir Texto"):
        if word_count == 0:
            st.warning("Por favor, ingresa algún texto para corregir.")
        else:
            with st.spinner("Corrigiendo el texto..."):
                # Obtener la clave de API de los secretos
                api_key = st.secrets["TOGETHER_API_KEY"]

                # Definir la URL de la API
                api_url = "https://api.together.xyz/v1/chat/completions"

                # Preparar los mensajes para la API
                # Instrucción para corregir el texto sin alterar las citas
                prompt = (
                    "Corrige la ortografía, gramática y estilo del siguiente texto sin modificar "
                    "las citas textuales (encerradas entre comillas simples, dobles o angulares):\n\n"
                    f"{user_input}"
                )

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

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
                    "stream": False  # Para simplificar, usamos stream=False
                }

                try:
                    response = requests.post(api_url, headers=headers, json=payload)
                    response.raise_for_status()
                    result = response.json()

                    # Extraer el texto corregido
                    corrected_text = result["choices"][0]["message"]["content"]

                    # Función para resaltar cambios
                    def highlight_differences(original, corrected):
                        # Usar difflib para obtener las diferencias
                        diff = difflib.ndiff(original.split(), corrected.split())
                        result = []
                        for word in diff:
                            if word.startswith('- '):
                                # Eliminado: rojo
                                result.append(f'<span style="color:red;">{word[2:]}</span>')
                            elif word.startswith('+ '):
                                # Agregado: verde
                                result.append(f'<span style="color:green;">{word[2:]}</span>')
                            elif word.startswith('? '):
                                # Cambiado: amarillo
                                pass  # Podemos ignorar estos indicadores
                            else:
                                # Sin cambios
                                result.append(word[2:])
                        return ' '.join(result)

                    # Generar el texto con resaltado
                    highlighted_text = highlight_differences(user_input, corrected_text)

                    # Mostrar los resultados en dos columnas
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Texto Corregido")
                        st.write(corrected_text)

                    with col2:
                        st.subheader("Cambios Realizados")
                        # Usar Markdown con HTML para los colores
                        st.markdown(highlighted_text, unsafe_allow_html=True)

                except requests.exceptions.RequestException as e:
                    st.error(f"Ocurrió un error al comunicarse con la API: {e}")
                except KeyError:
                    st.error("Respuesta inesperada de la API.")
