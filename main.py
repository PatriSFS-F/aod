import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import os
import random
import logging
import webserver
from datetime import datetime

# Configuração do logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord')
TOKEN = os.environ.get('discordkey')

# Define os IDs personalizados para os componentes
MEDAL_SELECT_ID = "medal_select"
NAME_SELECT_ID = "name_select"
SUBMIT_BUTTON_ID = "submit_button"

# Criar uma instância de Intents
intents = discord.Intents.default()
intents.messages = True  
intents.message_content = True  
intents.guilds = True  
intents.dm_messages = True  

# Define o prefixo do comando e passa os intents
bot = commands.Bot(command_prefix='$', intents=intents)

TARGET_TIME = datetime(2024, 8, 23, 23, 0, 0)
ALLOWED_GUILD_ID = 1261355808940363827
TARGET_CHANNEL_ID = 1276669341714087999 
AUTHORIZED_USERS = [757934740308361247, 351140224140574720, 583098488535908352]
MEDALS = [
    "Peacekeeper",
    "Unholy",
    "Iron Fist",
    "Main Prospect",
    "Blood Oath",
    "Bullseye",
    "Outlaw Sheriff",
    "Brother's Keeper",
    "Tail Gunner",
    "Ride or Die",
    "Cold Blood",
]
NAMES = ["Deamon Cooper", "Bianca Fletcher Cooper", "Elijah Fletcher", "Dylan Carter","Ethan Oliver","Faskur Montague","Alice Hargreaves","Edgar Santana","Ezekiel Goldwyn", "Philip Mathers","Harry Stephan","James Cooper","Miles Jones","Oliver Morgan","Petzold","Benny Cooper","jessica miller","Mila Cooper", "Phil Goldwyn"]

TICKET_CHANNEL_ID = 1276536612787851378 # canal para enviar o comando
ALLOWED_ROLE_ID = 1266152353686487082 # Conselho
LOG_CHANNEL_ID = 1276538920703758428 # canal de logsG
class TicketButton(Button):
    def __init__(self):
        super().__init__(label="Indicar", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        allowed_role = guild.get_role(ALLOWED_ROLE_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            allowed_role: discord.PermissionOverwrite(view_channel=True)
        }

        try:
            ticket_channel = await guild.create_text_channel(name=f'ticket-{interaction.user.name}', overwrites=overwrites)
            logger.info(f'Canal de ticket criado: {ticket_channel.name} (ID: {ticket_channel.id})')
            await ticket_channel.send(f'{interaction.user.mention}, selecione a medalha e o nome que deseja indicar.', view=MedalNameDropdownView())
            await interaction.response.send_message(f'Ticket criado: {ticket_channel.mention}', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("Ocorreu um erro ao criar o ticket.", ephemeral=True)
            logger.error(f'Erro ao criar canal de ticket: {str(e)}')
class TicketView(View):
    def __init__(self, timeout=86400): 
        super().__init__(timeout=timeout)
        self.add_item(TicketButton())


@bot.event
async def on_guild_join(guild):
    if guild.id != ALLOWED_GUILD_ID:
        await guild.leave()  # Faz o bot sair de outros servidores
        logger.info(f'Saiu do servidor não autorizado: {guild.name} (ID: {guild.id})')

@bot.event
async def on_ready():
    logger.info(f'Bot {bot.user} está online!')
    logger.info('Aguardando comandos...')

    # Envie a View com o botão para um canal específico (ao iniciar o bot)
    channel = bot.get_channel(TICKET_CHANNEL_ID)  # Canal onde o botão será enviado
    if channel:
        await channel.send("Clique no botão abaixo para abrir uma indicação.", view=TicketView())


@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        if target_channel:
            await target_channel.send(f"{message.content}")
            logger.info(f'Redirecionou mensagem privada de {message.author} para o canal {target_channel.name}.')
        else:
            logger.error(f'Canal com ID {TARGET_CHANNEL_ID} não encontrado.')
    
    # Permite que outros comandos sejam processados
    await bot.process_commands(message)

# Dicionário global para armazenar as seleções dos usuários
user_selections = {}

class MedalNameDropdownView(View):
    def __init__(self):
        super().__init__()
        self.add_item(MedalSelect())
        self.add_item(NameSelect())
        self.add_item(SubmitButton())

class MedalSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=medal) for medal in MEDALS]
        super().__init__(placeholder='Escolha uma medalha...', min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_selections[user_id] = {'medal': self.values[0]}
        await interaction.response.send_message(f'{self.values[0]}', ephemeral=True)

class NameSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=name) for name in NAMES]
        super().__init__(placeholder='Escolha um nome...', min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in user_selections:
            user_selections[user_id]['name'] = self.values[0]
        else:
            user_selections[user_id] = {'name': self.values[0]}
        await interaction.response.send_message(f'{self.values[0]}', ephemeral=True)

class SubmitButton(Button):
    def __init__(self):
        super().__init__(label='Enviar', style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in user_selections:
            selections = user_selections[user_id]
            medal = selections.get('medal')
            name = selections.get('name')
            custom_message = selections.get('custom_message', 'Nenhuma mensagem personalizada.')
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f'{interaction.user.mention} indicou {name} para a medalha {medal} com a mensagem: "{custom_message}"')
                await interaction.response.send_message(f'Ticket enviado para {log_channel.mention} escreva em poucas palavras os motivos da sua escolha, envie fotos e videos caso ache necessário', ephemeral=True)
            else:
                await interaction.response.send_message("Canal de logs não encontrado.", ephemeral=True)
        else:
            await interaction.response.send_message("Nenhuma seleção encontrada.", ephemeral=True)

@bot.command(name='ticket')
async def open_ticket(ctx):
    if ctx.channel.id != TICKET_CHANNEL_ID:
        await ctx.send("Este comando deve ser usado no canal de tickets.")
        return

    guild = ctx.guild
    allowed_role = guild.get_role(ALLOWED_ROLE_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True),
        allowed_role: discord.PermissionOverwrite(view_channel=True)
    }

    try:
        ticket_channel = await guild.create_text_channel(name=f'ticket-{ctx.author.name}', overwrites=overwrites)
        logger.info(f'Canal de ticket criado: {ticket_channel.name} (ID: {ticket_channel.id})')
        await ticket_channel.send(f'{ctx.author.mention}, selecione a medalha e o nome que deseja indicar.', view=MedalNameDropdownView())
        logger.info(f'Mensagem enviada para o canal de ticket: {ticket_channel.name}')
    except Exception as e:
        await ctx.send("Ocorreu um erro ao criar o ticket.")
        logger.error(f'Erro ao criar canal de ticket: {str(e)}')
        
@bot.command(name='suco')
async def play(ctx, filename='arquivo'):
    if not ctx.author.voice:
        await ctx.send("Você precisa estar em um canal de voz para usar este comando.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()

    if ctx.voice_client.is_playing():
        await ctx.send('Já estou tocando uma música!')
        return

    audio_file = f'{filename}.mp3'
    if not os.path.isfile(audio_file):
        await ctx.send(f'O arquivo {audio_file} não foi encontrado.')
        return

    audio_source = discord.FFmpegPCMAudio(audio_file)
    ctx.voice_client.play(audio_source, after=lambda e: logger.info(f'Player error: {e}') if e else None)
    await ctx.send(f'Reproduzindo: {filename}.mp3')

@bot.command(name='dados')
async def roll_d100(ctx):
    roll = random.randint(1, 100)
    await ctx.send(f'🎲 Você rolou: {roll}')

@bot.command(name='fechar')
async def fechar(ctx):
    user_id = ctx.author.id

    # Verifica se o usuário é autorizado
    if user_id not in AUTHORIZED_USERS:
        await ctx.send("Você não tem permissão para usar este comando.")
        logger.warning(f"Usuário não autorizado: {ctx.author} (ID: {user_id}) tentou usar o comando fechar.")
        return

    # Verifica se o canal foi criado para um ticket
    if ctx.channel.name.startswith("ticket-"):
        try:
            await ctx.channel.delete()
            logger.info(f'Canal de ticket {ctx.channel.name} foi fechado por {ctx.author}.')
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para excluir este canal.")
            logger.error(f'Permissão insuficiente para excluir o canal {ctx.channel.name}.')
        except discord.HTTPException as e:
            await ctx.send(f"Ocorreu um erro ao tentar excluir o canal: {str(e)}")
            logger.error(f'Erro ao tentar excluir o canal {ctx.channel.name}: {str(e)}')
    else:
        await ctx.send("Este comando só pode ser usado em canais de ticket.")


@bot.command(name='limpar')
async def clear(ctx, amount: int):
    user_id = ctx.author.id

    if user_id not in AUTHORIZED_USERS:
        await ctx.send("Você não tem permissão para usar este comando.")
        logger.warning(f"Usuário não autorizado: {ctx.author} (ID: {user_id}) tentou usar o comando limpar.")
        return

    # Se o usuário estiver autorizado, prossegue com a limpeza
    logger.info(f'Comando limpar foi chamado por {ctx.author} ({user_id}) para apagar {amount} mensagens')
    try:
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f'{len(deleted)} mensagens apagadas!', delete_after=5)
    except discord.Forbidden:
        await ctx.send('Eu não tenho permissões suficientes para apagar mensagens aqui.', delete_after=5)
        logger.error('Permissão insuficiente para apagar mensagens.')
    except discord.HTTPException as e:
        await ctx.send(f'Ocorreu um erro ao tentar apagar as mensagens: {str(e)}', delete_after=5)
        logger.error(f'Erro ao tentar apagar mensagens: {str(e)}')
    except Exception as e:
        await ctx.send(f'Ocorreu um erro inesperado: {str(e)}', delete_after=5)
        logger.error(f'Erro inesperado: {str(e)}')

@bot.command(name='angels')
async def angels(ctx):
    logger.info('Comando angels foi chamado.')
    await ctx.send('Angels Forever, Forever Angels!')

@bot.command(name='comandos')
async def comandos(ctx):
    await ctx.send('meus comandos: $tempo, $angels, $limpar, $vavazinho, $comandos, $james, $suco')

@bot.command(name='vavazinho')
async def vavazinho(ctx):
    await ctx.send('Boar um vavazinho? colem Call!')

@bot.command(name='tempo')
async def tempo(ctx):
    now = datetime.now()
    remaining_time = TARGET_TIME - now

    if remaining_time.total_seconds() > 0:
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        countdown_message = (f" {hours} horas, {minutes} minutos e {seconds} segundos")
    else:
        countdown_message = "<@&1269533248875266080> A contagem regressiva terminou!"

    await ctx.send(countdown_message)

webserver.keep_alive()
bot.run(TOKEN)

