from uagents import Protocol, Model

class RequestResponse(Model):
    request: str
    response: str

class QueryRequest(Model):
    query: str

query_protocol = Protocol("Query Handling")

# Export the protocol and models
__all__ = ["query_protocol", "RequestResponse", "QueryRequest"]
