import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import aiosqlite
import datetime
import asyncio  # Necessário para usar asyncio.TimeoutError
from collections import defaultdict
import sqlite3
import datetime
import random

# Configurações do bot
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True  # Necessário para ler mensagens
intents.guilds = True  # Necessário para interações com servidores
intents.members = True  # Necessário para interações com membros do servidor

bot = commands.Bot(command_prefix='!', intents=intents)

# Banco de dados
DB_NAME = 'economia.db'

# Função para inicializar o banco de dados
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                saldo INTEGER NOT NULL,
                last_daily DATETIME
            )
        ''')
        await db.commit()

# Função para garantir que o usuário existe no banco de dados
async def garantir_usuario(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)) as cursor:
            user = await cursor.fetchone()
            if user is None:
                await db.execute('INSERT INTO usuarios (id, saldo, last_daily) VALUES (?, ?, ?)', (user_id, 0, None))
                await db.commit()

# Função para obter saldo do usuário
async def get_saldo(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT saldo FROM usuarios WHERE id = ?', (user_id,)) as cursor:
            saldo = await cursor.fetchone()
            return saldo[0] if saldo else 0

# Função para atualizar saldo do usuário
async def update_saldo(user_id, novo_saldo):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE usuarios SET saldo = ? WHERE id = ?', (novo_saldo, user_id))
        await db.commit()

# Função para obter a última vez que o usuário fez daily
async def get_last_daily(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT last_daily FROM usuarios WHERE id = ?', (user_id,)) as cursor:
            last_daily = await cursor.fetchone()
            return last_daily[0] if last_daily else None

# Função para atualizar a última vez que o usuário fez daily
async def update_last_daily(user_id, timestamp):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE usuarios SET last_daily = ? WHERE id = ?', (timestamp, user_id))
        await db.commit()

# Função para adicionar a coluna last_daily, se não existir
async def adicionar_coluna_last_daily():
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("ALTER TABLE usuarios ADD COLUMN last_daily DATETIME")
            await db.commit()
        except aiosqlite.Error:
            # Ignorar o erro se a coluna já existir
            pass

# Comando para Kick
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} Esqueceu que aqui **não** era anarquia! E foi expulso pelo *MOTIVO* {reason}')

# Tratamento de erro para falta de permissão
@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para expulsar membros!")
        
# Comando para adicionar PP COIN
@bot.command(name='adicionar')
async def adicionar(ctx, valor: int):
    if ctx.author.id != 779913122655240222:
        await ctx.send("Você não tem permissão para usar este comando!. So MEU DONO TEM!")
        return

    await garantir_usuario(ctx.author.id)
    saldo_atual = await get_saldo(ctx.author.id)
    novo_saldo = saldo_atual + valor
    await update_saldo(ctx.author.id, novo_saldo)
    await ctx.send(f"{ctx.author.name}, você adicionou {valor} Fox COIN(s). Seu saldo atual é de {novo_saldo} Fox COIN(s).")
    
# Comando para Ban
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} foi banido por fazer caquinhas, siga o exemplo *DELE* só que ao contrário... MOTIVO: {reason}')

# Tratamento de erro para falta de permissão
@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para banir membros!")

# Comando para verificar saldo
@bot.command(name='saldo')
async def saldo(ctx):
    await garantir_usuario(ctx.author.id)
    saldo = await get_saldo(ctx.author.id)
    posicao = await ranking_position(ctx.author.id)

    if saldo < 5000:
        status = f"💰 Você está POBRE! 💰\n\nVocê tem um saldo de **{saldo}** PP COIN(s), e está infelizmente na **{posicao}**ª posição no ranking dos mais poderosos! 😔\n\nSe quiser ver quem está no topo do pódio dos ostentadores, use !ranking e veja se alguém ousa competir com você!"
    elif 5000 <= saldo < 100000:
        status = f"💰 Você está RICÃO! 💰\n\nVocê tem um saldo de **{saldo}** PP COIN(s), e está brilhando na **{posicao}**ª posição no ranking dos mais poderosos! ⚡\n\nSe quiser ver quem está no topo do pódio dos ostentadores, use !ranking e veja se alguém ousa competir com você!"
    else:
        status = f"💰 Você está MILIONÁRIO(a)! 💰\n\nVocê tem um saldo de **{saldo}** PP COIN(s), e está brilhando na **{posicao}**ª posição no ranking dos mais poderosos! ⚡\n\nSe quiser ver quem está no topo do pódio dos ostentadores, use !ranking e veja se alguém ousa competir com você!"

    await ctx.send(f"{ctx.author.name}, {status}")

# Comando para Unban
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = [entry async for entry in ctx.guild.bans()]  # Obtem a lista de banidos

    for ban_entry in banned_users:
        user = ban_entry.user
        if user.name.lower() == member_name.lower():  # Compara os nomes ignorando maiúsculas/minúsculas
            await ctx.guild.unban(user)
            await ctx.send(f'Olha quem DECIDIU VOLTAR NÉ {user.mention}? Volte com cuidados, viu! Você foi desbanido.')
            return

    await ctx.send(f'Não tem nenhum {member_name} na lista de BANIDOS!')

# Tratamento de erro para falta de permissão
@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para desbanir membros!")

# Função para obter a posição do usuário no ranking
async def ranking_position(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM usuarios WHERE saldo > (SELECT saldo FROM usuarios WHERE id = ?)', (user_id,)) as cursor:
            posicao = await cursor.fetchone()
            return posicao[0] + 1  # +1 porque a contagem é zero-indexed

@bot.command(name='apostar')  # ou name='apostar' se preferir
async def apostar(ctx, valor: int):
    await garantir_usuario(ctx.author.id)
    saldo = await get_saldo(ctx.author.id)

    if saldo >= valor:
        resultado = random.choice(['cara', 'coroa'])
        await ctx.send(f"{ctx.author.name}, você apostou {valor} PP COIN(s). Resultado: {resultado}.")
        if resultado == 'cara':
            novo_saldo = saldo + valor
            await update_saldo(ctx.author.id, novo_saldo)
            await ctx.send(f"Você ganhou! Seu saldo agora é de {novo_saldo} PP COIN(s).")
        else:
            novo_saldo = saldo - valor
            await update_saldo(ctx.author.id, novo_saldo)
            await ctx.send(f"Você perdeu! Seu saldo agora é de {novo_saldo} PP COIN(s).")
    else:
        await ctx.send(f"{ctx.author.name}, você não tem saldo suficiente para apostar {valor} PP COIN(s)!")


# Comando para pagar a outro usuário
@bot.command(name='pay')
async def pay(ctx, membro: discord.Member, valor: int):
    await garantir_usuario(ctx.author.id)
    await garantir_usuario(membro.id)

    saldo_remetente = await get_saldo(ctx.author.id)

    if saldo_remetente >= valor:
        # Mensagem de confirmação
        confirm_msg = await ctx.send(
            f"{ctx.author.mention} Você está prestes a transferir {valor} PP COIN(s) para {membro.mention}!\n"
            "Para confirmar a transação, você e {membro.mention} devem clicar em ✅!\n"
            "🔔 Não se esqueça: É proibido o comércio de produtos que possuem valores reais (Nitro, dinheiro real, invites, conteúdo ilegal/NSFW, etc.) por PP COIN e venda de PP COIN por dinheiro real. Caso faça isso, você será banido de usar o bot!\n"
            "💡 Ao aceitar a transação, você não conseguirá pedir os PP COIN de volta, e a equipe não irá ajudar a recuperá-los. Portanto, envie PP COIN apenas para pessoas confiáveis!\n"
            "⚠️ Lembre-se: Emprestar PP COIN é como emprestar seu carregador: é provável que você nunca o veja novamente! Ser agiota é feio!"
        )

        await confirm_msg.add_reaction("✅")

        def check(reaction, user):
            return user in [ctx.author, membro] and str(reaction.emoji) == "✅" and reaction.message.id == confirm_msg.id

        try:
            # Espera pela reação de ambos os usuários
            await bot.wait_for('reaction_add', timeout=900.0, check=check)
            await bot.wait_for('reaction_add', timeout=900.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("A transação foi cancelada.")
            return

        # Transfere os valores após a confirmação de ambos
        await update_saldo(ctx.author.id, saldo_remetente - valor)
        saldo_destinatario = await get_saldo(membro.id)
        await update_saldo(membro.id, saldo_destinatario + valor)

        await ctx.send(f"{ctx.author.name} transferiu {valor} PP COIN(s) para {membro.mention}! Seu novo saldo é {saldo_remetente - valor} PP COIN(s).")
    else:
        await ctx.send(f"{ctx.author.name}, você não tem saldo suficiente para transferir {valor} PP COIN(s)!")

# Comando para Clear (limpar mensagens)
@bot.command()
@commands.has_permissions(manage_guild=True)  # Permissão de Gerenciar Servidor
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f'{amount} mensagens foram deletadas.', delete_after=5)

# Tratamento de erro para falta de permissão
@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para limpar mensagens neste servidor!")

# Comando para ver o ranking
@bot.command(name='ranking')
async def ranking(ctx):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT id, saldo FROM usuarios ORDER BY saldo DESC') as cursor:
            rank = await cursor.fetchall()

    ranking_msg = "🏆 **Ranking dos Ostentadores** 🏆\n\n"
    for posicao, (user_id, saldo) in enumerate(rank, start=1):
        user = await bot.fetch_user(user_id)
        ranking_msg += f"{posicao} - {user.name}: {saldo} PP COIN(s)\n"

    await ctx.send(ranking_msg)

# Comando para Info (informações do usuário)
@bot.command()
async def info(ctx, member: discord.Member):
    embed = discord.Embed(title="Informações do Usuário", color=discord.Color.blue())
    embed.add_field(name="Nome de Usuário", value=str(member), inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Entrou no Servidor em", value=member.joined_at.strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    embed.add_field(name="Conta Criada em", value=member.created_at.strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    await ctx.send(embed=embed)

# Comando para coletar recompensa diária
@bot.command(name='daily')
async def daily(ctx):
    await garantir_usuario(ctx.author.id)  # Verifica se o usuário está registrado

    # Verifica a última vez que o usuário fez daily
    last_daily = await get_last_daily(ctx.author.id)
    now = datetime.datetime.now()

    if last_daily is None or (now - datetime.datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S.%f')).days > 0:
        recompensa = random.randint(300, 5000)  # Recompensa aleatória entre 300 e 5000
        novo_saldo = await get_saldo(ctx.author.id) + recompensa

        await update_saldo(ctx.author.id, novo_saldo)
        await update_last_daily(ctx.author.id, now)

        await ctx.send(f"{ctx.author.name}, você recebeu sua daily de {recompensa} PP COIN(s)! Seu novo saldo é {novo_saldo} PP COIN(s).")
    else:
        # Calcula a próxima disponibilidade da daily
        next_daily_time = datetime.datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S.%f') + datetime.timedelta(days=1)
        next_daily_formatted = next_daily_time.strftime("%H:%M")  # Formata a hora para HH:MM
        await ctx.send(f"{ctx.author.name}, você já retirou sua daily hoje. Tente novamente às {next_daily_formatted}! ( faça o HH -3 )")


# Dicionário para armazenar o saldo dos usuários
user_balances = {}

# Lista de questões de trivia
trivia_questions = [
    {
        "question": "Qual é a capital do Brasil?",
        "options": ["A) Brasília", "B) Rio de Janeiro", "C) São Paulo", "D) Salvador"],
        "answer": "A"
    },
    {
        "question": "Qual é a maior floresta do mundo?",
        "options": ["A) Floresta Amazônica", "B) Floresta do Congo", "C) Taiga", "D) Floresta Boreal"],
        "answer": "A"
    },
    {
        "question": "Qual é o maior planeta do sistema solar?",
        "options": ["A) Marte", "B) Terra", "C) Júpiter", "D) Saturno"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital da França?",
        "options": ["A) Paris", "B) Londres", "C) Roma", "D) Madri"],
        "answer": "A"
    },
    {
        "question": "Quem pintou a Mona Lisa?",
        "options": ["A) Van Gogh", "B) Picasso", "C) Leonardo da Vinci", "D) Michelangelo"],
        "answer": "C"
    },
    {
        "question": "Qual é o símbolo químico da água?",
        "options": ["A) O2", "B) H2O", "C) CO2", "D) H2"],
        "answer": "B"
    },
    {
        "question": "Qual é a capital da Itália?",
        "options": ["A) Milão", "B) Roma", "C) Veneza", "D) Nápoles"],
        "answer": "B"
    },
    {
        "question": "Qual é a montanha mais alta do mundo?",
        "options": ["A) K2", "B) Monte Everest", "C) Monte Kilimanjaro", "D) Monte McKinley"],
        "answer": "B"
    },
    {
        "question": "Qual é a capital do Japão?",
        "options": ["A) Tóquio", "B) Osaka", "C) Quioto", "D) Hiroshima"],
        "answer": "A"
    },
    {
        "question": "Qual é o continente onde se encontra o deserto do Saara?",
        "options": ["A) América do Sul", "B) Ásia", "C) Europa", "D) África"],
        "answer": "D"
    },
    {
        "question": "Qual é a primeira letra do alfabeto grego?",
        "options": ["A) Beta", "B) Alfa", "C) Gama", "D) Delta"],
        "answer": "B"
    },
    {
        "question": "Qual é a cor do sangue humano?",
        "options": ["A) Azul", "B) Verde", "C) Vermelho", "D) Amarelo"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital da Finlândia?",
        "options": ["A) Estocolmo", "B) Helsinque", "C) Oslo", "D) Copenhague"],
        "answer": "B"
    },
    {
        "question": "Qual é a maior cidade da Austrália?",
        "options": ["A) Sydney", "B) Melbourne", "C) Brisbane", "D) Perth"],
        "answer": "A"
    },
    {
        "question": "Qual é o planeta mais distante do Sol?",
        "options": ["A) Marte", "B) Netuno", "C) Urano", "D) Plutão"],
        "answer": "B"
    },
    {
        "question": "Qual é o principal ingrediente do guacamole?",
        "options": ["A) Tomate", "B) Cebola", "C) Abacate", "D) Pimentão"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital da Nova Zelândia?",
        "options": ["A) Auckland", "B) Wellington", "C) Christchurch", "D) Dunedin"],
        "answer": "B"
    },
    {
        "question": "Qual é o nome da maior estrutura viva do mundo?",
        "options": ["A) Grande Barreira de Corais", "B) Floresta Amazônica", "C) Monte Everest", "D) Deserto do Saara"],
        "answer": "A"
    },
    {
        "question": "Qual é o sistema de governo da Grécia?",
        "options": ["A) Monarquia", "B) Ditadura", "C) Democracia", "D) Oligarquia"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital da Croácia?",
        "options": ["A) Split", "B) Dubrovnik", "C) Zagreb", "D) Rijeka"],
        "answer": "C"
    },
    {
        "question": "Qual é o maior continente do mundo?",
        "options": ["A) América do Sul", "B) África", "C) Europa", "D) Ásia"],
        "answer": "D"
    },
    {
        "question": "Qual é a capital do Chile?",
        "options": ["A) Santiago", "B) Valparaíso", "C) Concepción", "D) Antofagasta"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da Áustria?",
        "options": ["A) Viena", "B) Salzburgo", "C) Innsbruck", "D) Graz"],
        "answer": "A"
    },
    {
        "question": "Qual é o planeta mais próximo do Sol?",
        "options": ["A) Vênus", "B) Mercúrio", "C) Terra", "D) Marte"],
        "answer": "B"
    },
    {
        "question": "Qual é a capital do México?",
        "options": ["A) Cancún", "B) Guadalajara", "C) Cidade do México", "D) Monterrey"],
        "answer": "C"
    },
    {
        "question": "Qual é o nome do famoso cientista que desenvolveu a teoria da relatividade?",
        "options": ["A) Isaac Newton", "B) Albert Einstein", "C) Nikola Tesla", "D) Stephen Hawking"],
        "answer": "B"
    },
    {
        "question": "Qual é o continente que possui o maior número de países?",
        "options": ["A) Ásia", "B) África", "C) Europa", "D) América do Sul"],
        "answer": "B"
    },
    {
        "question": "Qual é a capital do Marrocos?",
        "options": ["A) Casablanca", "B) Rabat", "C) Marrakech", "D) Fes"],
        "answer": "B"
    },
    {
        "question": "Qual é a unidade de medida da força?",
        "options": ["A) Newton", "B) Joule", "C) Pascal", "D) Watt"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da Grécia?",
        "options": ["A) Atenas", "B) Tessalônica", "C) Heraklion", "D) Patras"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da Turquia?",
        "options": ["A) Istambul", "B) Ancara", "C) Izmir", "D) Bursa"],
        "answer": "B"
    },
    {
        "question": "Qual é a forma de governo da China?",
        "options": ["A) Monarquia", "B) Ditadura", "C) Democracia", "D) República"],
        "answer": "B"
    },
    {
        "question": "Qual é o elemento químico com o símbolo 'H'?",
        "options": ["A) Hidrogênio", "B) Hélio", "C) Mercúrio", "D) Cádmio"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da Espanha?",
        "options": ["A) Barcelona", "B) Madri", "C) Valência", "D) Sevilha"],
        "answer": "B"
    },
    {
        "question": "Qual é a capital da Rússia?",
        "options": ["A) Moscovo", "B) São Petersburgo", "C) Novosibirsk", "D) Yekaterinburg"],
        "answer": "A"
    },
    {
        "question": "Qual é o nome da invenção que permitiu a impressão em massa?",
        "options": ["A) Impressora 3D", "B) Máquina de escrever", "C) Prensa de Gutenberg", "D) Computador"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital da Irlanda?",
        "options": ["A) Dublin", "B) Belfast", "C) Cork", "D) Galway"],
        "answer": "A"
    },
    {
        "question": "Qual é o país conhecido como a terra dos leões?",
        "options": ["A) Índia", "B) África do Sul", "C) Sri Lanka", "D) Brasil"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital da Suécia?",
        "options": ["A) Gotemburgo", "B) Estocolmo", "C) Malmö", "D) Uppsala"],
        "answer": "B"
    },
    {
        "question": "Qual é a capital da Noruega?",
        "options": ["A) Oslo", "B) Estocolmo", "C) Copenhague", "D) Helsinque"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da Índia?",
        "options": ["A) Nova Délhi", "B) Bombaim", "C) Calcutá", "D) Chennai"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da Bélgica?",
        "options": ["A) Bruxelas", "B) Antuérpia", "C) Liège", "D) Gante"],
        "answer": "A"
    },
    {
        "question": "Qual é o maior oceano do mundo?",
        "options": ["A) Oceano Atlântico", "B) Oceano Índico", "C) Oceano Ártico", "D) Oceano Pacífico"],
        "answer": "D"
    },
    {
        "question": "Qual é a capital da Dinamarca?",
        "options": ["A) Copenhague", "B) Aarhus", "C) Odense", "D) Aalborg"],
        "answer": "A"
    },
    {
        "question": "Qual é a forma de governo da Alemanha?",
        "options": ["A) Monarquia", "B) Ditadura", "C) República", "D) Oligarquia"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital da Coreia do Sul?",
        "options": ["A) Seul", "B) Busan", "C) Incheon", "D) Gwangju"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da França?",
        "options": ["A) Paris", "B) Marselha", "C) Lyon", "D) Nice"],
        "answer": "A"
    },
    {
        "question": "Qual é a capital da Suíça?",
        "options": ["A) Genebra", "B) Zurique", "C) Berna", "D) Lucerna"],
        "answer": "C"
    },
    {
        "question": "Qual é a capital do Egito?",
        "options": ["A) Cairo", "B) Alexandria", "C) Luxor", "D) Aswan"],
        "answer": "A"
    },

]

# Função para obter o saldo do usuário
async def get_user_balance(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT saldo FROM usuarios WHERE id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

# Função para atualizar o saldo do usuário
async def update_user_balance(user_id, new_balance):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE usuarios SET saldo = ? WHERE id = ?', (new_balance, user_id))
        await db.commit()

# Comando de trivia
@bot.command()
async def trivia(ctx):
    await ctx.send(f"|{ctx.author.mention} tanana Trivia Da PP!\n"
                   f"| Ganhe Fox COINs acertando as QUESTÕES!\n"
                   f"| Ao digitar o comando **!trivia_comprar** você perderá 200 Fox COINs, "
                   f"mas se acertar a questão você ganhará 300 Fox COINs. para jogar novamente, use o comando !trivia_comprar novamente!")

# Comando para comprar uma pergunta de trivia
@bot.command(name="trivia_comprar")
async def trivia_comprar(ctx):
    user_id = ctx.author.id
    balance = await get_user_balance(user_id)  # Obter saldo do banco de dados

    if balance < 500:
        await ctx.send(f"{ctx.author.mention} você não tem Fox COINs suficientes para comprar uma pergunta.")
        return

    new_balance = balance - 200  # Deduz 500 PP COINs
    await update_user_balance(user_id, new_balance)  # Atualiza o saldo no banco de dados

    question = random.choice(trivia_questions)  # Seleciona uma pergunta aleatória
    options = "\n".join(question["options"])  # Formata as opções
    await ctx.send(f"{ctx.author.mention} aqui está a sua questão! Acerte ela e ganhe 300 Fox COINs!!\n"
                   f"**{question['question']}**\n{options}")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        answer_msg = await bot.wait_for('message', check=check, timeout=10)
        if answer_msg.content.upper() == question["answer"]:
            new_balance += 300  # Adiciona 1000 PP COINs
            await update_user_balance(user_id, new_balance)  # Atualiza o saldo no banco de dados
            await ctx.send(f"{ctx.author.mention} Parabéns! Você acertou! Agora você tem {new_balance} Fox COINs.")
        else:
            await ctx.send(f"{ctx.author.mention} Você errou! A resposta correta era {question['answer']}. "
                           f"Você ainda tem {new_balance} Fox COINs.")
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention} Tempo esgotado! A resposta correta era {question['answer']}.")

afk_users = {}  # Dicionário para armazenar usuários AFK

@bot.command()
async def afk(ctx, *, motivo: str = "Nenhum motivo fornecido."):
    """Define o usuário como AFK com um motivo opcional."""
    user_id = ctx.author.id
    afk_users[user_id] = motivo
    await ctx.send(f"{ctx.author.mention} está agora AFK: {motivo}")

@bot.event
async def on_message(message):
    """Remove o status AFK quando o usuário envia uma mensagem."""
    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"{message.author.mention} já não está mais AFK.")

    await bot.process_commands(message)

@bot.event
async def on_member_update(before, after):
    """Exibe um aviso quando alguém muda para AFK."""
    if after.status == discord.Status.idle and after.id in afk_users:
        afk_motivo = afk_users[after.id]
        await after.send(f"Você está AFK: {afk_motivo}")

@commands.has_permissions(manage_guild=True)
@bot.command()
async def lock(ctx):
    """Bloqueia o canal, impedindo que usuários sem a permissão 'Gerenciar Servidor' enviem mensagens."""

    # Tenta obter a sobreposição de permissões para o papel padrão
    default_overwrite = ctx.channel.overwrites.get(ctx.guild.default_role)

    # Se não existir, inicialize como uma nova sobreposição com permissões padrão
    if default_overwrite is None:
        default_overwrite = discord.PermissionOverwrite(send_messages=True)  # Permissão padrão
        ctx.channel.overwrites[ctx.guild.default_role] = default_overwrite

    # Verifica se o canal já está bloqueado
    if default_overwrite.send_messages is False:
        await ctx.send("O canal já está bloqueado!")
        return

    # Adiciona permissões de bloqueio
    overwrites = ctx.channel.overwrites
    overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(send_messages=False)

    # Permitir que os cargos com 'Gerenciar Servidor' possam enviar mensagens
    for role in ctx.guild.roles:
        if role.permissions.manage_guild:
            overwrites[role] = discord.PermissionOverwrite(send_messages=True)

    await ctx.channel.edit(overwrites=overwrites)
    await ctx.send("🔒┃ O canal foi trancado! Somente a equipe de moderação pode falar aqui agora. Vamos manter a ordem!🚫")

@commands.has_permissions(manage_guild=True)
@bot.command()
async def unlock(ctx):
    """Desbloqueia o canal, permitindo que todos enviem mensagens."""

    # Tenta obter a sobreposição de permissões para o papel padrão
    default_overwrite = ctx.channel.overwrites.get(ctx.guild.default_role)

    # Se não existir, inicialize como uma nova sobreposição com permissões padrão
    if default_overwrite is None:
        default_overwrite = discord.PermissionOverwrite(send_messages=True)  # Permissão padrão
        ctx.channel.overwrites[ctx.guild.default_role] = default_overwrite

    # Verifica se o canal já está desbloqueado
    if default_overwrite.send_messages is True:
        await ctx.send("O canal já está desbloqueado!")
        return

    # Adiciona permissões de desbloqueio
    overwrites = ctx.channel.overwrites
    overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(send_messages=True)

    for role in ctx.guild.roles:
        if role.permissions.manage_guild:
            overwrites[role] = discord.PermissionOverwrite(send_messages=True)

    await ctx.channel.edit(overwrites=overwrites)
    await ctx.send("🔓┃ O canal foi desbloqueado! Todos podem participar da conversa novamente. Vamos lá, fiquem à vontade! 🎉")

# Função para inicializar o banco de dados e criar a tabela de configuração, se não existir
async def init_db():
    async with aiosqlite.connect("economia.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS server_config (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel_id INTEGER,
                goodbye_channel_id INTEGER
            )
        """)
        await db.commit()

# Chamar init_db() ao iniciar o bot
@bot.event
async def on_ready():
    await init_db()
    print(f"Bot {bot.user} está pronto!")

# Variáveis globais para os canais de boas-vindas e despedidas
welcome_channel_id = None
goodbye_channel_id = None

# Comando para configurar o canal de boas-vindas
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setboasvindas(ctx, channel_id: int):
    async with aiosqlite.connect("economia.db") as db:
        await db.execute("""
            INSERT INTO server_config (guild_id, welcome_channel_id) 
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET welcome_channel_id = excluded.welcome_channel_id
        """, (ctx.guild.id, channel_id))
        await db.commit()
    await ctx.send(f"Canal de boas-vindas definido para <#{channel_id}>")

@setboasvindas.error
async def setboasvindas_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para usar este comando. É necessário ter a permissão de **Gerenciar Servidor**.")

# Comando para configurar o canal de despedidas
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setsaida(ctx, channel_id: int):
    async with aiosqlite.connect("economia.db") as db:
        await db.execute("""
            INSERT INTO server_config (guild_id, goodbye_channel_id) 
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET goodbye_channel_id = excluded.goodbye_channel_id
        """, (ctx.guild.id, channel_id))
        await db.commit()
    await ctx.send(f"Canal de despedidas definido para <#{channel_id}>")

@setsaida.error
async def setsaida_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para usar este comando. É necessário ter a permissão de **Gerenciar Servidor**.")

# Evento de entrada no servidor
@bot.event
async def on_member_join(member):
    async with aiosqlite.connect("economia.db") as db:
        async with db.execute("SELECT welcome_channel_id FROM server_config WHERE guild_id = ?", (member.guild.id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                channel = bot.get_channel(row[0])
                if channel:
                    embed = discord.Embed(
                        title="👋 Bem-vindo(a)!",
                        description=(
                            f"Seja bem-vindo(a), {member.mention}!\n\n"
                            f"📅 **Entrou em:** {member.joined_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
                            f"📌 **ID do usuário:** {member.id}\n\n"
                            f"⚠️ Não se esqueça de ler as regras e se precisar de ajuda, use o comando `!duvidas` para ver todos os comandos do bot."
                        ),
                        color=discord.Color.green()
                    )
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    await channel.send(embed=embed)

# Evento de saída do servidor
@bot.event
async def on_member_remove(member):
    async with aiosqlite.connect("economia.db") as db:
        async with db.execute("SELECT goodbye_channel_id FROM server_config WHERE guild_id = ?", (member.guild.id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                channel = bot.get_channel(row[0])
                if channel:
                    embed = discord.Embed(
                        title="💔 ⚰ Despedida!",
                        description=(
                            f"{member.mention}\n"
                            f"F demais!\n"
                            f"😢 **{member}** saiu do servidor.\n\n"
                            f"📌 **ID do usuário:** {member.id}"
                        ),
                        color=discord.Color.red()
                    )
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    await channel.send(embed=embed)

            
@bot.command(name='duvidas')
async def duvidas(ctx):
    response = (
        "Está com dúvidas sobre os comandos do BOT? AQUI ESTÁ TODOS OS COMANDOS DIVIDIDOS EM CATEGORIA!\n\n"
        "DIGITE **!duvida_moderação** PARA SABER TODOS OS COMANDOS SOBRE MODERAÇÃO!\n"
        "DIGITE **!duvida_economia** PARA SABER TODOS OS COMANDOS SOBRE ECONOMIA!\n"
        "DIGITE **!duvida_afk** PARA SABER TODOS OS COMANDOS SOBRE AFK!\n"
        "DIGITE **!duvida_minigames** PARA SABER TODOS OS COMANDOS SOBRE MINIGAMES!"
    )
    await ctx.send(response)

@bot.command(name='duvida_moderação')
async def duvida_moderacao(ctx):
    response = (
        "OS COMANDOS DE MODERAÇÃO SÃO: ( Esses comandos só podem ser usados pelos ADMINISTRADORES! )\n\n"
        "!kick: Expulsa alguém do servidor!\n"
        "!ban: Bane alguém do servidor!\n"
        "!unban: Desbane alguém do servidor.\n"
        "!clear <número>: Limpa mensagens.\n"
        "!lock: Bloqueia o chat (só pessoas com permissão Gerenciar Servidor podem usar).\n"
        "!unlock: Libera o chat (só pessoas com permissão Gerenciar Servidor podem usar)."
    )
    await ctx.send(response)

@bot.command(name='duvida_economia')
async def duvida_economia(ctx):
    response = (
        "OS COMANDOS DE ECONOMIA SÃO: ( Esses comandos podem ser usados por todo MUNDO! )\n\n"
        "!saldo: Você vê quantos Fox COINs você tem!\n"
        "!pay <usuário> <valor>: Você paga/doa para alguém Fox COINs.\n"
        "!ranking: Vê as pessoas com mais Fox COINs do servidor.\n"
        "!daily: Pega seu daily diário (uma vez ao dia)."
    )
    await ctx.send(response)

@bot.command(name='duvida_afk')
async def duvida_afk(ctx):
    response = (
        "O COMANDO DE AFK É: ( Esses comandos podem ser usados por todo MUNDO! )\n\n"
        "!afk <motivo>: Você fica afk até você falar de novo no chat."
    )
    await ctx.send(response)

@bot.command(name='duvida_minigames')
async def duvida_minigames(ctx):
    response = (
        "OS COMANDOS DE MINIGAMES SÃO: ( Esses comandos podem ser usados por todo MUNDO! )\n\n"
        "!trivia: Ele dá uma mini explicação de como funciona o jogo!\n"
        "!trivia_comprar: Você compra um ticket por 200 Fox COINs e se acertar ganha 300 Fox COINs.\n"
        "!apostar <valor>: Você aposta em um jogo de cara ou coroa onde você é sempre CARA!"
    )
    await ctx.send(response)


# Evento para quando o bot estiver pronto
@bot.event
async def on_ready():
    await init_db()
    await adicionar_coluna_last_daily()
    print(f'Bot {bot.user.name} está online!')
