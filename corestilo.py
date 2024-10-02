import streamlit as st
import requests
import re
from langdetect import detect, DetectorFactory
from time import sleep

# Asegurar resultados consistentes de langdetect
DetectorFactory.seed = 0

# Funciones auxiliares para manejar las notas a pie de página
def extract_footnotes(text):
    """
    Extrae las notas a pie de página del texto principal.
    Asume que las notas están al final del texto en formato '1. Nota'.
    """
    footnotes = {}
    # Busca líneas que comienzan con un número seguido de un punto y un espacio
    pattern = re.compile(r'^(\d+)\.\s+(.*)', re.MULTILINE)
    matches = pattern.findall(text)
    for match in matches:
        number, note = match
        footnotes[number] = note
    # Elimina las notas a pie de página del texto principal
    main_text = pattern.sub('', text).strip()
    return main_text, footnotes

def replace_footnote_markers(text):
    """
    Reemplaza los marcadores de notas a pie de página (superscript) con [number].
    Soporta tanto notación ^1 como caracteres superscript Unicode.
    """
    # Mapa de caracteres superscript a números
    superscript_map = {
        '⁰': '0',
        '¹': '1',
        '²': '2',
        '³': '3',
        '⁴': '4',
        '⁵': '5',
        '⁶': '6',
        '⁷': '7',
        '⁸': '8',
        '⁹': '9',
    }

    # Reemplaza ^number con [number]
    text = re.sub(r'\^(\d+)', r'[\1]', text)

    # Reemplaza caracteres superscript con [number]
    for sup, num in superscript_map.items():
        text = text.replace(sup, f'[{num}]')

    return text

def restore_footnote_markers(text):
    """
    Restaura los marcadores de notas a pie de página de [number] a superscript.
    """
    # Mapa de números a caracteres superscript
    superscript_map = {
        '0': '⁰',
        '1': '¹',
        '2': '²',
        '3': '³',
        '4': '⁴',
        '5': '⁵',
        '6': '⁶',
        '7': '⁷',
        '8': '⁸',
        '9': '⁹',
    }

    # Función para reemplazar [number] con superscript
    def replace_brackets(match):
        number = match.group(1)
        superscript = ''.join(superscript_map.get(digit, digit) for digit in number)
        return superscript

    # Reemplaza [number] con superscript
    text = re.sub(r'\[(\d+)\]', replace_brackets, text)

    return text

def append_footnotes(text, footnotes):
    """
    Añade las notas a pie de página al final del texto.
    """
    if not footnotes:
        return text
    footnotes_text = '\n\n' + 'Notas a pie de página:\n'
    for number in sorted(footnotes.keys(), key=lambda x: int(x)):
        footnotes_text += f'{number}. {footnotes[number]}\n'
    return text + footnotes_text

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
                status_text.text("Procesando notas a pie de página...")
                progress_bar.progress(10)
                sleep(0.5)  # Simular tiempo de procesamiento

                # Extraer y procesar notas a pie de página
                main_text, footnotes = extract_footnotes(user_input)
                processed_text = replace_footnote_markers(main_text)

                # Mostrar progreso
                progress_bar.progress(20)
                status_text.text("Detectando el idioma del texto...")
                sleep(0.5)  # Simular tiempo de procesamiento

                # Detectar el idioma del texto
                try:
                    idioma = detect(processed_text)
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
                    'it': 'italiano',
                    'pt': 'portugués',
                    'ru': 'ruso',
                    'zh-cn': 'chino',
                    'ja': 'japonés',
                    'ko': 'coreano',
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
                    f"{processed_text}"
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

                # Restaurar los marcadores de notas a pie de página
                restored_text = restore_footnote_markers(corrected_text)

                # Reinsertar las notas a pie de página
                final_text = append_footnotes(restored_text, footnotes)

                progress_bar.progress(90)
                status_text.text("Finalizando...")
                sleep(0.5)  # Simular tiempo de procesamiento

                progress_bar.progress(100)
                status_text.text("¡Corrección completada!")

                # Mostrar el texto corregido
                st.subheader("Texto Corregido")
                st.write(final_text)

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
