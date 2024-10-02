import streamlit as st
import requests
from langdetect import detect, DetectorFactory
from time import sleep

# Asegurar resultados consistentes de langdetect
DetectorFactory.seed = 0

# Configuración de la página
st.set_page_config(
    page_title="Corrector de Texto Multilingüe",
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
            # Iniciar la barra de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Actualizar progreso inicial
                status_text.text("Detectando el idioma del texto...")
                progress_bar.progress(10)
                sleep(0.5)  # Simular tiempo de procesamiento

                # Detectar el idioma del texto
                try:
                    idioma = detect(user_input)
                except Exception as e:
                    st.error(f"No se pudo detectar el idioma: {e}")
                    progress_bar.empty()
                    status_text.empty()
                    st.stop()

                idiomas = {
                    'es': 'español',
                    'en': 'inglés',
                    'fr': 'francés',
                    'de': 'alemán',
                    # Agrega más idiomas según sea necesario
                }
                idioma_detectado = idiomas.get(idioma, 'idioma desconocido')

                progress_bar.progress(30)
                status_text.text(f"Idioma detectado: {idioma_detectado}")
                sleep(0.5)  # Simular tiempo de procesamiento

                progress_bar.progress(40)
                status_text.text("Preparando la solicitud a la API...")

                # Obtener la clave de API de los secretos
                api_key = st.secrets["TOGETHER_API_KEY"]

                # Definir la URL de la API
                api_url = "https://api.together.xyz/v1/chat/completions"

                # Instrucción para corregir el texto sin alterar las citas
                prompt = (
                    f"Corrige la ortografía, gramática y estilo del siguiente texto sin modificar "
                    f"las citas textuales (encerradas entre comillas simples, dobles o angulares) en {idioma_detectado}:\n\n"
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

                progress_bar.progress(50)
                status_text.text("Enviando solicitud a la API...")
                sleep(0.5)  # Simular tiempo de procesamiento

                # Realizar la solicitud a la API
                response = requests.post(api_url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()

                progress_bar.progress(70)
                status_text.text("Procesando la respuesta...")
                sleep(0.5)  # Simular tiempo de procesamiento

                # Extraer el texto corregido
                try:
                    corrected_text = result["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as e:
                    st.error(f"Formato de respuesta inesperado de la API: {e}")
                    progress_bar.empty()
                    status_text.empty()
                    st.stop()

                progress_bar.progress(90)
                status_text.text("Finalizando...")

                progress_bar.progress(100)
                status_text.text("¡Corrección completada!")

                # Mostrar el texto corregido
                st.subheader("Texto Corregido")
                st.write(corrected_text)

            except requests.exceptions.RequestException as e:
                st.error(f"Ocurrió un error al comunicarse con la API: {e}")
                progress_bar.empty()
                status_text.empty()
            except KeyError:
                st.error("Respuesta inesperada de la API.")
                progress_bar.empty()
                status_text.empty()
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")
                progress_bar.empty()
                status_text.empty()
