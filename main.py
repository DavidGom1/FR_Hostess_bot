from telegram.ext import CallbackQueryHandler, CommandHandler, ApplicationBuilder, ContextTypes, JobQueue
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import datetime
import priv.config as cfg

sistema = ["Digi", "Anal"]
dias_semana = {
    "Lunes": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Martes": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Miercoles": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Jueves": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Viernes": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Sabado": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    "Domingo": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
}

async def limpieza(context) -> None:
    dia_hoy = datetime.datetime.now().strftime("%A")
    days_week = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"  }
    nombre_dia_semana_espanol = days_week[dia_hoy]
    if datetime.datetime.now().strftime("%H:%M") == "23:55:":
        print(nombre_dia_semana_espanol)
        for day, dia in days_week.items():
            if nombre_dia_semana_espanol == dia:
                for numero in dias_semana[dia]:
                    if len(numero) > 2:
                        dias_semana[dia][dias_semana[dia].index(numero)] = numero[:2]

async def reserva_dia(update, context):
    keyboard = [
        [
            InlineKeyboardButton(dia, callback_data=dia)
            ]
        for dia in dias_semana
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecciona el día deseas reservar:', reply_markup=reply_markup)

async def reserva_numero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        await query.edit_message_text(mensaje)
    elif callback_data == "anular":
        name_user = query.from_user.name
        for numero in dias_semana[dia_sel]:
            if name_user in numero:
                dias_semana[dia_sel][
                dias_semana[dia_sel].index(numero)] = numero[:2]
                context.chat_data['callback_data'] = None
                await query.edit_message_text(f"Reserva anulada para el {dia_sel}.")
    else:
        keyboard0 = [
            [
                InlineKeyboardButton(numero, callback_data=numero)
                ]
            for numero in dias_semana[dia_sel]
            ]
        reply_markup0 = InlineKeyboardMarkup(keyboard0)
        await query.edit_message_text(f'Selecciona un número para el {dia_sel}:', reply_markup=reply_markup0)

async def reserva_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    eleccion = query.data
    for dia in dias_semana:
        for numero in dias_semana[dia_sel]:
            if query.from_user.name in numero:
                await query.edit_message_text(f"Ya tienes reservada una frecuencia para el {dia_sel}, por favor elije otra.")
                return
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
        await query.edit_message_text(f"¡Frecuencia {query.data} reservada para {query.from_user.name} el {dia_sel}!")

async def tabla(update, context):
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
    jobqueue.run_repeating(limpieza, interval=30, first=0)

    application.add_handler(CommandHandler('reserva', reserva_dia))
    application.add_handler(CallbackQueryHandler(reserva_numero, pattern='^(Lunes|Martes|Miercoles|Jueves|Viernes|Sabado|Domingo)$'))
    application.add_handler(CallbackQueryHandler(reserva_response))
    application.add_handler(CommandHandler('tabla', tabla))
    application.add_handler(CommandHandler('anular', anular_reserva))

    application.run_polling()