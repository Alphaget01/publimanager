import discord
from discord.ext import commands
from discord import app_commands
from utils_py.firestore import db
import logging

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActualizarProyectoModal(discord.ui.Modal):
    """
    Modal para capturar los datos de un proyecto a actualizar.
    """
    def __init__(self, titulo: str = None):
        super().__init__(title="Actualizar Proyecto")

        # Nombre del proyecto (autocompletado)
        self.nombre_actual = discord.ui.TextInput(
            label="Nombre del Proyecto",
            placeholder="Proyecto seleccionado",
            style=discord.TextStyle.short,
            required=True,
            default=titulo
        )
        self.add_item(self.nombre_actual)

        # Nuevo nombre del proyecto
        self.nombre_nuevo = discord.ui.TextInput(
            label="Nuevo Nombre del Proyecto",
            placeholder="Ingrese el nuevo nombre del proyecto",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.nombre_nuevo)

        # Sinopsis actualizada
        self.sinopsis = discord.ui.TextInput(
            label="Sinopsis Actualizada",
            placeholder="Ingrese la nueva sinopsis (opcional)",
            style=discord.TextStyle.paragraph,
            required=False
        )
        self.add_item(self.sinopsis)

    async def on_submit(self, interaction: discord.Interaction):
        """
        Procesa los datos ingresados en el modal y los guarda en Firestore.
        """
        try:
            # Obtener ID del servidor
            server_id = str(interaction.guild_id)
            proyectos_ref = db.collection(f'servidores/{server_id}/proyectos')

            # Buscar el proyecto por título
            proyecto = proyectos_ref.where('titulo', '==', self.nombre_actual.value).get()
            if not proyecto:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Error",
                        description="No se encontró el proyecto especificado.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            # Construir campos a actualizar
            campos_a_actualizar = {"titulo": self.nombre_nuevo.value}
            if self.sinopsis.value.strip():
                campos_a_actualizar["sinopsis"] = self.sinopsis.value.strip()

            # Actualizar los campos
            proyecto_ref = proyectos_ref.document(proyecto[0].id)
            proyecto_ref.update(campos_a_actualizar)

            # Confirmación al usuario
            embed = discord.Embed(
                title="Proyecto Actualizado",
                description=f"**Nombre anterior:** {self.nombre_actual.value}\n"
                            f"**Nuevo Nombre:** {self.nombre_nuevo.value}\n"
                            f"**Sinopsis:** {self.sinopsis.value.strip() or 'Sin cambios'}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error al actualizar proyecto: {e}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error al Actualizar Proyecto",
                    description=str(e),
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


async def autocomplete_proyectos(interaction: discord.Interaction, current: str):
    """
    Autocompletado para el campo de título basado en los proyectos existentes en Firestore.
    """
    try:
        logger.info(f"Iniciando autocompletado de proyectos con filtro: {current}")
        server_id = str(interaction.guild_id)
        proyectos_ref = db.collection(f'servidores/{server_id}/proyectos')
        proyectos = proyectos_ref.stream()

        matching_titulos = [
            proyecto.to_dict().get('titulo', '')
            for proyecto in proyectos
            if current.lower() in proyecto.to_dict().get('titulo', '').lower()
        ]

        logger.info(f"Resultados del autocompletado: {matching_titulos[:25]}")
        return [app_commands.Choice(name=titulo, value=titulo) for titulo in matching_titulos[:25]]
    except Exception as e:
        logger.error(f"Error en el autocompletado: {e}")
        return []


async def setup(bot: commands.Bot):
    """
    Configura el comando /actualizarproyecto en el árbol de comandos del bot.
    """
    @app_commands.command(name="actualizarproyecto", description="Abre un formulario para actualizar un proyecto.")
    @app_commands.autocomplete(titulo=autocomplete_proyectos)
    async def actualizarproyecto(interaction: discord.Interaction, titulo: str):
        """
        Comando slash para mostrar el formulario interactivo.
        """
        logger.info(f"Ejecutando comando /actualizarproyecto con título: {titulo}")
        modal = ActualizarProyectoModal(titulo=titulo)
        await interaction.response.send_modal(modal)

    bot.tree.add_command(actualizarproyecto)
    logger.info("Comando /actualizarproyecto registrado correctamente.")
