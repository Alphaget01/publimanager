import discord
from discord.ext import commands
from discord import app_commands
from utils_py.firestore import db
import logging
import aiohttp
import os

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenerarMensajeModal(discord.ui.Modal):
    def __init__(self, titulo: str = None):
        super().__init__(title="Generar Mensaje")

        self.titulo = discord.ui.TextInput(
            label="Título del Proyecto",
            placeholder="Ingrese el título del proyecto",
            style=discord.TextStyle.short,
            required=True,
            default=titulo
        )
        self.add_item(self.titulo)

        self.capitulo = discord.ui.TextInput(
            label="Capítulo",
            placeholder="Ingrese el capítulo",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.capitulo)

        self.tmo_link = discord.ui.TextInput(
            label="Link de TMO",
            placeholder="Ingrese el link de TMO",
            style=discord.TextStyle.short,
            required=False
        )
        self.add_item(self.tmo_link)

        self.imagen = discord.ui.TextInput(
            label="URL de la Imagen",
            placeholder="Ingrese la URL de la imagen",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.imagen)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            logger.info("Iniciando procesamiento del modal para generar mensaje.")

            # Obtener ID del servidor
            server_id = str(interaction.guild_id)
            logger.info(f"ID del servidor: {server_id}")

            # Obtener configuración general del servidor
            config_ref = db.collection(f'servidores/{server_id}/configugeneral').document('main')
            logger.info("Obteniendo configuración general del servidor.")
            config_doc = config_ref.get()

            if not config_doc.exists:
                raise ValueError("No se encontró la configuración general del servidor.")

            config = config_doc.to_dict()
            if not isinstance(config, dict):
                raise TypeError("La configuración del servidor no es un diccionario válido.")
            logger.info(f"Configuración general obtenida: {config}")

            # Buscar el proyecto en la base de datos
            proyecto_ref = db.collection(f'servidores/{server_id}/proyectos').where('titulo', '==', self.titulo.value)
            proyectos = proyecto_ref.stream()
            proyecto = next(proyectos, None)

            if not proyecto:
                raise ValueError(f"No se encontró el proyecto con el título '{self.titulo.value}'.")

            proyecto_data = proyecto.to_dict()
            logger.info(f"Datos del proyecto encontrados: {proyecto_data}")

            # Datos obtenidos
            titulo = proyecto_data.get('titulo', 'Título no encontrado')
            sinopsis = proyecto_data.get('sinopsis', 'Sin sinopsis disponible')
            link_ikigai = proyecto_data.get('link_ikigai', '#')

            # Obtener roles etiquetados para agradecimientos
            ide_roles = [config.get(f'ide_{i}') for i in range(1, 6) if config.get(f'ide_{i}')]
            ido_roles = [config.get(f'ido_{i}') for i in range(1, 6) if config.get(f'ido_{i}')]

            menciones_ide = ' '.join([f'<@&{role_id}>' for role_id in ide_roles])
            menciones_ido = ' '.join([f'<@&{role_id}>' for role_id in ido_roles])

            # Construir el mensaje
            mensaje = (
                f":mega:| {menciones_ide}\n"
                f":loudspeaker: Buenas, nuevo capítulo de **{titulo}** :rotating_light:\n"
                f"# :newspaper2: Capítulo {self.capitulo.value}\n"
                f"# :link: [Link de Ikigai](<{link_ikigai}>)\n"
            )

            # Agregar el link de TMO si está presente
            if self.tmo_link.value.strip():
                mensaje += f":link: [Link de TMO](<{self.tmo_link.value}>)\n"

            mensaje += ":newspaper2: Gracias a todo el staff por el trabajo realizado :hearts:\n"

            # Agradecimientos a los roles de donadores
            if menciones_ido:
                mensaje += f":newspaper2: Gracias a {menciones_ido} por apoyar el proyecto :hearts:\n"

            mensaje += f"⊳Sinopsis:\n```{sinopsis}```\n"

            # Obtener el canal configurado
            canal_id = config.get('id_canalp')
            if not canal_id:
                raise ValueError("No se configuró un canal para publicaciones en este servidor.")

            canal = interaction.guild.get_channel(int(canal_id))
            if not canal:
                raise ValueError("El canal configurado no es válido o no existe en este servidor.")

            # Descargar y adjuntar la imagen
            async with aiohttp.ClientSession() as session:
                async with session.get(self.imagen.value) as resp:
                    if resp.status == 200:
                        file_path = "temp_image.png"
                        with open(file_path, "wb") as f:
                            f.write(await resp.read())
                        await canal.send(content=mensaje, file=discord.File(file_path))
                        os.remove(file_path)
                    else:
                        raise ValueError("No se pudo descargar la imagen desde la URL proporcionada.")

            await interaction.response.send_message("¡Mensaje publicado!", ephemeral=True)
            logger.info("¡Mensaje enviado exitosamente!")

        except Exception as e:
            logger.error(f"Error al procesar el modal: {e}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error al Generar Mensaje",
                    description=str(e),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

async def autocomplete_titulos(interaction: discord.Interaction, current: str):
    try:
        logger.info(f"Iniciando autocompletado de títulos con filtro: {current}")
        server_id = str(interaction.guild_id)
        proyectos_ref = db.collection(f'servidores/{server_id}/proyectos')
        proyectos = proyectos_ref.stream()

        matching_titulos = [
            proyecto.to_dict().get('titulo', '')
            for proyecto in proyectos
            if current.lower() in proyecto.to_dict().get('titulo', '').lower()
        ]

        return [app_commands.Choice(name=titulo, value=titulo) for titulo in matching_titulos[:25]]
    except Exception as e:
        logger.error(f"Error en el autocompletado: {e}")
        return []

async def setup(bot: commands.Bot):
    @app_commands.command(name="generarmensaje", description="Abre un formulario para generar un mensaje.")
    @app_commands.autocomplete(titulo=autocomplete_titulos)
    async def generarmensaje(interaction: discord.Interaction, titulo: str):
        modal = GenerarMensajeModal(titulo=titulo)
        await interaction.response.send_modal(modal)

    bot.tree.add_command(generarmensaje)
