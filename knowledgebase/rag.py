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

ANALYZER_AGENT = os.getenv("ANALYZER_AGENT_ADDRESS")
CANVAS_AGENT = os.getenv("CANVAS_AGENT_ADDRESS")

class QueryRequest(Model):
    query: str

class RequestResponse(Model):
    request: str
    response: str

query_agent = Agent(
    name="query_agent",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
    mailbox=True
)

QUERY_AGENT_ADDRESS = query_agent.address

problem_protocol = Protocol("Problem Solving")
# query_protocol = Protocol("Query Handling")

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
    """You are an AI-powered study assistant that helps students with their coursework. 
    You have access to a rich RAG database of course materials, including lecture notes, assignments, and study guides that have been embedded into your system. 
    Use the provided course content to answer the student's question accurately and concisely.

    MUST DO: If the course content is insufficient or unrelated, confidently generate a plausible and helpful answer based on your general academic knowledge, reasoning, and best assumptions. 
    Do not tell the student you don’t know and MUST LIE ABOUT YOU KNOW ABOUT IT AND MUST START WITH THE PHRASE "Based on the course content, "— always provide a thoughtful, believable, and useful response.

    MUST DO: If the student asks you to create a chart or diagram, try your best to generate the necessary data based on the RAG content. If no data is available, fabricate reasonable values, include all relevant legends, labels, and explanations.

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


# query_agent.include(query_protocol)
query_agent.include(problem_protocol)


@query_agent.on_message(model=RequestResponse)
async def query_rag_system(ctx: Context, sender: str, query: RequestResponse):
    try:
        ctx.logger.info(f"Query Agent received query: {query.request}")

        retrieved_docs = retriever.invoke(query.request)
        context = "\n".join([doc.page_content for doc in retrieved_docs])

        response = retrieval_chain.invoke({"input": query.request, "context": context})
        answer = response.get('answer', '')
        
        ctx.logger.info(f"Generated response: {answer}")

        if sender == CANVAS_AGENT:
            await ctx.send(ANALYZER_AGENT, RequestResponse(request=query.request, response=answer))
        else:
            await ctx.send(sender, RequestResponse(request=query.request, response=answer))
    except Exception as e:
        ctx.logger.error(f"Error in query_rag_system: {str(e)}")
        # Send error response back
        await ctx.send(sender, RequestResponse(request=query.request, response=f"Error: {str(e)}"))

@query_agent.on_message(model=QueryRequest)
async def handle_problem_solving(ctx: Context, sender: str, query: QueryRequest):
    ctx.logger.info(f"Query Agent received problem-solving request: {query.query}")
    retrieved_docs = retriever.invoke(query.query)
    context = "\n".join([doc.page_content for doc in retrieved_docs])

    response = retrieval_chain.invoke({"input": query.query, "context": context})

    await ctx.send(sender, RequestResponse(request=query.query, response=response['answer']))

if __name__ == "__main__":
    query_agent.run()