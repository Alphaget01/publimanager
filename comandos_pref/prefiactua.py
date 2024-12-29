# comandos_pref/prefiactua.py
import discord
from discord.ext import commands
from utils_py.firestore import db
from google.cloud.firestore import DELETE_FIELD
import asyncio
import logging

# Configuración del logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class PrefixedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_config = {}  # Inicializa server_config como un diccionario vacío

    def set_server_config(self, server_id: str, server_name: str):
        """
        Configura los datos del servidor actual.
        """
        self.server_config = {
            "server_id": server_id,
            "server_name": server_name
        }
        logger.info(f"Server configurado: ID={server_id}, Nombre={server_name}")

    # Función para crear embeds
    def create_embed(self, title, description, color=discord.Color.blue()):
        """
        Crea un embed personalizado para mensajes.
        """
        return discord.Embed(title=title, description=description, color=color)
    
    @commands.command(name="ayuda")
    async def ayuda(self, ctx):
        """
        Muestra una lista de comandos disponibles para el bot.
        """
        embed = self.create_embed(
            title="Comandos de Configuración",
            description=(
                "**$manager server <id> <nombre>** - Configura Firestore para el servidor.\n"
                "**$manager canal_publicaciones <ID del canal>** - Configura el canal de publicaciones.\n"
                "**$manager rolesautorizados <IDs de roles>** - Configura roles autorizados.\n"
                "**$manager resetearroles** - Elimina todos los roles autorizados.\n"
                "**$manager rolesetiquetar <IDs de roles>** - Configura roles para publicaciones.\n"
                "**$manager eliminarrolesetiquetar** - Elimina roles configurados para publicaciones.\n"
                "**$manager rolesdona <IDs de roles>** - Configura roles de donadores.\n"
                "**$manager eliminarrolesdona** - Elimina roles configurados como donadores.\n"
                "**$manager actualizar_dominio <nuevo dominio>** - Cambia el dominio en Firestore."
            )
        )
        embed.set_footer(text="Usa estos comandos para configurar tu servidor.")
        await ctx.send(embed=embed)

    @commands.command(name="server")
    async def server(self, ctx, server_id: str, *, server_name: str):
        """
        Configura un servidor y guarda los datos en Firestore.
        """
        try:
            # Llama al método `set_server_config` para guardar la configuración
            self.set_server_config(server_id, server_name)

            # Guarda en Firestore
            collection_name = f"servidores/{server_id}/configugeneral"
            db.collection(collection_name).document("main").set(
                {
                    "server_name": server_name,
                    "idsv_": server_id
                },
                merge=True  # No sobrescribe campos existentes
            )

            embed = self.create_embed(
                title="Servidor Configurado",
                description=f"Servidor configurado correctamente:\n**Nombre:** {server_name}\n**ID:** {server_id}"
            )
        except Exception as e:
            logger.error(f"Error al configurar el servidor: {e}")
            embed = self.create_embed(
                title="Error al Configurar el Servidor",
                description=f"No se pudo configurar el servidor: {str(e)}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name="canal_publicaciones")
    async def canal_publicaciones(self, ctx, canal_id: int):
        """
        Configura el canal donde se harán las publicaciones.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]
            collection_name = f"servidores/{server_id}/configugeneral"
            doc_ref = db.collection(collection_name).document("main")

            # Verificar si el documento ya existe
            doc = doc_ref.get()
            if not doc.exists:
                # Crear el documento si no existe
                doc_ref.set({"id_canalp": canal_id})
                embed = self.create_embed(
                    title="Canal Configurado",
                    description=f"Canal de publicaciones configurado: `{canal_id}` (Nuevo documento creado)."
                )
            else:
                # Actualizar el documento existente
                doc_ref.update({"id_canalp": canal_id})
                embed = self.create_embed(
                    title="Canal Configurado",
                    description=f"Canal de publicaciones configurado: `{canal_id}`."
                )
        except ValueError as ve:
            # Error si el servidor no está configurado
            embed = self.create_embed(
                title="Error",
                description=str(ve),
                color=discord.Color.red()
            )
        except Exception as e:
            # Error genérico al interactuar con Firestore
            embed = self.create_embed(
                title="Error al Configurar el Canal",
                description=f"No se pudo configurar el canal: {str(e)}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name="rolesautorizados")
    async def rolesautorizados(self, ctx, *roles_ids: int):
        """
        Configura roles autorizados para usar comandos.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]

            # Referencia directa al documento en Firestore
            doc_ref = db.collection(f"servidores/{server_id}/configugeneral").document("main")
            
            # Log para depuración
            logger.info(f"Accediendo a Firestore: servidores/{server_id}/configugeneral/main")
            
            # Crear un diccionario con los roles autorizados
            roles_dict = {f"id_role_{i+1}": role_id for i, role_id in enumerate(roles_ids)}

            # Actualizar o crear los roles en el documento Firestore
            doc_ref.update(roles_dict)

            # Log de éxito
            logger.info(f"Roles configurados exitosamente: {roles_dict}")

            # Crear el embed de respuesta
            embed = self.create_embed(
                title="Roles Configurados",
                description=f"Roles autorizados agregados: {', '.join(map(str, roles_ids))}."
            )
        except Exception as e:
            # Log de error
            logger.error(f"Error al configurar roles: {e}")

            # Crear el embed de error
            embed = self.create_embed(
                title="Error al Configurar Roles",
                description=f"No se pudo configurar los roles: {str(e)}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name="resetearroles")
    async def resetearroles(self, ctx):
        """
        Elimina los roles configurados en la base de datos.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]

            # Referencia al documento en Firestore
            doc_ref = db.collection(f"servidores/{server_id}/configugeneral").document("main")

            # Log para depuración
            logger.info(f"Accediendo a Firestore: servidores/{server_id}/configugeneral/main")

            # Solicitar confirmación al usuario
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            # Crear embed de confirmación
            embed = self.create_embed(
                title="Confirmación de Reseteo",
                description="¿Deseas eliminar los roles de autoridad agregados? Escribe `si` o `no` (30 segundos para responder)."
            )
            await ctx.send(embed=embed)

            # Esperar respuesta del usuario
            try:
                msg = await self.bot.wait_for("message", timeout=30.0, check=check)
                if msg.content.lower() == "si":
                    # Obtener datos del documento
                    doc_data = doc_ref.get().to_dict()
                    if not doc_data:
                        raise ValueError("No hay roles configurados para eliminar.")

                    # Crear un diccionario para eliminar todos los roles que empiezan con "id_role_"
                    updates = {key: DELETE_FIELD for key in doc_data.keys() if key.startswith("id_role_")}

                    # Actualizar el documento en Firestore
                    doc_ref.update(updates)

                    # Log de éxito
                    logger.info(f"Roles eliminados: {updates}")

                    # Crear embed de éxito
                    embed = self.create_embed(
                        title="Roles Eliminados",
                        description="Los roles de autoridad han sido eliminados correctamente."
                    )
                else:
                    # Crear embed de operación cancelada
                    embed = self.create_embed(
                        title="Operación Cancelada",
                        description="No se han eliminado los roles."
                    )
            except asyncio.TimeoutError:
                # Crear embed de tiempo excedido
                embed = self.create_embed(
                    title="Tiempo Excedido",
                    description="No respondiste a tiempo, los roles no se han eliminado."
                )
            await ctx.send(embed=embed)

        except ValueError as ve:
            # Error si el servidor no está configurado o no hay roles configurados
            logger.error(f"Error de configuración: {ve}")
            embed = self.create_embed(
                title="Error",
                description=str(ve),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            # Log de error genérico
            logger.error(f"Error al eliminar roles: {e}")
            # Crear embed de error genérico
            embed = self.create_embed(
                title="Error al Eliminar Roles",
                description=f"No se pudo eliminar los roles: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="rolesetiquetar")
    async def rolesetiquetar(self, ctx, *roles_ids: int):
        """
        Configura roles que serán usados para las publicaciones.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]
            doc_ref = db.collection("servidores").document(server_id).collection("configugeneral").document("main")

            # Crear un diccionario con los roles etiquetados
            roles_dict = {f"ide_{i+1}": role_id for i, role_id in enumerate(roles_ids)}
            doc_ref.update(roles_dict)

            # Obtener los nombres de los roles agregados
            role_names = [discord.utils.get(ctx.guild.roles, id=role_id).name for role_id in roles_ids]

            # Log y respuesta
            logger.info(f"Roles etiquetados configurados: {roles_dict}")
            embed = self.create_embed(
                title="Roles Configurados",
                description=f"Roles configurados correctamente:\n**ID(s):** {', '.join(map(str, roles_ids))}\n**Nombre(s):** {', '.join(role_names)}."
            )
        except Exception as e:
            # Log de error y respuesta
            logger.error(f"Error al configurar roles etiquetados: {e}")
            embed = self.create_embed(
                title="Error al Configurar Roles",
                description=f"No se pudo configurar los roles: {str(e)}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name="eliminarrolesetiquetar")
    async def eliminarrolesetiquetar(self, ctx):
        """
        Elimina los roles etiquetados configurados en la base de datos.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]
            doc_ref = db.collection("servidores").document(server_id).collection("configugeneral").document("main")

            # Confirmación al usuario
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            embed = self.create_embed(
                title="Confirmación de Eliminación",
                description="¿Deseas eliminar los roles etiquetados configurados? Escribe `si` o `no` (30 segundos para responder)."
            )
            await ctx.send(embed=embed)

            try:
                msg = await self.bot.wait_for("message", timeout=30.0, check=check)
                if msg.content.lower() == "si":
                    # Obtener datos del documento y preparar eliminación
                    doc_data = doc_ref.get().to_dict()
                    if not doc_data:
                        raise ValueError("No hay roles etiquetados configurados para eliminar.")

                    updates = {key: DELETE_FIELD for key in doc_data.keys() if key.startswith("ide_")}
                    doc_ref.update(updates)

                    # Log y respuesta de éxito
                    logger.info(f"Roles etiquetados eliminados: {updates}")
                    embed = self.create_embed(
                        title="Roles Eliminados",
                        description="Los roles etiquetados han sido eliminados correctamente."
                    )
                else:
                    # Respuesta de cancelación
                    embed = self.create_embed(
                        title="Operación Cancelada",
                        description="No se han eliminado los roles etiquetados. Para la próxima piénsala bien crack."
                    )
            except asyncio.TimeoutError:
                # Respuesta de tiempo excedido
                embed = self.create_embed(
                    title="Tiempo Excedido",
                    description="Care pene no me hagas perder el tiempo."
                )
            await ctx.send(embed=embed)

        except ValueError as ve:
            # Log y respuesta de error de configuración
            logger.error(f"Error de configuración: {ve}")
            embed = self.create_embed(
                title="Error",
                description=str(ve),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            # Log y respuesta de error genérico
            logger.error(f"Error al eliminar roles etiquetados: {e}")
            embed = self.create_embed(
                title="Error al Eliminar Roles",
                description=f"No se pudo eliminar los roles: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="rolesdona")
    async def rolesdona(self, ctx, *roles_ids: int):
        """
        Configura roles de donadores para publicaciones.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]

            # Referencia al documento en Firestore
            doc_ref = db.collection("servidores").document(server_id).collection("configugeneral").document("main")
            
            # Log para depuración
            logger.info(f"Accediendo a Firestore: servidores/{server_id}/configugeneral/main")
            
            # Crear un diccionario con los roles donadores
            roles_dict = {f"ido_{i+1}": role_id for i, role_id in enumerate(roles_ids)}

            # Actualizar o crear los roles en el documento Firestore
            doc_ref.update(roles_dict)

            # Obtener nombres de los roles
            role_names = [ctx.guild.get_role(role_id).name for role_id in roles_ids if ctx.guild.get_role(role_id)]
            role_names_str = ', '.join(role_names)

            # Respuesta de confirmación
            embed = self.create_embed(
                title="Roles Configurados",
                description=f"Los roles se han configurado correctamente.\nIDs de roles: {', '.join(map(str, roles_ids))}\nRoles: {role_names_str}."
            )
        except Exception as e:
            # Log de error
            logger.error(f"Error al configurar roles de donadores: {e}")

            # Embed de error
            embed = self.create_embed(
                title="Error al Configurar Roles",
                description=f"No se pudo realizar la configuración de roles por alguna razón: {str(e)}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name="eliminarrolesdona")
    async def eliminarrolesdona(self, ctx):
        """
        Elimina los roles configurados como donadores.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]

            # Referencia al documento en Firestore
            doc_ref = db.collection("servidores").document(server_id).collection("configugeneral").document("main")
            
            # Log para depuración
            logger.info(f"Accediendo a Firestore: servidores/{server_id}/configugeneral/main")

            # Solicitar confirmación al usuario
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            # Enviar mensaje de confirmación
            embed = self.create_embed(
                title="Confirmación de Eliminación",
                description="¿Deseas eliminar los roles de donadores configurados? Escribe `si` o `no` (30 segundos para responder)."
            )
            await ctx.send(embed=embed)

            try:
                msg = await self.bot.wait_for("message", timeout=30.0, check=check)
                if msg.content.lower() == "si":
                    # Obtener datos del documento
                    doc_data = doc_ref.get().to_dict()
                    if not doc_data:
                        raise ValueError("No hay roles configurados para eliminar.")

                    # Crear un diccionario para eliminar todos los roles que empiezan con "ido_"
                    updates = {key: DELETE_FIELD for key in doc_data.keys() if key.startswith("ido_")}

                    # Actualizar el documento en Firestore
                    doc_ref.update(updates)

                    # Log de éxito
                    logger.info(f"Roles eliminados: {updates}")

                    # Crear embed de éxito
                    embed = self.create_embed(
                        title="Roles Eliminados",
                        description="Los roles de donadores han sido eliminados correctamente."
                    )
                elif msg.content.lower() == "no":
                    # Embed de operación cancelada
                    embed = self.create_embed(
                        title="Operación Cancelada",
                        description="No se han eliminado los roles, para la próxima piénsala bien crack."
                    )
                else:
                    # Embed de respuesta inválida
                    embed = self.create_embed(
                        title="Respuesta Inválida",
                        description="Por favor responde con `si` o `no`."
                    )
            except asyncio.TimeoutError:
                # Embed de tiempo excedido
                embed = self.create_embed(
                    title="Tiempo Excedido",
                    description="Care pene no me hagas perder el tiempo."
                )
        except ValueError as ve:
            # Log de error por configuración faltante
            logger.error(f"Error de configuración: {ve}")

            # Embed de error por configuración faltante
            embed = self.create_embed(
                title="Error",
                description=str(ve),
                color=discord.Color.red()
            )
        except Exception as e:
            # Log de error genérico
            logger.error(f"Error al eliminar roles de donadores: {e}")

            # Embed de error genérico
            embed = self.create_embed(
                title="Error al Eliminar Roles",
                description=f"No se pudieron eliminar los roles de donadores: {str(e)}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name="actualizar_dominio")
    async def actualizar_dominio(self, ctx, nuevo_dominio: str):
        """
        Cambia el dominio en todos los proyectos de la base de datos del servidor actual.
        """
        try:
            # Verificar que el servidor esté configurado
            if not self.server_config:
                raise ValueError("No se ha configurado ningún servidor. Usa `$manager server` primero.")
            
            # Usar el ID del servidor configurado
            server_id = self.server_config["server_id"]
            collection_name = f"servidores/{server_id}/proyectos"

            # Log para depuración
            logger.info(f"Actualizando dominios en la colección: {collection_name}")

            # Obtener todos los documentos en la colección de proyectos
            docs = db.collection(collection_name).stream()
            updated_count = 0  # Contador de proyectos actualizados

            for doc in docs:
                doc_ref = db.collection(collection_name).document(doc.id)
                doc_data = doc.to_dict()

                # Verificar y actualizar el campo "link_ikigai" si existe
                if "link_ikigai" in doc_data:
                    # Reemplazar el dominio completo con el nuevo
                    path_parts = doc_data["link_ikigai"].split("/", 3)  # Dividir por la tercera '/' (dominio)
                    if len(path_parts) > 3:
                        path_suffix = path_parts[3]  # Obtener la parte restante del enlace
                    else:
                        path_suffix = ""  # Por si acaso el enlace no tiene un sufijo
                    
                    # Construir el nuevo enlace
                    new_link = f"{nuevo_dominio.rstrip('/')}/{path_suffix}"
                    doc_ref.update({"link_ikigai": new_link})
                    updated_count += 1  # Incrementar contador de actualizaciones

                    # Log de cada proyecto actualizado
                    logger.info(f"Documento actualizado: {doc.id}, Nuevo link: {new_link}")

            # Crear respuesta
            embed = self.create_embed(
                title="Dominio Actualizado",
                description=f"El dominio ha sido actualizado a `{nuevo_dominio}` en {updated_count} proyectos."
            )
        except ValueError as ve:
            # Error si el servidor no está configurado
            logger.error(f"Error de configuración: {ve}")
            embed = self.create_embed(
                title="Error",
                description=str(ve),
                color=discord.Color.red()
            )
        except Exception as e:
            # Error genérico al interactuar con Firestore
            logger.error(f"Error al actualizar dominios: {e}")
            embed = self.create_embed(
                title="Error al Actualizar Dominio",
                description=f"No se pudo actualizar el dominio: {str(e)}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)


async def setup(bot):
    cog = PrefixedCommands(bot)
    await bot.add_cog(cog)
    print(f"Cog {cog.__class__.__name__} cargado correctamente.")

    # Verificar registro de comandos
    registered_commands = [command.name for command in bot.commands]
    print(f"Comandos registrados: {registered_commands}")
