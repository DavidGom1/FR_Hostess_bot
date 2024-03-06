from telegram.ext import CallbackQueryHandler, CommandHandler, ApplicationBuilder, ContextTypes, JobQueue
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import datetime, pytz
import priv.config as cfg

sistema = ["Digi", "Anal"]
chats_permitidos = [-1002036234330, 545562756] #
dias_semana = {
    "Lunes": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Martes": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Miércoles": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Jueves": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Viernes": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Sabado": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Domingo": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
}

async def ban(update) -> None:
    chat_id = update.message.chat_id
    if chat_id not in chats_permitidos:
        await update.message.reply_text("No tienes permisos para usar este bot.")
        return False
    return True

async def limpieza(context) -> None:
    dia_hoy = datetime.datetime.now().strftime("%A")
    hora_local = datetime.datetime.now(pytz.timezone('Europe/Madrid')).strftime("%H:%M")
    days_week = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"  }
    nombre_dia_semana_espanol = days_week[dia_hoy]
    if hora_local == "07:29":
        for day, dia in days_week.items():
            if nombre_dia_semana_espanol == dia:
                for numero in dias_semana[dia]:
                    if len(numero) > 2:
                        dias_semana[dia][dias_semana[dia].index(numero)] = numero[:2]

async def reserva_dia(update, context):
    if not await ban(update):   return # Si no tiene permisos, la función se detiene
    keyboard = [
        [
            InlineKeyboardButton(dia, callback_data=dia)
            ]
        for dia in dias_semana
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecciona el día deseas reservar:', reply_markup=reply_markup)

async def reserva_numero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #if not await ban(update):   return # Si no tiene permisos, la función se detiene
    query = update.callback_query
    message = update.message
    global dia_sel
    dia_sel = query.data
    callback_data = context.chat_data.get('callback_data')
    if callback_data == "tabla":
        mensaje = f'La tabla de frecuencias para el {dia_sel} es:\n'
        for numero in dias_semana[dia_sel]:
            mensaje += f"- {numero}\n"
        context.chat_data['callback_data'] = None
        await query.edit_message_text(mensaje + "\nSi lo necesitas, /anula tu reserva, o /reserva otra frecuencia.")
    elif callback_data == "anular":
        name_user = query.from_user.name
        for numero in dias_semana[dia_sel]:
            if name_user in numero:
                dias_semana[dia_sel][dias_semana[dia_sel].index(numero)] = numero[:2]
                context.chat_data['callback_data'] = None
                await query.edit_message_text(f"Reserva anulada para el {dia_sel}. \n Si lo necesitas, /reserva otra frecuencia")
    else:
        for numero in dias_semana[dia_sel]:
            if query.from_user.name in numero:
                await query.edit_message_text(f"Ya tienes reservada una frecuencia para el {dia_sel}, por favor /anula tu reserva y elije otra disponible.")
                return
            else:
                keyboard0 = [
                    [
                        InlineKeyboardButton(num, callback_data=num)
                        ]
                    for num in dias_semana[dia_sel]
                    ]
                reply_markup0 = InlineKeyboardMarkup(keyboard0)
        await query.edit_message_text(f'Selecciona una freccencia para el {dia_sel}:', reply_markup=reply_markup0)


async def reserva_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #if not await ban(update):   return # Si no tiene permisos, la función se detiene
    query = update.callback_query
    await query.answer()
    eleccion = query.data
    """for dia in dias_semana:
        for numero in dias_semana[dia_sel]:
            if query.from_user.name in numero:
                await query.edit_message_text(f"Ya tienes reservada una frecuencia para el {dia_sel}, por favor /anula tu reserva y elije otra disponible.")
                return
                """
    if len(query.data) > 2:
        await query.edit_message_text(f"Esta frecuencia ya se encuentra reservada, por favor elije otra.")
        return
    else:
        index = dia_sel
        nuevo_valor = f"{query.data} - {query.from_user.name}"
        if index in dias_semana:
            lista_de_frecuencias = dias_semana[index]
            if eleccion in lista_de_frecuencias:
                indice = lista_de_frecuencias.index(eleccion)
                lista_de_frecuencias[indice] = nuevo_valor
        await query.edit_message_text(f"¡Frecuencia {query.data} reservada para {query.from_user.name} el {dia_sel}! \n Si lo necesitas, /anula tu reserva o /reserva otro día.")

async def tabla(update, context):
    if not await ban(update):   return # Si no tiene permisos, la función se detiene
    context.chat_data['callback_data'] = "tabla"
    keyboard1 = [
        [
            InlineKeyboardButton(dia, callback_data=dia)
            ]
        for dia in dias_semana
        ]
    reply_markup1 = InlineKeyboardMarkup(keyboard1)
    await update.message.reply_text('Selecciona el día para ver la tabla de frecuencias:', reply_markup=reply_markup1)

async def anular_reserva(update, context):
    if not await ban(update):   return # Si no tiene permisos, la función se detiene
    context.chat_data['callback_data'] = "anular"
    keyboard2 = [
        [
            InlineKeyboardButton(dia, callback_data=dia)
            ]
        for dia in dias_semana
        ]
    reply_markup2 = InlineKeyboardMarkup(keyboard2)
    await update.message.reply_text('Selecciona el día para ver la tabla de frecuencias:', reply_markup=reply_markup2)

if __name__ == '__main__':
    application = ApplicationBuilder().token(cfg.TOKEN).build()
    jobqueue = application.job_queue
    jobqueue.run_repeating(limpieza, interval=3, first=0)

    application.add_handler(CommandHandler('reserva', reserva_dia))
    application.add_handler(CallbackQueryHandler(reserva_numero, pattern='^(Lunes|Martes|Miércoles|Jueves|Viernes|Sabado|Domingo)$'))
    application.add_handler(CallbackQueryHandler(reserva_response))
    application.add_handler(CommandHandler('tabla', tabla))
    application.add_handler(CommandHandler('anula', anular_reserva))

    application.run_polling()