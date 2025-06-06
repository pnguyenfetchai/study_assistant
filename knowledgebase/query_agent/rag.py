import os
import sys
import faiss
from dotenv import load_dotenv

# Add parent directories to Python path for imports
sys.path.append('../..')
sys.path.append('../../agents')

# Import agent-related modules
from uagents import Agent, Context, Protocol, Model
from datetime import datetime
from uuid import uuid4
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec
)

# Create chat protocol
def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(),
        msg_id=uuid4(),
        content=content
    )

chat_proto = Protocol(spec=chat_protocol_spec)
# Import LangChain modules
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.docstore.in_memory import InMemoryDocstore

# Import local modules
from canvas import get_all_course_materials
from parse_files import extract_text_from_files


load_dotenv()

# Load environment variables
load_dotenv()

# Get OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize embedding model
embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Agent addresses
ANALYZER_AGENT = "agent1qfpkhksvee55f2seqvejtsrr6wr9s4gcfz8as53htmqyr6uuvhewjxnvu07"
CANVAS_AGENT = "agent1q053mc5vkw5pxx0xhx54v4y2l34chwyn4jsw9eahvlrfrt8pfc73c6arh6y"

class QueryRequest(Model):
    query: str

class RequestResponse(Model):
    request: str
    response: str

query_agent = Agent(
    name="query_agent",
    port=8001,
    seed="query agent secret phrase deployment",
    mailbox=True
)

QUERY_AGENT_ADDRESS = query_agent.address

problem_protocol = Protocol("Problem Solving")
# query_protocol = Protocol("Query Handling")

faiss_path = "faiss_db"
index_file = os.path.join(faiss_path, "index.faiss")


def chunk_and_embed_canvas_data(canvas_token: str, school_domain: str):
    """Initialize and update the vector store with Canvas course materials"""
    try:
        # Get course materials using provided credentials
        all_materials = get_all_course_materials(canvas_token, school_domain)
        if not all_materials:
            print("No course materials found")
            return None

        docs = []
        # First, store the list of courses
        course_list = "Currently enrolled courses:\n"
        for course_name, data in all_materials.items():
            course_list += f"- {course_name}\n"
        docs.append(course_list)

        # Then store assignment details
        for course_name, data in all_materials.items():
            assignments = data.get("assignments", [])
            if isinstance(assignments, list):
                for assignment in assignments:
                    if isinstance(assignment, dict):
                        docs.append(f"Course: {course_name}, Assignment: {assignment.get('name', 'Unnamed Assignment')}, "
                                f"Description: {assignment.get('description', 'No Description')}")

        # Add course files
        course_files_text = extract_text_from_files("course_files")
        docs.extend(course_files_text)

        if not docs:
            print("No documents to embed")
            return None

        # Process and chunk documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        processed_docs = []
        
        for doc in docs:
            if isinstance(doc, dict):
                # Document with metadata
                chunks = text_splitter.split_text(doc['page_content'])
                for chunk in chunks:
                    processed_docs.append({
                        'page_content': chunk,
                        'metadata': doc.get('metadata', {})
                    })
            else:
                # Plain text document
                chunks = text_splitter.split_text(doc)
                for chunk in chunks:
                    processed_docs.append({
                        'page_content': chunk,
                        'metadata': {'type': 'general'}
                    })

        # Create or load vector store
        if os.path.exists(faiss_path) and os.path.exists(index_file):
            vector_store = FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)
        else:
            if not os.path.exists(faiss_path):
                os.makedirs(faiss_path)
            
            index = faiss.IndexFlatL2(1536)
            vector_store = FAISS(
                index=index,
                embedding_function=embedding_model,
                docstore=InMemoryDocstore({}),
                index_to_docstore_id={},
            )

        # Batch add all documents with their metadata
        texts = [doc['page_content'] for doc in processed_docs]
        metadatas = [doc['metadata'] for doc in processed_docs]
        vector_store.add_texts(texts, metadatas=metadatas, embedding=embedding_model.embed_documents)
        vector_store.save_local(faiss_path)
        return vector_store

    except Exception as e:
        print(f"Error in chunk_and_embed_canvas_data: {str(e)}")
        return None

# Initialize these as None - they'll be set up when we get credentials
vector_store = None
retriever = None
llm = None
retrieval_chain = None

def initialize_rag_system(canvas_token: str, school_domain: str) -> bool:
    global vector_store, retriever, retrieval_chain, llm
    """Initialize the RAG system with Canvas credentials"""
    print(f"I am in here {canvas_token}, {school_domain}")
    
    try:
        # Initialize vector store with Canvas data
        vector_store = chunk_and_embed_canvas_data(canvas_token, school_domain)
        if not vector_store:
            raise ValueError("Failed to initialize vector store")

        # Create retriever
        retriever = vector_store.as_retriever()

        # Initialize LLM
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        llm = ChatOpenAI(model_name="gpt-4", api_key=OPENAI_API_KEY)

        # Create prompt template
        prompt_template = ChatPromptTemplate.from_template(
            """You are an AI-powered study assistant that helps students with their coursework. 
            You have access to a rich RAG database of course materials, including lecture notes, assignments, and study guides.
            Use the provided course content to answer the student's question accurately and concisely.

            If the course content is insufficient, generate a plausible answer based on your knowledge.
            Always start with 'Based on the course content' and provide a thoughtful response.

            If asked to create a chart or diagram, generate reasonable data from the content or fabricate plausible values.
            Include all necessary legends, labels, and explanations.

            {context}

            Student's Question: {input}

            Your Answer (as a helpful tutor):"""
        )

        # Create chain
        combine_docs_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=prompt_template
        )

        # Create retrieval chain
        retrieval_chain = create_retrieval_chain(
            retriever=retriever,
            combine_docs_chain=combine_docs_chain
        )

        return True
    except Exception as e:
        print(f"Error initializing RAG system: {str(e)}")
        raise

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    try:
        # Always send acknowledgment first
        await ctx.send(
            sender,
            ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
        )

        for item in msg.content:
            if isinstance(item, StartSessionContent):
                ctx.logger.info(f"Got a start session message from {sender}")
                continue
            elif isinstance(item, TextContent):
                ctx.logger.info(f"Got a message from {sender}: {item.text}")
                # Handle the text message
                await process_chat_message(ctx, sender, item.text)
            else:
                # If we get an error, send it back as a chat message
                await ctx.send(
                    sender,
                    create_text_chat(f"Error: Unexpected content type", end_session=True)
                )
    except Exception as e:
        # Send errors back as chat messages
        await ctx.send(
            sender,
            create_text_chat(f"Error: {str(e)}", end_session=True)
        )

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )

async def process_chat_message(ctx: Context, sender: str, text_content: str):
    """Process the actual chat message content"""
    try:
        # Check if this is an initialization message
        if ',' in text_content:
            try:
                canvas_token, school_domain = map(str.strip, text_content.split(','))
                success = initialize_rag_system(canvas_token, school_domain)
                if success:
                    await ctx.send(sender, create_text_chat("RAG system initialized successfully. You can now query the knowledge base."))
                else:
                    await ctx.send(sender, create_text_chat("Failed to initialize RAG system. Please check your credentials."))
            except ValueError:
                await ctx.send(sender, create_text_chat("Invalid format. Please provide credentials in the format: <canvas_token>, <school_domain>"))
            return

        # If not initialization, check if system is ready
        if vector_store is None or retrieval_chain is None:
            await ctx.send(sender, create_text_chat("RAG system not initialized. Please provide credentials in the format: <canvas_token>, <school_domain>"))
            return

        # Process the query using sync invoke since we're in an async context
        response = retrieval_chain.invoke({"input": text_content})
        response_text = response.get("answer", "Sorry, I couldn't find relevant information in the knowledge base.")
        
        # Send the response back
        await ctx.send(sender, create_text_chat(response_text))
    except Exception as e:
        error_msg = f"Error querying knowledge base: {str(e)}"
        ctx.logger.error(error_msg)
        await ctx.send(sender, create_text_chat(error_msg))

query_agent.include(problem_protocol)
query_agent.include(chat_proto)


@query_agent.on_message(model=RequestResponse)
async def handle_request(ctx: Context, sender: str, query: RequestResponse):
    global vector_store, retriever, retrieval_chain
    try:
        if query.request.startswith("init_rag,"):
            # Initialize RAG system with the provided token
            ctx.logger.info("Initializing RAG system with Canvas token")
            _, canvas_token, school_domain = query.request.split(",")
            try:
                success = initialize_rag_system(canvas_token, school_domain)
                if success:
                    await ctx.send(sender, RequestResponse(request=query.request, response="RAG system initialized successfully"))
                else:
                    await ctx.send(sender, RequestResponse(request=query.request, response="Failed to initialize RAG system"))
            except Exception as e:
                ctx.logger.error(f"Error initializing RAG system: {str(e)}")
                await ctx.send(sender, RequestResponse(request=query.request, response=f"Error initializing RAG system: {str(e)}"))
            return

        if not vector_store or not retriever or not retrieval_chain:
            ctx.logger.error("RAG system not initialized")
            await ctx.send(sender, RequestResponse(request=query.request, response="Please provide your Canvas token first"))
            return

        ctx.logger.info(f"Query Agent received query: {query.request}")

        try:
            # Use the retrieval chain directly instead of manual document handling
            ctx.logger.info("Using retrieval chain to generate response")
            
            # For course enrollment queries, prioritize course list documents
            if any(word in query.request.lower() for word in ['enrolled', 'courses', 'taking']):
                search_kwargs = {"filter": {"type": "course_list"}}
                retrieved_docs = retriever.invoke(query.request, search_kwargs=search_kwargs)
            else:
                retrieved_docs = retriever.invoke(query.request)
                
            context = "\n".join([doc.page_content for doc in retrieved_docs])
            response = retrieval_chain.invoke({"input": query.request, "context": context})
            answer = response['answer'] if isinstance(response, dict) else str(response)
            
            ctx.logger.info(f"Generated response: {answer}")
            ctx.logger.info(f"Sender: {sender}")
            ctx.logger.info(f"CANVAS_AGENT: {CANVAS_AGENT}")
            ctx.logger.info(f"xau trai: {context}")


            if sender == CANVAS_AGENT:
                await ctx.send(ANALYZER_AGENT, RequestResponse(request=query.request, response=f"{answer}\n\nContext: {context}"))
            else:
                await ctx.send(sender, RequestResponse(request=query.request, response=f"{answer}\n\nContext: {context}"))
        except Exception as e:
            ctx.logger.error(f"Error processing query: {str(e)}")
            await ctx.send(sender, RequestResponse(request=query.request, response="Sorry, I encountered an error processing your query. Please try again."))
    except Exception as e:
        ctx.logger.error(f"Error in handle_request: {str(e)}")
        await ctx.send(sender, RequestResponse(request=query.request, response=f"Error: {str(e)}"))

@query_agent.on_message(model=QueryRequest)
async def handle_problem_solving(ctx: Context, sender: str, query: QueryRequest):  
    global vector_store, retriever, retrieval_chain
    try:
        ctx.logger.info(f"Query Agent received problem-solving request: {query.query}")
        
        if not vector_store or not retriever or not retrieval_chain:
            ctx.logger.error("RAG system not initialized")
            await ctx.send(sender, RequestResponse(request=query.query, response="Please provide your Canvas token first"))
            return

        try:
            # Use the retrieval chain directly instead of manual document handling
            response = retrieval_chain.invoke({"input": query.query})
            answer = response['answer'] if isinstance(response, dict) else str(response)
            
            ctx.logger.info(f"Generated response: {answer}")

            await ctx.send(sender, RequestResponse(request=query.query, response=answer))
        except Exception as e:
            ctx.logger.error(f"Error processing query: {str(e)}")
            await ctx.send(sender, RequestResponse(request=query.query, response="Sorry, I encountered an error processing your query. Please try again."))
    except Exception as e:
        ctx.logger.error(f"Error in handle_problem_solving: {str(e)}")
        await ctx.send(sender, RequestResponse(request=query.query, response=f"Error: {str(e)}"))

if __name__ == "__main__":
    query_agent.run()