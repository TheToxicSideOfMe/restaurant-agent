from langchain_core.tools import tool
from sqlalchemy.orm import Session
from openai import OpenAI
import json
import os

from app.services.rag_service import search_knowledge_base
from app.models.order import Order


def make_tools(db: Session):
    """
    Returns the two agent tools with db session injected via closure.
    Called once per request in chat.py, so each request gets its own db scope.
    """

    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

    @tool
    def search_menu(query: str) -> str:
        """
        Search the restaurant's menu, prices, opening hours, delivery zones, and payment methods.
        Use this whenever the customer asks anything about food, drinks, availability, or restaurant info.
        """
        return search_knowledge_base(query, db)

    @tool
    def place_order(
        customer_name: str,
        customer_phone: str,
        customer_address: str,
        items: str
    ) -> str:
        """
        Place a customer order. Use this only after you have collected:
        - customer_name
        - customer_phone
        - customer_address
        - items (what they want to order, as a plain string like '2x burger, 1x juice')
        Do NOT call this tool until all four fields are confirmed by the customer.
        """

        # Parse the plain string into structured JSON using a small LLM call
        parse_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a data parser. Convert the order string into a JSON array. "
                        "Each element must have 'name' (string) and 'quantity' (integer). "
                        "Return ONLY the JSON array, no explanation, no markdown."
                    )
                },
                {
                    "role": "user",
                    "content": items
                }
            ],
            temperature=0
        )

        raw = parse_response.choices[0].message.content.strip()

        try:
            parsed_items = json.loads(raw)
        except json.JSONDecodeError:
            return "Sorry, I couldn't parse the order items. Please ask the customer to clarify what they want."

        price_context = search_knowledge_base("menu prices", db)

        price_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a price calculator. Given a list of ordered items and a price list, "
                        "calculate the total price. Return ONLY a number with no currency symbol, "
                        "no explanation, no markdown. Example: 15.000"
                    )
                },
                {
                    "role": "user",
                    "content": f"Items: {json.dumps(parsed_items)}\n\nPrice list:\n{price_context}"
                }
            ],
            temperature=0
        )
        
        try:
            total_price = float(price_response.choices[0].message.content.strip())
        except ValueError:
            total_price = 0.0
        
        order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            items=json.dumps(parsed_items),   # store as JSON string in DB
            total_price=total_price,
            status="pending"
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return (
            f"Order placed successfully! Order ID: {order.id}. "
            f"We'll deliver to {customer_address}. Thank you, {customer_name}!"
        )

    return [search_menu, place_order]