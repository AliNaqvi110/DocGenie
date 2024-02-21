# import libraries
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from htmlTemplates import css, bot_template, user_template



# get text data from pdfs
def get_text(docs):
    text=""
    for file in docs:                                # for number of  document
        if file.type == "application/pdf":
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:               # for each document
                text += page.extract_text()             # extracting text
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            document = Document(file)
            for paragraph in document.paragraphs:
                text += paragraph.text       
        else:
            print("file Type Not Supported")
    return text


# get multiple chunks from the text
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


# get vector
def get_vectorstore(text_chunks):
    # generate embddings
    embeddings =  OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore


# get conversations
def get_conversations(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain


# handle user question
def  handleQuestion(user_question):
    if st.session_state.conversations is not None:  # Check if conversations is not None
        response = st.session_state.conversations({'question': user_question})
        st.session_state.chat_history = response['chat_history']

        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)




def main():
    # function to load API keys
    load_dotenv()

    # set layout
    st.set_page_config(page_title="Doc Genie", page_icon=":books")
    # Define CSS code
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    .reportview-container .sidebar-content {display: none;}
    .stDeployButton {visibility: hidden;}
    #stDecoration {display: none;}
    </style>
    """

    # Display the CSS code
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


    # Add css
    st.write(css, unsafe_allow_html=True)

    # initialize session state
    if "conversations" not in st.session_state:
        st.session_state.conversations=None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history=None

    # Add logo image
    st.image("assets/logo.png", width=80)
    # add header
    st.header("Doc Genie")
    user_question = st.text_input("Ask a question about your document")

    if user_question:
        handleQuestion(user_question)


    # side bar
    with st.sidebar:
        st.subheader("Your Document")                                                   # Sub Header
        pdf_docs = st.file_uploader("Upload your PDFs", type=['pdf', 'docx'], accept_multiple_files=True)     # file Uploader 
        if st.button("Process"):                                                        # button
            
            # Add Spinner
            with st.spinner("Processing"):
                # get pdf text
                raw_text = get_text(pdf_docs)

                # get text chunks
                text_chunks = get_text_chunks(raw_text)


                # create vector store
                vectorstore = get_vectorstore(text_chunks)

                # create conversations
                st.session_state.conversations = get_conversations(vectorstore)



if __name__ == '__main__':
    main()