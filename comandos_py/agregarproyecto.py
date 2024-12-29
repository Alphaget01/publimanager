import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from utils_py.firestore import db

class AgregarProyectoModal(Modal):
    """
    Modal para capturar los datos de un nuevo proyecto.
    """
    def __init__(self):
        super().__init__(title="Agregar Proyecto")

        # Título del proyecto
        self.nombre = TextInput(
            label="Título del Proyecto",
            placeholder="Ingrese el título",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.nombre)

        # Link de Ikigai
        self.link = TextInput(
            label="Link de Ikigai",
            placeholder="Ingrese el link de Ikigai",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.link)

        # Sinopsis del proyecto
        self.sinopsis = TextInput(
            label="Sinopsis",
            placeholder="Ingrese una breve sinopsis",
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
            # Referencia a la colección de Firestore
            proyectos_ref = db.collection('servidores').document(server_id).collection('proyectos')
            # Agregar los datos del proyecto
            proyectos_ref.add({
                "titulo": self.nombre.value,
                "link_ikigai": self.link.value,
                "sinopsis": self.sinopsis.value or "Sin sinopsis"
            })

            # Respuesta al usuario
            embed = discord.Embed(
                title="Proyecto Agregado",
                description=f"**Título:** {self.nombre.value}\n**Link:** {self.link.value}\n**Sinopsis:** {self.sinopsis.value or 'Sin sinopsis'}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Responder en caso de error
            embed = discord.Embed(
                title="Error al Agregar Proyecto",
                description=f"Hubo un error al intentar guardar el proyecto: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    """
    Configura el comando /agregarproyecto en el árbol de comandos del bot.
    """
    @app_commands.command(name="agregarproyecto", description="Abre un formulario para agregar un proyecto.")
    async def agregarproyecto(interaction: discord.Interaction):
        """
        Comando slash para mostrar el formulario interactivo.
        """
        modal = AgregarProyectoModal()
        await interaction.response.send_modal(modal)

    bot.tree.add_command(agregarproyecto)
