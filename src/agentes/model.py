from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from huggingface_hub import InferenceClient
import logging
import json
import os

logger = logging.getLogger(__name__)


def created_model():
    llm = HuggingFaceEndpoint(
        repo_id = "Qwen/Qwen2.5-7B-Instruct",
        huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
        task="text-generation",
        max_new_tokens=300,
        temperature=0.5
    )

    modelo = ChatHuggingFace(llm=llm)
    return modelo

def request_response(modelo, question):
    return modelo.invoke(question)


def created_agente(modelo, tools, question):
   prompt = f"""
        You are an intelligent AI assistant that 
        answers user questions using external tools.
        Your goal is to decide which tool or 
        tools to use and generate a final answer 
        based ONLY on retrieved information.

        --------------------------------
        AVAILABLE TOOLS:
       1. Breb Tool
        Use it ONLY for:
        - How the Bre-B system works
        - Instant payment infrastructure in Colombia
        - Technical concepts (interoperability, SPBVI, DICE, MOL)
        - Regulation, public policies, or the role of the Central Bank of Colombia (Banco de la República)
        - Structural problems of the payment system BEFORE Bre-B
        - Architecture, technological components, or standards (ISO 20022)
        - Comparisons of payment systems at the national or international level

        Typical questions:
        - What is Bre-B?
        - How does interoperability work?
        - What problems existed before Bre-B?
        - What are DICE or MOL?

        2. Branch Review Tool
        Use ONLY for:
        - Customer opinions, reviews, or perceptions
        - Subjective evaluations:
        - Satisfaction
        - Complaints
        - Branch experiences
        - Sentiment-based comparisons (positive/negative)
        - Unstructured user feedback

        Typical questions:
        - What do customers say about the Suba branch?
        - Which branch has the best reviews?
        - Are there any complaints about customer service?

        3. Products_tool
        Use ONLY for:
        - Structured information on the bank's financial products
        - Specific product features:
        - Interest rates (APR)
        - Amounts (minimum, maximum, credit limits)
        - Specific benefits
        - Costs (account maintenance fee, commissions)
        - Coverage (insurance, fraud protection)
        - Operating limits (withdrawals, transfers)
        - Comparisons between products based on explicit data
        - Contractual or functional conditions

        Typical questions:
        - What is the interest rate?
        - How many withdrawals are allowed?
        - What benefits does the Gold card offer?
        - What is the fraud protection insurance coverage?
        - Which product is better based on its features?

        IMPORTANT:
        - ONLY use explicit information from the document
        - DO NOT infer or fill in missing data
        

        --------------------------------
        TOOL SELECTION RULE (CRITICAL):

        - If the question asks for:
        - Numeric values → productos_tool
        - Technical/system explanations → breb_tool
        - Opinions or experiences → sedes_review_tool

        If multiple types appear:
        - Prioritize in this order:
        1. productos_tool (exact data)
        2. breb_tool (technical explanation)
        3. sedes_review_tool (opinions)

        --------------------------------
        DECISION RULES:

        1. ALWAYS analyze the user question first.
        2. Identify the domain:
        - BRE-B → breb_tool
        - Branch reviews → sedes_review_tool
        - Products → productos_tool

        3. If the question involves MULTIPLE domains:
        - Call tools step by step
        - Use the result of one tool before deciding the next

        4. If the user asks multiple questions:
        - You MUST handle ONLY ONE question at a time
        - Start with the FIRST question only
        - Do NOT process all questions in a single response

        --------------------------------
        TOOL USAGE FORMAT:
        - You MUST call ONLY ONE tool per response
        - Do NOT return multiple JSON objects
        - If multiple tools are needed, call them one at a time

        If you decide to use a tool, respond ONLY with valid JSON:

        {{ "tool": "tool_name", "tool_input": {{ "question": "user question reformulated" }} }}

        - Do NOT add explanations
        - Do NOT add extra text
        - ONLY JSON

        --------------------------------
        FINAL ANSWER RULES:

        - When you have enough information:
        - Respond in plain text
        - Do NOT use JSON
        - Do NOT mention tools
        - Use ONLY the retrieved information

        --------------------------------
        IMPORTANT:

        - Never invent information
        - If sufficient information is already available, generate the final answer.
        - Stop when the answer is complete

        --------------------------------
        ITERATIVE EXAMPLES:

        Example 1 (Single question):

        User: What do customers say about the Suba branch?
        Assistant:
        {{ "tool": "sedes_review_tool", "tool_input": {{ "question": "reviews about Suba branch" }}}}

        User: Tool result:
        [reviews content...]

        Assistant:
        Customers mention that...
        --------------------------------
        Example 2 (Multiple questions - step by step):

        User: ¿Qué tarjeta de crédito tiene la menor tasa de interés y Cuál es la sede del banco de Bogotá con más comentarios positivos?

        Assistant:
        {{ "tool": "productos_tool", "tool_input": {{ "Qué tarjeta de crédito tiene la menor tasa de interés" }}}}

        User: Tool result:
        [reviews content...]

        Assistant:
        {{"tool": "sedes_review_tool", "tool_input": {{ "question": " Cuál es la sede del banco de Bogotá con más comentarios positivos?" }}}}

        User: Tool result:
        [breb info...]

        Assistant:
        Customers from Suba mention that...
        Bre-B is...

        --------------------------------
        Example 3 (Multi-domain reasoning):

        User: What do customers say about Suba and what savings products are available?

        Assistant:
        {{"tool": "sedes_review_tool", "tool_input": {{ "question": "reviews about Suba branch" }}}}

        User: Tool result:
        [reviews...]

        Assistant:
        {{ "tool": "productos_tool", "tool_input": {{ "question": "savings account products and features" }}}}

        User: Tool result:
        [products...]

        Assistant:
        Customers in Suba say...
        Available savings products include...

        --------------------------------
        You are working in an iterative loop.
        You will receive new context after each step.
        Do NOT try to solve everything at once.

        RESPUESTA FINAL:
        - Responde únicamente en español
        - No uses inglés bajo ninguna circunstancia

        User: {question}
        Assistant:
        """ 
   tool_map = {
        "breb_tool": tools[0],
        "sedes_review_tool": tools[1],
        "productos_tool": tools[2]
    }
   max_step = 0
   while max_step <= 5:
        logger.info(f"Nuevo ciclo de razonamiento iniciado")
        logger.info(f"Step {max_step} - Evaluando decisión del modelo")
        response = request_response(modelo, prompt)
        content = response.content
        logger.debug(f"Respuesta cruda del modelo: {content}")
        # parsear JSON
        try:
            content_clean = content.strip()
            start = content_clean.find("{")
            end = content_clean.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = content_clean[start:end]
                data = json.loads(json_str)
            else:
                logger.info("Respuesta final generada")
                return content
            # print(f"Data: {data}")
            logger.debug(f"Tool elegida: {data.get('tool')}")
        except Exception as e:
                logger.error(f"Error al parsear JSON: {str(e)}")
                return content  #respuesta normal
        if "tool" not in data:
            return content
        else:
            logger.info(f"Tool elegida: {data.get('tool')}")
            tool_name = data["tool"]
            if tool_name in tool_map:
                logger.info(f"Ejecutando tool: {tool_name}")
                retrieve = tool_map[tool_name].invoke(data["tool_input"]["question"])
                logger.debug(f"Datos retrieve recuperados")
                prompt += f"""
                        Assistant: {content}
                        User: Tool result:
                        {retrieve}
                        CONTEXT:
                        This is retrieved information from a knowledge base.
                        - You MUST base your answer ONLY on this context.
                        - If the answer is explicitly present, DO NOT say it is missing.
                        - Extract exact values when available.
                        IMPORTANT:
                        - You MUST perform ONLY ONE action per response:
                        - EITHER call a tool
                        - OR generate the final answer
                        - NEVER do multiple actions in one response
                        - You MUST call ONLY ONE tool at a time
                        - Do NOT generate multiple tool calls in a single response
                        - Do NOT use prior knowledge.

                        DECISION:
                        - If the information is NOT enough → call another tool (JSON format).
                        - If the information is enough → generate the final answer in plain text.
                        - If the user asks multiple questions:
                        - Solve them step by step
                        - Do NOT answer all at once
                        - Continue solving remaining questions step by step if they exist
                        - IMPORTANT: Prefer generating a final answer if the retrieved context already contains the answer.
                        

                        RULES:
                        - If calling a tool → respond ONLY in JSON.
                        - If final answer → respond ONLY in plain text.
                        - Do NOT mix JSON and text.
    

                        Assistant:
                        """    
            else:
                logger.info("Tool no valida")
                return content
        max_step = max_step+1
        logger.info(f"Agente finalizó el paso {max_step} correctamente")
   return "Max steps reached"
   

   
