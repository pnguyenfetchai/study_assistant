from uagents import Protocol, Model

class QueryRequest(Model):
    query: str

problem_protocol = Protocol("Problem Solving")

# Export the protocol and models
__all__ = ["problem_protocol", "QueryRequest"]
