import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from collections import defaultdict

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Sinf darajalari va kunlar
CLASS_LEVELS = [5, 6, 7, 8, 9, 10, 11]
days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]

# Fanlar va ularning haftalik soatlari + dars davomiyligi
SUBJECTS = {
    5: {
        "Tarix": {"weekly_hours": 1, "lesson_length": 2},
        "Matematika": {"weekly_hours": 6, "lesson_length": 2},
        "Ona tili": {"weekly_hours": 6, "lesson_length": 2},
        "Rus tili": {"weekly_hours": 2, "lesson_length": 2},
        "Jismoniy tarbiya": {"weekly_hours": 2, "lesson_length": 2},
        "Biologiya": {"weekly_hours": 1, "lesson_length": 1},
        "Python": {"weekly_hours": 4, "lesson_length": 2},
        "Robo": {"weekly_hours": 2, "lesson_length": 2},
        "Musiqa": {"weekly_hours": 1, "lesson_length": 1},
        "Tasviriy san'at": {"weekly_hours": 1, "lesson_length": 1}
    },
    6: {
        "Tarix": {"weekly_hours": 1, "lesson_length": 1},
        "Matematika": {"weekly_hours": 6, "lesson_length": 2},
        "Ona tili": {"weekly_hours": 6, "lesson_length": 2},
        "Rus tili": {"weekly_hours": 2, "lesson_length": 2},
        "Jismoniy tarbiya": {"weekly_hours": 2, "lesson_length": 1},
        "Biologiya": {"weekly_hours": 1, "lesson_length": 1},
        "Robo": {"weekly_hours": 2, "lesson_length": 2},
        "Python": {"weekly_hours": 2, "lesson_length": 2},
        "Musiqa": {"weekly_hours": 1, "lesson_length": 1},
        "Tasviriy san'at": {"weekly_hours": 1, "lesson_length": 1}
    },
    7: {
        "Tarix": {"weekly_hours": 1, "lesson_length": 1},
        "Matematika": {"weekly_hours": 6, "lesson_length": 2},
        "Ona tili": {"weekly_hours": 6, "lesson_length": 2},
        "Rus tili": {"weekly_hours": 2, "lesson_length": 2},
        "Texnologiya": {"weekly_hours": 1, "lesson_length": 1},
        "Jismoniy tarbiya": {"weekly_hours": 2, "lesson_length": 2},
        "Robo": {"weekly_hours": 2, "lesson_length": 2},
        "Python": {"weekly_hours": 4, "lesson_length": 2},
        "Musiqa": {"weekly_hours": 1, "lesson_length": 1},
        "Tasviriy san'at": {"weekly_hours": 1, "lesson_length": 1},
        "Fizika": {"weekly_hours": 1, "lesson_length": 1},
        "Biologiya": {"weekly_hours": 1, "lesson_length": 1},
        "Kimyo": {"weekly_hours": 1, "lesson_length": 1}
    },
    8: {
        "Tarix": {"weekly_hours": 2, "lesson_length": 1},
        "Matematika": {"weekly_hours": 6, "lesson_length": 2},
        "Ona tili": {"weekly_hours": 6, "lesson_length": 2},
        "Rus tili": {"weekly_hours": 2, "lesson_length": 2},
        "Jismoniy tarbiya": {"weekly_hours": 2, "lesson_length": 2},
        "AI": {"weekly_hours": 2, "lesson_length": 2},
        "Python": {"weekly_hours": 4, "lesson_length": 2},
        "Fizika": {"weekly_hours": 1, "lesson_length": 1},
        "Biologiya": {"weekly_hours": 1, "lesson_length": 1},
        "Kimyo": {"weekly_hours": 1, "lesson_length": 1}
    },
    9: {
        "Tarix": {"weekly_hours": 2, "lesson_length": 1},
        "Matematika": {"weekly_hours": 6, "lesson_length": 2},
        "Ona tili": {"weekly_hours": 6, "lesson_length": 2},
        "Rus tili": {"weekly_hours": 2, "lesson_length": 2},
        "Jismoniy tarbiya": {"weekly_hours": 1, "lesson_length": 1},
        "AI": {"weekly_hours": 4, "lesson_length": 2},
        "WEB": {"weekly_hours": 4, "lesson_length": 2},
        "Fizika": {"weekly_hours": 1, "lesson_length": 1},
        "Biologiya": {"weekly_hours": 1, "lesson_length": 1},
        "Kimyo": {"weekly_hours": 1, "lesson_length": 1}
    },
    10: {
        "Tarbiya": {"weekly_hours": 1, "lesson_length": 1},
        "Tarix": {"weekly_hours": 2, "lesson_length": 1},
        "Matematika": {"weekly_hours": 6, "lesson_length": 2},
        "Ona tili": {"weekly_hours": 6, "lesson_length": 2},
        "Rus tili": {"weekly_hours": 2, "lesson_length": 2},
        "Jismoniy tarbiya": {"weekly_hours": 2, "lesson_length": 2},
        "AI": {"weekly_hours": 4, "lesson_length": 2},
        "WEB": {"weekly_hours": 4, "lesson_length": 2},
        "Fizika": {"weekly_hours": 1, "lesson_length": 1},
        "Biologiya": {"weekly_hours": 1, "lesson_length": 1},
        "Kimyo": {"weekly_hours": 1, "lesson_length": 1}
    },
    11: {
        "Tarix": {"weekly_hours": 2, "lesson_length": 1},
        "Matematika": {"weekly_hours": 6, "lesson_length": 2},
        "Ona tili": {"weekly_hours": 6, "lesson_length": 2},
        "Rus tili": {"weekly_hours": 1, "lesson_length": 1},
        "Jismoniy tarbiya": {"weekly_hours": 2, "lesson_length": 1},
        "AI": {"weekly_hours": 4, "lesson_length": 2},
        "WEB": {"weekly_hours": 4, "lesson_length": 2}
    }
}

# Har bir fan uchun ustozlar
TEACHERS = {
    "Tarix": ["Tarix ustoz 1"],
    "Matematika": ["Matematika ustoz 1"],
    "Ona tili": ["Ona tili ustoz 1"],
    "Rus tili": ["Rus tili ustoz 1"],
    "Tarbiya": ["Tarbiya ustoz 1"],
    "Texnologiya": ["Texnologiya ustoz 1"],
    "Jismoniy tarbiya": ["Jismoniy tarbiya ustoz 1", "Jismoniy tarbiya ustoz 2"],
    "Biologiya": ["Biologiya ustoz 1"],
    "Python": ["Python ustoz 1"],
    "Robo": ["Robo ustoz 1"],
    "Musiqa": ["Musiqa ustoz 1"],
    "Tasviriy san'at": ["Tasviriy san'at ustoz 1"],
    "Fizika": ["Fizika ustoz 1", "Fizika ustoz 2"],
    "Kimyo": ["Kimyo ustoz 1"],
    "AI": ["AI ustoz 1"],
    "WEB": ["WEB ustoz 1"]
}

# Maktab turlari
SCHOOL_TYPES = {
    "standard": {"max_daily_hours": 6, "max_daily_lessons": 6},
    "extended": {"max_daily_hours": 7, "max_daily_lessons": 7},
    "gimnaziya": {"max_daily_hours": 8, "max_daily_lessons": 8}
}

# Conversation holatlari
SELECT_SCHOOL_TYPE, GET_CLASS_INFO = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni ishga tushirish"""
    await update.message.reply_text(
        "📅 Dars jadvali generatori (5-11 sinflar)\n\n"
        "Avval maktab turini tanlang:\n"
        "/standard - Kunlik 6 soat (maksimal 6 dars)\n"
        "/extended - Kunlik 7 soat (maksimal 7 dars)\n"
        "/gimnaziya - Kunlik 8 soat (maksimal 8 dars)",
        parse_mode="HTML"
    )
    return SELECT_SCHOOL_TYPE


async def select_school_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maktab turini tanlash"""
    school_type = update.message.text.strip().lower().replace('/', '')

    if school_type not in SCHOOL_TYPES:
        await update.message.reply_text(
            "⚠️ Noto'g'ri tanlov! Quyidagilardan birini tanlang:\n"
            "/standard - Kunlik 6 soat\n"
            "/extended - Kunlik 7 soat\n"
            "/gimnaziya - Kunlik 8 soat",
            parse_mode="HTML"
        )
        return SELECT_SCHOOL_TYPE

    context.user_data['school_type'] = school_type
    await update.message.reply_text(
        f"✅ Tanlandi: {school_type} (kunlik {SCHOOL_TYPES[school_type]['max_daily_hours']} soat)\n\n"
        "Endi har bir sinf uchun sinflar sonini kiriting (1-9 oralig'ida):\n"
        "Masalan: <code>5-sinf:3,6-sinf:2,7-sinf:2,8-sinf:1,9-sinf:1,10-sinf:1,11-sinf:1</code>",
        parse_mode="HTML"
    )
    return GET_CLASS_INFO


async def place_lesson(subject, length, available_teachers, timetable,
                       teacher_workload, teacher_schedule, class_id,
                       max_hours, max_lessons, update):
    """Bitta darsni jadvalga joylashtirish"""
    teacher_assigned = False

    # Agar ustoz bo'lmasa xabar beramiz
    if not available_teachers:
        logger.warning(f"{subject} uchun ustoz topilmadi!")
        if update:
            await update.message.reply_text(f"⚠️ {subject} faniga ustoz yetmayapti!")
        return False

    # Ustozlarni ish yuki bo'yicha saralash
    available_teachers.sort(key=lambda t: (
        teacher_workload[t]["total"],
        len([d for d in days if teacher_workload[t][d] > 0])
    ))

    for teacher in available_teachers:
        if teacher_assigned:
            break

        # Kunlarni ish yuki bo'yicha saralash
        days_sorted = sorted(days, key=lambda d: (
            sum(int(les.split('-')[-1].split()[0]) if '-' in les else 1
                for les in timetable[d]
                ), len(timetable[d]), teacher_workload[teacher][d]))

        for day in days_sorted:
            if teacher_assigned:
                break

            # Kunlik jami soatlarni hisoblash
            current_day_hours = sum(
                int(les.split('-')[-1].split()[0]) if '-' in les else 1
                for les in timetable[day]
            )

            # Cheklovlarni tekshirish
            if current_day_hours + length > max_hours:
                continue
            if len(timetable[day]) >= max_lessons:
                continue
            if (day, class_id) in teacher_schedule[teacher].get('classes', set()):
                continue

            # Fan bir kun ichida takrorlanmasligi
            if any(subject in lesson for lesson in timetable[day]):
                continue

            # Darsni qo'shish
            if length > 1:
                lesson_str = f"{subject} ({teacher}) - {length} soat"
            else:
                lesson_str = f"{subject} ({teacher})"

            timetable[day].append(lesson_str)
            teacher_workload[teacher]["total"] += length
            teacher_workload[teacher][day] += length
            teacher_assigned = True

            # Ustoz jadvalini yangilash
            if 'classes' not in teacher_schedule[teacher]:
                teacher_schedule[teacher]['classes'] = set()
            teacher_schedule[teacher]['classes'].add((day, class_id))

    return teacher_assigned


async def generate_class_timetable(class_level, class_num, teacher_workload, teacher_schedule, school_type, update):
    """Bir sinf uchun jadval yaratish"""
    timetable = {day: [] for day in days}
    class_id = f"{class_level}-{class_num}"
    max_hours = SCHOOL_TYPES[school_type]['max_daily_hours']
    max_lessons = SCHOOL_TYPES[school_type]['max_daily_lessons']

    # Fanlarni haftalik soatlari kamayish tartibida saralash
    sorted_subjects = sorted(
        SUBJECTS[class_level].items(),
        key=lambda x: (-x[1]['weekly_hours'], -x[1]['lesson_length'])
    )

    for subject, subject_info in sorted_subjects:
        weekly_hours = subject_info['weekly_hours']
        lesson_length = subject_info['lesson_length']
        available_teachers = TEACHERS.get(subject, [])

        if not available_teachers:
            await update.message.reply_text(f"⚠️ {subject} faniga ustoz yetmayapti!")
            continue

        # Darslar sonini hisoblash
        full_lessons = weekly_hours // lesson_length
        remaining_hours = weekly_hours % lesson_length

        # To'liq darslarni joylashtirish
        for _ in range(full_lessons):
            placed = await place_lesson(subject, lesson_length, available_teachers,
                                        timetable, teacher_workload, teacher_schedule,
                                        class_id, max_hours, max_lessons, update)
            if not placed:
                break

        # Qolgan soatlarni joylashtirish
        if remaining_hours > 0:
            await place_lesson(subject, remaining_hours, available_teachers,
                               timetable, teacher_workload, teacher_schedule,
                               class_id, max_hours, max_lessons, update)

    return timetable


async def generate_timetable_for_all_classes(class_counts, school_type, update):
    """Barcha sinflar uchun jadval yaratish"""
    all_timetables = {}
    teacher_workload = defaultdict(lambda: defaultdict(int))
    teacher_schedule = defaultdict(lambda: defaultdict(set))

    for class_level, class_count in sorted(class_counts.items()):
        if class_level not in CLASS_LEVELS:
            continue

        class_timetables = []
        for class_num in range(1, class_count + 1):
            timetable = await generate_class_timetable(
                class_level, class_num, teacher_workload, teacher_schedule, school_type, update
            )
            class_timetables.append(timetable)
        all_timetables[class_level] = class_timetables

    return all_timetables, teacher_workload


async def send_long_message(update: Update, text: str, max_length=4000):
    """Uzun xabarlarni qismlarga bo'lib yuborish"""
    for i in range(0, len(text), max_length):
        part = text[i:i + max_length]
        await update.message.reply_text(part, parse_mode="HTML")


async def send_timetables(update: Update, timetables, teacher_workload):
    """Jadvallarni foydalanuvchiga yuborish"""
    # Sinf jadvallari
    for class_level, class_timetables in timetables.items():
        for i, timetable in enumerate(class_timetables, 1):
            msg = [f"<b>{class_level}-sinf, Sinf {i}:</b>"]
            for day in days:
                if timetable[day]:
                    day_hours = sum(
                        int(les.split('-')[-1].split()[0]) if '-' in les else 1
                        for les in timetable[day]
                    )
                    msg.append(f"\n<b>{day}:</b> ({day_hours} soat)")
                    for j, lesson in enumerate(timetable[day], 1):
                        msg.append(f"{j}. {lesson}")
            await send_long_message(update, "\n".join(msg))

    # Ustozlarning ish yuki
    workload_msg = ["<b>Ustozlarning ish yuki:</b>"]
    for subject in sorted(TEACHERS.keys()):
        workload_msg.append(f"\n<b>{subject}:</b>")
        for teacher in TEACHERS[subject]:
            days_worked = [d for d in days if teacher_workload[teacher][d] > 0]
            workload_msg.append(
                f"{teacher}: {teacher_workload[teacher]['total']} soat "
                f"({', '.join(f'{d}:{teacher_workload[teacher][d]}' for d in days_worked)})"
            )
    await send_long_message(update, "\n".join(workload_msg))


async def process_class_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi kiritgan ma'lumotlarni qayta ishlash"""
    try:
        text = update.message.text.strip()
        class_counts = {}
        school_type = context.user_data.get('school_type', 'standard')

        parts = [p.strip() for p in text.split(",") if p.strip()]
        for part in parts:
            if ":" not in part:
                continue

            level_part, count_part = part.split(":", 1)
            level = int(''.join([c for c in level_part if c.isdigit()]))
            count = int(''.join([c for c in count_part if c.isdigit()]))

            if level in CLASS_LEVELS and 1 <= count <= 9:
                class_counts[level] = count
            else:
                await update.message.reply_text(
                    "⚠️ Noto'g'ri son yoki sinf darajasi! Faqat 5-11 sinflar va 1-9 oralig'ida son kiriting.",
                    parse_mode="HTML"
                )
                return GET_CLASS_INFO

        if not class_counts:
            raise ValueError("Hech qanday ma'lumot kiritilmadi")

        # Jadval generatsiya qilish
        timetables, teacher_workload = await generate_timetable_for_all_classes(class_counts, school_type, update)
        await send_timetables(update, timetables, teacher_workload)

    except ValueError as e:
        logger.error(f"Xatolik: {str(e)}")
        await update.message.reply_text(
            "⚠️ Xato format! Iltimos, quyidagi formatda kiriting:\n"
            "<code>5-sinf:3,6-sinf:2,7-sinf:2,8-sinf:1,9-sinf:1,10-sinf:1,11-sinf:1</code>\n\n"
            "Har bir sinf uchun 1-9 oralig'ida son kiriting. "
            "Faqat vergul bilan ajrating.",
            parse_mode="HTML"
        )
        return GET_CLASS_INFO
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {str(e)}")
        await update.message.reply_text(
            "⚠️ Kutilmagan xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversationni bekor qilish"""
    await update.message.reply_text("Jarayon bekor qilindi. /start buyrug'i bilan qayta boshlashingiz mumkin.")
    return ConversationHandler.END


def main():
    """Dasturni ishga tushirish"""
    application = Application.builder().token("7830429206:AAHFLVu-UZN1HA9-oLu2vdF6X7m2XCIoPqQ").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_SCHOOL_TYPE: [
                CommandHandler('standard', select_school_type),
                CommandHandler('extended', select_school_type),
                CommandHandler('gimnaziya', select_school_type),
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_school_type)
            ],
            GET_CLASS_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_class_info)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    logger.info("Bot ishga tushdi...")
    application.run_polling()


if __name__ == "__main__":
    main()