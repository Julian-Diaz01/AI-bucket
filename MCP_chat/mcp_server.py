from mcp.server.fastmcp import FastMCP
from pydantic import Field
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool (
    name="read_doc_contents",
    description="Read the contents of a document and return as a string",
)
def read_document(
    doc_id: str = Field(description="The ID of the document to read")
):
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    return docs[doc_id]
    
@mcp.tool (
    name="edit_doument", 
    description="Edit a documnet by replacing a string in the documents content with a new string")
def edit_document(
    doc_id: str = Field(description="The ID of the document to edit"),
    old_string: str = Field(description="The string to replace"),
    new_string: str = Field(description="The new string to replace the old string with")
):
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    docs[doc_id] = docs[doc_id].replace(old_string, new_string)
    return docs[doc_id]


@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    return list(docs.keys())

# TODO: Write a resource to return the contents of a particular doc
@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def get_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")
    return docs[doc_id]

@mcp.prompt(
    name="rewrite_doc_in_markdown",
    description="Rewrite a doc in markdown format",
)
def rewrite_doc_in_markdown(
    doc_id: str = Field(description="The ID of the document to rewrite"),
) -> list[base.Message]:
    prompt = f"""
Your goal is to reformat a document to be written with markdown syntax.

The id of the document you need to reformat is:
<document_id>
{doc_id}
</document_id>

Add in headers, bullet points, tables, etc as necessary. Feel free to add in structure.
Use the 'edit_document' tool to edit the document. After the document has been reformatted...
"""
    
    return [
        base.UserMessage(prompt)
    ]
# TODO: Write a prompt to summarize a doc


if __name__ == "__main__":
    mcp.run(transport="stdio")
