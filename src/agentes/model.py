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

        1. breb_tool
        Use for:
        - BRE-B system
        - Payment systems in Colombia
        - Regulations or technical explanations

        2. sedes_review_tool
        Use for:
        - Customer reviews of bank branches
        - Specific locations (Suba, Chapinero, etc.)
        - Complaints or satisfaction

        3. productos_tool
        Use for:
        - Bank products
        - Interest rates
        - Account features and benefits

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
        - Never answer without using tools (if domain applies)
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

        User: What do customers say about Suba and what is Bre-B?

        Assistant:
        {{ "tool": "sedes_review_tool", "tool_input": {{ "question": "reviews about Suba branch" }}}}

        User: Tool result:
        [reviews content...]

        Assistant:
        {{"tool": "breb_tool", "tool_input": {{ "question": "What is Bre-B?" }}}}

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
   max_step = 0
   while max_step <= 5:
        logger.info(f"Nuevo ciclo de razonamiento iniciado")
        logger.info(f"Step {max_step} - Evaluando decisión del modelo")
        max_step = max_step+1
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
            if data["tool"] == "breb_tool":
                logger.info(f"Ejecutando tool: {data['tool']}")
                retrieve = tools[0].invoke(data["tool_input"]["question"])
                logger.debug(f"Datos retrieve recuperados")
                prompt += f"""
                        Assistant: {content}
                        User: Tool result:
                        {retrieve}
                        CONTEXT:
                        This is retrieved information from a knowledge base.
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
                        

                        RULES:
                        - If calling a tool → respond ONLY in JSON.
                        - If final answer → respond ONLY in plain text.
                        - Do NOT mix JSON and text.
    

                        Assistant:
                        """    
            
            elif data["tool"] == "sedes_review_tool":
                logger.info(f"Ejecutando tool: {data['tool']}")
                retrieve = tools[1].invoke(data["tool_input"]["question"])
                logger.debug(f"Datos retrieve recuperados")
                prompt += f"""
                        Assistant: {content}          
                        User: Tool result:
                        {retrieve}
                        CONTEXT:
                        This is retrieved information from a knowledge base.
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

                        RULES:
                        - If calling a tool → respond ONLY in JSON.
                        - If final answer → respond ONLY in plain text.
                        - Do NOT mix JSON and text.

                        Assistant:
                        """    
                              
            elif data["tool"] == "productos_tool":
                logger.info(f"Ejecutando tool: {data['tool']}")
                retrieve = tools[2].invoke(data["tool_input"]["question"])
                logger.debug(f"Datos retrieve recuperados")
                prompt += f"""
                        Assistant: {content}
                        User: Tool result:
                        {retrieve}
                        CONTEXT:
                        This is retrieved information from a knowledge base.
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
                        

                        RULES:
                        - If calling a tool → respond ONLY in JSON.
                        - If final answer → respond ONLY in plain text.
                        - Do NOT mix JSON and text.

                        Assistant:
                        """     
            else:
                logger.info("Tool no valida")
                return content
        logger.info("Agente finalizó correctamente")
   return "Max steps reached"
   

   
