import os
import discord
from discord.ext import commands
from comandos_py.agregarproyecto import setup as setup_agregar_proyecto
from comandos_py.generarmensaje import setup as setup_generar_mensaje
from comandos_py.actualizarproyecto import setup as setup_actualizar_proyecto
from comandos_pref.prefiactua import setup as setup_prefixed_commands
from dotenv import load_dotenv
import asyncio
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("El token de Discord no está configurado en las variables de entorno.")

# Configuración de intents
intents = discord.Intents.default()
intents.message_content = True  # Habilitar el contenido de mensajes

# Inicializar bot
bot = commands.Bot(command_prefix="$manager ", intents=intents, help_command=None)  # Prefijo personalizado

# Evento cuando el bot está listo
@bot.event
async def on_ready():
    logger.info(f"Bot conectado como {bot.user}")

    # Sincronizar comandos de barra
    try:
        synced = await bot.tree.sync()
        logger.info(f"Comandos de barra sincronizados: {len(synced)}")
    except Exception as e:
        logger.error(f"Error al sincronizar comandos de barra: {e}")

    # Listar comandos de prefijo registrados
    prefixed_commands = [command.name for command in bot.commands]
    logger.info(f"Comandos con prefijo registrados: {prefixed_commands}")

    # Verificar Cogs registrados
    cogs = list(bot.cogs.keys())
    logger.info(f"Cogs registrados: {cogs}")

# Cargar extensiones de comandos
async def load_extensions():
    """
    Carga todos los comandos de prefijo y barra desde sus respectivos módulos.
    """
    try:
        # Cargar comandos de barra
        await setup_agregar_proyecto(bot)
        logger.info("Comando agregarproyecto cargado.")
        await setup_generar_mensaje(bot)
        logger.info("Comando generarmensaje cargado.")
        await setup_actualizar_proyecto(bot)
        logger.info("Comando actualizarproyecto cargado.")

        # Cargar comandos de prefijo
        await setup_prefixed_commands(bot)
        logger.info("Comandos con prefijo cargados desde prefiactua.py.")

        logger.info("Todas las extensiones cargadas correctamente.")
    except Exception as e:
        logger.error(f"Error al cargar extensiones: {e}")

# Ejecutar el bot
if __name__ == "__main__":
    async def main():
        """
        Función principal para iniciar el bot.
        """
        try:
            async with bot:
                await load_extensions()
                logger.info("Iniciando el bot...")
                await bot.start(TOKEN)
        except Exception as e:
            logger.error(f"Error al iniciar el bot: {e}")

    asyncio.run(main())
