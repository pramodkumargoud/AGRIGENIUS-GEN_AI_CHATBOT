from flask import Flask, render_template, request, jsonify
import requests
import PyPDF2
from itertools import chain
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_together import Together
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from googletrans import Translator
from langdetect import detect
from dotenv import load_dotenv
import os

app = Flask(__name__)

'''
# Function to fetch content from a website
def fetch_website_content(url):
    response = requests.get(url)
    return response.text
'''
# Function to extract text from a PDF file
def extract_pdf_text(pdf_file):
    with open(pdf_file, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

# Split the combined content into smaller chunks
def split_text(text, chunk_size=500, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_text(text)
    return chunks

# Initialize embeddings and vector store
def initialize_vector_store(contents):
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    web_chunks = list(chain.from_iterable(split_text(content) for content in contents))
    db = Chroma.from_texts(web_chunks, embedding_function)
    return db

load_dotenv()
together_api_key = os.getenv('API_KEY')

llm = Together(
    model="meta-llama/Llama-2-70b-chat-hf",
    max_tokens=256,
    temperature=0.1,
    top_k=1,
    together_api_key=together_api_key
)

# Set up the retrieval QA chain
def setup_retrieval_qa(db):
    retriever = db.as_retriever(similarity_score_threshold=0.6)

    # Define the prompt template
    prompt_template = """Please answer questions related to Agriculture. Try explaining in simple words. Answer in less than 100 words. If you don't know the answer, simply respond with 'Don't know.'
     CONTEXT: {context}
     QUESTION: {question}"""

    PROMPT = PromptTemplate(template=f"[INST] {prompt_template} [/INST]", input_variables=["context", "question"])

    # Initialize the RetrievalQA chain
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        input_key='query',
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
        verbose=True
    )
    return chain

def translate_text(text):
    """Translate text to English if it is not already in English."""
    try:
        # Check if the text is too short to accurately detect
        if len(text) <= 5:
            return text, "en"
        
        detected_lang = detect(text)
        if detected_lang != "en":
            translator = Translator()
            translation = translator.translate(text, src=detected_lang, dest='en')
            return translation.text, detected_lang
        return text, "en"
    except Exception as e:
        return str(e), None


def translate_from_english(result, target_lang):
    """Translate text from English to the specified target language."""
    try:
        if target_lang != "en":
            translator = Translator()
            translation = translator.translate(result, src='en', dest=target_lang)
            return translation.text
        return result
    except Exception as e:
        return str(e)

# Initialize the vector store and RetrievalQA chain
urls = ["https://mospi.gov.in/4-agricultural-statistics"]
pdf_files = ["Data/farmerbook.pdf"]               # ["Data/Farming Schemes.pdf", "Data/farmerbook.pdf"]

#website_contents = [fetch_website_content(url) for url in urls]
pdf_texts = [extract_pdf_text(pdf_file) for pdf_file in pdf_files]
all_contents = pdf_texts   #  + website_contents

db = initialize_vector_store(all_contents)
chain = setup_retrieval_qa(db)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            query = request.form['query']
            translated_query, detected_lang = translate_text(query)
            
            print(f"Translated query: {translated_query}")
            print(f"Detected language: {detected_lang}")
            
            # Check if chain is callable
            if callable(chain):
                response = chain.invoke({"query": translated_query})

                print(f"Raw response: {response}")
                
                if isinstance(response, dict) and 'result' in response:
                    result = response['result']
                elif isinstance(response, str):
                    result = response
                else:
                    result = str(response)
                
                print(f"Processed result: {result}")
                
                translated_response = translate_from_english(result, detected_lang)
                return jsonify({'response': translated_response, 'status': 'success'})
            else:
                return jsonify({'response': 'Error: chain is not callable', 'status': 'error'})
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return jsonify({'response': f'An error occurred: {str(e)}', 'status': 'error'})
    return render_template('index.html')


