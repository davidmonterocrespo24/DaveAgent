"""
Test para verificar la generación automática de títulos de sesión
"""
import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import UserMessage


async def test_title_generation():
    """Prueba la generación de títulos usando el LLM"""
    
    # Configurar cliente
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key="sk-d1c818b3ebdb410cab1114f1182e4481",
        base_url="https://api.deepseek.com",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
        }
    )
    
    # Simular conversación
    conversation = """user: Crea un archivo main.py con una función que calcule números fibonacci
assistant: Voy a crear el archivo main.py con la función fibonacci.
user: Ahora agrega tests unitarios
assistant: He agregado los tests en test_main.py"""
    
    # Prompt para generar título
    title_prompt = f"""Based on the following conversation, generate a short, descriptive title (maximum 50 characters).
The title should capture the main topic or task being discussed.

CONVERSATION:
{conversation}

Generate ONLY the title text, nothing else. Make it concise and descriptive.
Examples: "Python API Development", "Bug Fix in Authentication", "Database Migration Setup"

TITLE:"""
    
    print("🧪 Probando generación de título...\n")
    print(f"📝 Conversación:\n{conversation}\n")
    
    # Generar título
    result = await model_client.create(
        messages=[UserMessage(content=title_prompt, source="user")]
    )
    
    title = result.content.strip().strip('"').strip("'").strip()
    
    if len(title) > 50:
        title = title[:47] + "..."
    
    print(f"✅ Título generado: {title}\n")
    
    # Cerrar cliente
    await model_client.close()
    
    return title


if __name__ == "__main__":
    print("=" * 60)
    print("TEST: Generación Automática de Títulos de Sesión")
    print("=" * 60)
    
    asyncio.run(test_title_generation())
    
    print("\n✅ Test completado!")
