# -*- coding: utf-8 -*-

from telegram.ext import CallbackQueryHandler, CommandHandler, ApplicationBuilder, ContextTypes, JobQueue
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import datetime, pytz, os, mysql.connector, logging
import priv.config as cfg
import bd_template as bd_template

logging.basicConfig(    #configuramos el logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  #formato del logging
    level=logging.INFO  #nivel del logging
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def insertar_valores_lista(x,y,z, id_chat): # Funcion que itera en la lista que le pasamos pod x, con nombre de tabla en y y nombre de columna en z ( igual que abajo)
    for valor in x:
        conexion = mysql.connector.connect(**bd_template.config)
        cursor = conexion.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS chat_{}".format(id_chat))
        conexion.database = "chat_{}".format(id_chat)
        consulta_select = f"SELECT * FROM {y} WHERE {z} = %s"
        cursor.execute(consulta_select, (valor,))
        busqueda = cursor.fetchall()
        if not busqueda:
            consulta_insert = f"INSERT INTO {y} ({z}) VALUES (%s)"
            cursor.execute(consulta_insert, (valor,))
            conexion.commit()
        else:
            pass

async def reserva_dia(update, context):
    global user_name
    user_name = update.message.from_user.username

    if not await cfg.ban(update, context):   return # Si no tiene permisos, la función se detiene
    keyboard = [
        [
            InlineKeyboardButton(dia, callback_data=dia)
            ]
        for dia in bd_template.dias_semana
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    #paso el dia pulsado en el teclado a la variable callback_data
    await update.message.reply_text('Selecciona el día deseas reservar:', reply_markup=reply_markup)

async def reserva_numero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    message = update.message
    #paso a variable el dia seleccionado en reserva_dia
    dia_sel = query.data
    # paso el id de este bot a la variable id_bot
    id_chat = str(context.bot.id).replace("-","") + "_" + str((context.bot.name).replace("@",""))
    id_grupo = str(query.message.chat_id).replace("-","")
    nombre_chat = str((context.bot.name).replace("@",""))
    print(id_chat, nombre_chat)
    callback_data = context.chat_data.get('callback_data')


    # ------ CONSTRUCCION DE LA TABLA DE FRECUENCIAS ------
    if callback_data == "tabla":
        conexion = mysql.connector.connect(**bd_template.config)
        mensaje = f'La tabla de frecuencias para el {dia_sel} es:\n'
        for numero in bd_template.frecuencias_dias:
            # Leo en la tabla de reservas si el numero esta reservado
            cursor = conexion.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS chat_{}".format(id_chat))
            conexion.database = "chat_{}".format(id_chat)
            consulta_select = "SELECT * FROM reservas WHERE dia = %s AND frecuencia = %s AND grupo = %s"
            cursor.execute(consulta_select, (dia_sel, numero, id_grupo))
            resultado = cursor.fetchall()
            if resultado:
                mensaje += f"- {numero} - {resultado[0][3]}\n"
            else:
                mensaje += f"- {numero}\n"

        context.chat_data['callback_data'] = None
        await query.edit_message_text(mensaje + "\nSi lo necesitas, /anula tu reserva, o /reserva otra frecuencia.")
        cursor.close()
        conexion.close()


    # ------ ANULACION DE RESERVA ------
    elif callback_data == "anular":
        # Consultar si el usuario tiene una reserva en el dia seleccionado en la tabla reservas y borrar la reserva
        conexion = mysql.connector.connect(**bd_template.config)
        cursor = conexion.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS chat_{}".format(id_chat))
        conexion.database = "chat_{}".format(id_chat)
        consulta_select = "SELECT * FROM reservas WHERE dia = %s AND usuario = %s AND grupo = %s"
        cursor.execute(consulta_select, (dia_sel, user_name, id_grupo))
        resultado = cursor.fetchall()
        if resultado:
            consulta = "DELETE FROM reservas WHERE dia = %s AND usuario = %s AND grupo = %s"
            cursor.execute(consulta, (dia_sel, user_name, id_grupo))
            conexion.commit()
            context.chat_data['callback_data'] = None
            await query.edit_message_text(f"Reserva anulada para el {dia_sel}. Si lo necesitas, /reserva otra frecuencia.")
        else:
            context.chat_data['callback_data'] = None
            await query.edit_message_text(f"No tienes ninguna reserva para el {dia_sel}. Si lo necesitas, /reserva otra frecuencia.")
        cursor.close()
        conexion.close()

    # ------ RESERVA DE FRECUENCIA ------
    else:
        conexion = mysql.connector.connect(**bd_template.config)
        cursor = conexion.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS chat_{}".format(id_chat))
        conexion.database = "chat_{}".format(id_chat)
        cursor.execute("CREATE TABLE IF NOT EXISTS reservas (ID INT AUTO_INCREMENT PRIMARY KEY, dia VARCHAR(255), frecuencia VARCHAR(255), usuario VARCHAR(255), grupo VARCHAR(255))")
        consulta_select = "SELECT * FROM reservas WHERE dia = %s AND usuario = %s AND grupo = %s"
        cursor.execute(consulta_select, (dia_sel, user_name, id_grupo))
        resultado = cursor.fetchall()
        if not resultado:
            keyboard0 = [
                [
                    InlineKeyboardButton(num, callback_data=num)
                    ]
                for num in bd_template.frecuencias_dias
                ]
            reply_markup0 = InlineKeyboardMarkup(keyboard0)
            context.chat_data['callback_data'] = str(dia_sel)
            await query.edit_message_text(f'Selecciona una frecuencia para el {dia_sel}:', reply_markup=reply_markup0)
        else:
            await query.edit_message_text(f"Ya tienes una reserva para el {dia_sel}. Si lo necesitas, /anula tu reserva o /reserva otro día.")
            context.chat_data['callback_data'] = None
        cursor.close()
        conexion.close()


async def reserva_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    dia = str(context.chat_data.get('callback_data'))
    frecuencia = query.data
    id_chat = str(context.bot.id).replace("-","") + "_" + str((context.bot.name).replace("@",""))
    id_grupo = str(query.message.chat_id).replace("-","")
    id_user = query.from_user.id

    conexion = mysql.connector.connect(**bd_template.config)
    cursor = conexion.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS chat_{}".format(id_chat))
    conexion.database = "chat_{}".format(id_chat)
    # Crear la tabla de dias de la semana si no existe y pasar los datos de bd_template.dias_semana a la tabla en dias
    cursor.execute("CREATE TABLE IF NOT EXISTS dias (ID INT AUTO_INCREMENT PRIMARY KEY, dia  VARCHAR(255))")
    insertar_valores_lista(bd_template.dias_semana, "dias", "dia", (id_chat))
    # Crear la tabla de frecuencias si no existe y pasar los datos de frecuencia a la tabla en frecuencias
    cursor.execute("CREATE TABLE IF NOT EXISTS frecuencias (ID INT AUTO_INCREMENT PRIMARY KEY, frecuencia VARCHAR(255))")
    insertar_valores_lista(bd_template.frecuencias_dias, "frecuencias", "frecuencia", id_chat)
    try:
        # Crear la tabla de usuarios si no existe con los datos del usuario
        cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (ID VARCHAR(255) PRIMARY KEY, name VARCHAR(255))")
        consulta_select = "SELECT * FROM usuarios WHERE ID = %s"
        cursor.execute(consulta_select, (id_chat,))
        resultado = cursor.fetchall()
        if not resultado:
            # Ejecutar la consulta SQL para insertar la clave y el valor en la tabla del diccionario
            consulta = "INSERT INTO usuarios (ID, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name = VALUES(name)"
            cursor.execute(consulta, (id_user, user_name))
            conexion.commit()
        else:
            pass

        # Crear tabla de reservas si no existe
        cursor.execute("CREATE TABLE IF NOT EXISTS reservas (ID INT AUTO_INCREMENT PRIMARY KEY, dia VARCHAR(255), frecuencia VARCHAR(255), usuario VARCHAR(255), grupo VARCHAR(255))")
        consulta_select = "SELECT * FROM reservas WHERE dia = %s AND frecuencia = %s AND grupo = %s"
        cursor.execute(consulta_select, (dia, frecuencia, id_grupo))
        resultado = cursor.fetchall()
        if not resultado:
            # Ejecutar la consulta SQL para insertar la clave y el valor en la tabla del diccionario
            consulta = "INSERT INTO reservas (dia, frecuencia, usuario, grupo) VALUES (%s, %s, %s, %s)"
            cursor.execute(consulta, (dia, frecuencia, user_name, id_grupo))
            conexion.commit()
            context.chat_data['callback_data'] = None
            await query.edit_message_text(f"¡Frecuencia {query.data} reservada para @{user_name} el {dia}! \n Recuerda no utilizar modos que usen mas de 1 canal (>25Mpbs)")
            cursor.close()
            conexion.close()
            return
        else:
            await query.edit_message_text(f"Esta frecuencia ya se encuentra reservada, por favor elije otra. 1")
            context.chat_data['callback_data'] = None
            cursor.close()
            conexion.close()
            return

    except mysql.connector.Error as error:
        await context.bot.send_message(chat_id=545562756, text=f"Error en la base de datos: {error}")
        cursor.close()
        conexion.close()
        context.chat_data['callback_data'] = None

async def tabla(update, context):
    global user_name
    user_name = update.message.from_user.username
    if not await cfg.ban(update, context):   return # Si no tiene permisos, la función se detiene
    context.chat_data['callback_data'] = "tabla"
    keyboard1 = [
        [
            InlineKeyboardButton(dia, callback_data=dia)
            ]
        for dia in bd_template.dias_semana
        ]
    reply_markup1 = InlineKeyboardMarkup(keyboard1)
    await update.message.reply_text('Selecciona el día para ver la tabla de frecuencias:', reply_markup=reply_markup1)

async def anular_reserva(update, context):
    global user_name
    user_name = update.message.from_user.username
    if not await cfg.ban(update, context):   return # Si no tiene permisos, la función se detiene
    context.chat_data['callback_data'] = "anular"
    keyboard2 = [
        [
            InlineKeyboardButton(dia, callback_data=dia)
            ]
        for dia in bd_template.dias_semana
        ]
    reply_markup2 = InlineKeyboardMarkup(keyboard2)
    await update.message.reply_text('Selecciona el día para ver la tabla de frecuencias:', reply_markup=reply_markup2)

async def tabla_ocupacion(update, context):
    # enviamos imagen llamada ocupacion_canales.jpg que se encuentra en la carpeta del bot
    if not await cfg.ban(update, context):   return # Si no tiene permisos, la función se detiene # Texto que deseas agregar al marco de la imagen
    # Texto que deseas agregar al marco de la imagen
    mensaje = "*TABLA DE OCUPACIÓN DE CANALES:*"

    # Enviamos el mensaje de texto primero con formato Markdown
    await update.message.reply_text(
        text=mensaje,
        parse_mode='Markdown'
    )

    # Luego, enviamos la imagen
    await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=open('ocupacion_canales.jpg', 'rb')
    )

async def limpieza(context) -> None:
    id_chat = str(context.bot.id).replace("-","") + "_" + str((context.bot.name).replace("@",""))
    dia_hoy = datetime.datetime.now().strftime("%A")
    hora_local = datetime.datetime.now(pytz.timezone('Europe/Madrid')).strftime("%H:%M")
    nombre_dia_semana_espanol = bd_template.days_translate[dia_hoy]
    print(f"dia_hoy: {nombre_dia_semana_espanol}, hora_local: {hora_local}")
    if hora_local == "23:55":
        for dia in bd_template.dias_semana:
            if nombre_dia_semana_espanol == dia:
                print('hoy es ' + dia)
                conexion = mysql.connector.connect(**bd_template.config)
                cursor = conexion.cursor()
                cursor.execute("CREATE DATABASE IF NOT EXISTS chat_{}".format(id_chat))
                conexion.database = "chat_{}".format(id_chat)
                consulta_select = "SELECT * FROM reservas WHERE dia = %s"
                cursor.execute(consulta_select, (dia,))
                resultado = cursor.fetchall()
                if resultado:
                    consulta_delete = "DELETE FROM reservas WHERE dia = %s"
                    cursor.execute(consulta_delete, (dia,))
                    conexion.commit()  # Confirmar la eliminación
                else:
                    pass
                cursor.close()
                conexion.close()

if __name__ == '__main__':
    application = ApplicationBuilder().token(cfg.TOKEN).build()

    jobqueue = application.job_queue
    jobqueue.run_repeating(limpieza, interval=20, first=0)

    application.add_handler(CommandHandler('reserva', reserva_dia))
    application.add_handler(CallbackQueryHandler(reserva_numero, pattern='^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)$'))
    application.add_handler(CallbackQueryHandler(reserva_response))
    application.add_handler(CommandHandler('tabla', tabla))
    application.add_handler(CommandHandler('anula', anular_reserva))
    application.add_handler(CommandHandler('tabla_ocupacion', tabla_ocupacion))


    application.run_polling()
