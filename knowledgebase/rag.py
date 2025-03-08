from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from uagents import Agent, Context, Protocol, Model
from langchain_community.docstore.in_memory import InMemoryDocstore
from canvas import get_all_course_materials
import os
import faiss
from dotenv import load_dotenv
from parse_files import extract_text_from_files

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

class QueryRequest(Model):
    query: str

class QueryResponse(Model):
    response: str

query_agent = Agent(
    name="query_agent",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"]
)

QUERY_AGENT_ADDRESS = query_agent.address

query_protocol = Protocol("Query Protocol")

faiss_path = "faiss_db"
index_file = os.path.join(faiss_path, "index.faiss")


def chunk_and_embed_canvas_data():
    all_materials = get_all_course_materials()
    docs = []

    for course_name, data in all_materials.items():
        for assignment in data["assignments"]:
            if isinstance(assignment, dict):
                docs.append(f"Course: {course_name}, Assignment: {assignment.get('name', 'Unnamed Assignment')}, "
                            f"Description: {assignment.get('description', 'No Description')}")


    course_files_text = extract_text_from_files("course_files")
    docs.extend(course_files_text)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunked_docs = [chunk for doc in docs for chunk in text_splitter.split_text(doc)]


    if os.path.exists(faiss_path) and os.path.exists(index_file):
        vector_store = FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)
    else:
        index = faiss.IndexFlatL2(1536) 
        vector_store = FAISS(
            index=index,
            embedding_function=embedding_model,
            docstore=InMemoryDocstore({}),
            index_to_docstore_id={},
        )

        vector_store.add_texts(chunked_docs, embedding=embedding_model.embed_documents)
        vector_store.save_local(faiss_path)

    return vector_store

vector_store = chunk_and_embed_canvas_data()
retriever = vector_store.as_retriever()

llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY)

prompt_template = ChatPromptTemplate.from_template(
    """You are an AI-powered study assistant specializing in helping students with their coursework. 
    You have access to a rich database of course materials, including lecture notes, assignments, and study guides. 
    Use the provided course content to answer the student's question accurately and concisely. 
    If the answer is not found in the course materials, provide guidance on how the student can find the answer.

    ### Context (from course materials):
    {context}

    ### Student's Question:
    {input}

    ### Your Answer (as a helpful tutor):"""
)


combine_docs_chain = create_stuff_documents_chain(
    llm=llm,
    prompt=prompt_template
)

retrieval_chain = create_retrieval_chain(
    retriever=retriever,
    combine_docs_chain=combine_docs_chain
)

@query_protocol.on_message(model=QueryRequest)
async def query_rag_system(ctx: Context, sender: str, query: QueryRequest):
    ctx.logger.info(f"Query Agent received query: {query.query}")

    retrieved_docs = retriever.invoke(query.query)
    context = "\n".join([doc.page_content for doc in retrieved_docs])

    response = retrieval_chain.invoke({"input": query.query, "context": context})

    await ctx.send(sender, QueryResponse(response=response['answer']))

query_agent.include(query_protocol)

if __name__ == "__main__":
    query_agent.run()
