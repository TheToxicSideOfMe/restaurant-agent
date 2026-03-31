from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from sqlalchemy.orm import Session
import os


SYSTEM_PROMPT = """You are a helpful customer support agent for a Tunisian restaurant.

You help customers with:
- Questions about the menu, prices, opening hours, delivery zones, and payment methods
- Placing food orders

When placing an order, you MUST collect ALL of the following before calling place_order:
1. Customer full name
2. Customer phone number
3. Delivery address
4. What they want to order (items and quantities)

Ask for missing information one step at a time. Be friendly, concise, and professional.
If the customer asks something unrelated to the restaurant, politely let them know you can only help with restaurant-related topics.
"""


def build_graph(db: Session):
    """
    Builds and compiles the LangGraph agent graph.
    Called once per request in chat.py with the request-scoped db session.
    """

    # Import here to avoid circular imports
    from app.agent.tools import make_tools

    tools = make_tools(db)

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0.7
    )

    # Bind tools to LLM — now the LLM knows what tools exist and can call them
    llm_with_tools = llm.bind_tools(tools)

    # Agent node — LLM thinks, decides whether to call a tool or respond
    def agent_node(state: MessagesState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Tool node — executes whatever tool the LLM decided to call
    tool_node = ToolNode(tools)

    # Build the graph
    graph = StateGraph(MessagesState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")

    # Conditional edge: if LLM called a tool → go to tools node, else → END
    graph.add_conditional_edges("agent", tools_condition)

    # After tool runs, always go back to agent
    graph.add_edge("tools", "agent")

    return graph.compile()