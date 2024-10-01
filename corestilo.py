import streamlit as st
import requests
import re
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from streamlit_quill import st_quill
from html import escape

# Configuración de la página
st.set_page_config(page_title="Corrector de Texto Avanzado", layout="wide")

# Título de la aplicación
st.title("Corrector de Texto con Resaltado de Cambios")

# Instrucciones para el usuario
st.markdown("""
**Instrucciones:**
- Pega tu texto con formato (máximo 2000 palabras) en el editor de texto enriquecido.
- La aplicación corregirá la ortografía, gramática y estilo.
- Las notas a pie de página y citas textuales (entre comillas) no serán modificadas.
- Los cambios se resaltarán en colores:
  - 🟨 **Amarillo**: Cambios realizados.
  - 🟥 **Rojo**: Eliminaciones.
  - 🟩 **Verde**: Adiciones.

**Nota:** Asegúrate de que las notas a pie de página estén en el formato `[1]`, `[2]`, etc., y que las citas textuales estén entre comillas dobles `"cita"`.
""")

# Editor de texto enriquecido para la entrada del usuario
user_input_html = st_quill(
    label="Editor de Texto:",
    placeholder="Pega tu texto con formato aquí...",
    theme="snow",
    height=300,
)

# Función para contar palabras (considerando texto plano)
def count_words(text):
    return len(re.findall(r'\b\w+\b', text))

# Función para proteger notas a pie de página y citas textuales
def protect_text(html):
    soup = BeautifulSoup(html, "lxml")
    placeholders = {}

    # Proteger citas textuales (texto entre comillas dobles)
    quotes = soup.find_all(string=re.compile(r'"[^"]+"'))
    for idx, quote in enumerate(quotes):
        original_quote = quote.strip()
        placeholder = f"__QUOTE_{idx}__"
        placeholders[placeholder] = original_quote
        new_quote = original_quote.replace(original_quote, placeholder)
        quote.replace_with(new_quote)

    # Proteger notas a pie de página en formato [1], [2], etc.
    footnotes = soup.find_all(string=re.compile(r'\[\d+\]'))
    for idx, footnote in enumerate(footnotes):
        original_footnote = footnote.strip()
        placeholder = f"__FOOTNOTE_{idx}__"
        placeholders[placeholder] = original_footnote
        new_footnote = original_footnote.replace(original_footnote, placeholder)
        footnote.replace_with(new_footnote)

    protected_html = str(soup)
    return protected_html, placeholders

# Función para restaurar notas a pie de página y citas textuales
def restore_text(html, placeholders):
    for placeholder, original in placeholders.items():
        html = html.replace(placeholder, original)
    return html

# Función para extraer texto plano del HTML
def extract_text(html):
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text()

# Función para llamar a la API de Together
def correct_text(text, api_key):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Mensaje de sistema para la API
    system_message = (
        "Eres un asistente que corrige la ortografía, gramática y estilo de un texto. "
        "No debes modificar las notas a pie de página ni las citas textuales (texto entre comillas)."
    )

    # Mensaje de usuario con el texto a corregir
    user_message = text

    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 2512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<|eot_id|>"],
        "stream": False  # Cambiado a False para simplificar
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        # Asumiendo que la respuesta contiene el texto corregido en 'choices'[0]['message']['content']
        corrected_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return corrected_text
    else:
        st.error(f"Error en la API: {response.status_code} - {response.text}")
        return None

# Función para resaltar los cambios
def highlight_changes(original, corrected):
    matcher = SequenceMatcher(None, original, corrected)
    highlighted = ""
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            highlighted += escape(original[i1:i2])
        elif tag == 'replace':
            highlighted += f"<span style='background-color: yellow;'>{escape(corrected[j1:j2])}</span>"
        elif tag == 'delete':
            highlighted += f"<span style='background-color: red; text-decoration: line-through;'>{escape(original[i1:i2])}</span>"
        elif tag == 'insert':
            highlighted += f"<span style='background-color: green;'>{escape(corrected[j1:j2])}</span>"
    return highlighted

# Botón para iniciar la corrección
if st.button("Corregir Texto"):
    if not user_input_html.strip():
        st.warning("Por favor, ingresa un texto para corregir.")
    else:
        # Extraer texto plano para contar palabras
        plain_text = extract_text(user_input_html)
        total_words = count_words(plain_text)
        if total_words > 2000:
            st.error(f"El texto excede el límite de 2000 palabras. Actualmente tiene {total_words} palabras.")
        else:
            with st.spinner("Corrigiendo el texto..."):
                # Proteger las notas a pie de página y las citas textuales
                protected_html, placeholders = protect_text(user_input_html)

                # Extraer texto plano del HTML protegido
                protected_text = extract_text(protected_html)

                # Llamar a la API con el texto protegido
                api_key = st.secrets["together_api_key"]
                corrected_protected = correct_text(protected_text, api_key)

                if corrected_protected:
                    # Restaurar las notas a pie de página y las citas textuales
                    corrected_html = restore_text(protected_html, placeholders)

                    # Aquí es donde podrías necesitar ajustar cómo se inserta el texto corregido.
                    # Actualmente, se asume que la API devuelve texto plano.
                    # Para una integración más precisa, podrías necesitar parsear y reemplazar segmentos específicos.

                    # Resaltar los cambios
                    highlighted_text = highlight_changes(plain_text, corrected_protected)

                    # Dividir la página en dos columnas
                    col1, col2 = st.columns(2)

                    with col1:
                        st.header("Texto Original")
                        st.markdown(user_input_html, unsafe_allow_html=True)

                    with col2:
                        st.header("Texto Corregido")
                        st.markdown(f"<div style='white-space: pre-wrap;'>{highlighted_text}</div>", unsafe_allow_html=True)
