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
import random
from collections import defaultdict

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7830429206:AAHFLVu-UZN1HA9-oLu2vdF6X7m2XCIoPqQ"

# Sinf darajalari
CLASS_LEVELS = [1, 2, 3, 4]
days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma"]

# Asosiy fanlar
BASE_SUBJECTS = {
    1: {"Ona tili": 4, "o'qish": 4, "Matematika": 5, "Science": 1, "Texnologiya": 1, "Tarbiya": 1,
        "Tasviriy san'at": 1},
    2: {"Ona tili": 3, "o'qish": 4, "Matematika": 5, "Science": 2, "Texnologiya": 1, "Tarbiya": 1,
        "Tasviriy san'at": 1},
    3: {"Ona tili": 3, "o'qish": 4, "Matematika": 5, "Science": 2, "Texnologiya": 1, "Tarbiya": 1,
        "Tasviriy san'at": 1},
    4: {"Ona tili": 3, "o'qish": 4, "Matematika": 5, "Science": 2, "Texnologiya": 1, "Tarbiya": 1, "Tasviriy san'at": 1}
}

# Qo'shimcha fanlar
EXTRA_SUBJECTS = {
    1: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1},
    2: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1, "Rus tili": 2},
    3: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1, "Rus tili": 2},
    4: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1, "Rus tili": 2}
}

# Ustozlar
TEACHERS = {
    "base": "Sinf rahbari",
    "Jismoniy tarbiya": ["Tarbiya ustoz 1"],
    "Chet tili": ["Ingliz tili ustoz 1"],
    "Rus tili": ["Rus tili ustoz 1"],
    "Musiqa": ["Musiqa ustoz 1"],
}


def generate_class_timetable(class_level, class_num, teacher_workload, teacher_schedule):
    """Bir sinf uchun jadval yaratish"""
    timetable = {day: [] for day in days}
    class_id = f"{class_level}-{class_num}"

    # Asosiy fanlarni joylashtirish (sinf rahbari)
    for subject, weekly_hours in BASE_SUBJECTS[class_level].items():
        scheduled = 0
        while scheduled < weekly_hours:
            day = random.choice(days)

            # Cheklovlarni tekshirish
            math_limit = (subject == "Matematika" and
                          sum(1 for les in timetable[day] if "Matematika" in les) >= 1)
            base_limit = (subject != "Matematika" and
                          sum(1 for les in timetable[day] if subject in les) >= 2)
            daily_limit = len(timetable[day]) >= 5
            consecutive = len(timetable[day]) > 0 and subject in timetable[day][-1]

            if not (math_limit or base_limit or daily_limit or consecutive):
                timetable[day].append(f"{subject} ({TEACHERS['base']})")
                scheduled += 1

    # Qo'shimcha fanlarni joylashtirish
    for subject, weekly_hours in EXTRA_SUBJECTS.get(class_level, {}).items():
        scheduled = 0
        available_teachers = TEACHERS.get(subject, [])

        if not available_teachers:
            continue

        # Ustozlarni ish yuki kam bo'yicha saralash (kam kunlarda ishlaganlar oldin)
        available_teachers.sort(key=lambda t: len([d for d in days if teacher_workload[t][d] > 0]))

        for teacher in available_teachers:
            remaining_hours = weekly_hours - scheduled
            if remaining_hours <= 0:
                break

            # Ustozning ishlagan kunlarini saralash (ko'p ishlagan kunlar oldin)
            teacher_days = [d for d in days if teacher_workload[teacher][d] > 0]
            teacher_days.sort(key=lambda d: -teacher_workload[teacher][d])

            # Ustoz ishlamagan kunlarni qo'shamiz
            other_days = [d for d in days if d not in teacher_days]
            days_priority = teacher_days + other_days

            for day in days_priority:
                if scheduled >= weekly_hours:
                    break

                # Ustoz bu kunda bu sinfga dars bermaganligini tekshirish
                if (day, class_id) in teacher_schedule[teacher].get('classes', set()):
                    continue

                # Ustoz kuniga maksimal 5 soat dars bera oladi
                if teacher_workload[teacher][day] >= 5:
                    continue

                # Sinfda bo'sh soat borligini tekshirish
                if len(timetable[day]) >= 5:
                    continue

                # Ketma-ket darslarning oldini olish
                hour = find_best_hour(day, subject, timetable)
                if hour is None:
                    continue

                # Darsni qo'shamiz
                timetable[day].insert(hour - 1, f"{subject} ({teacher})")
                teacher_workload[teacher]["total"] += 1
                teacher_workload[teacher][day] += 1
                scheduled += 1

                # Ustozning jadvalini yangilaymiz
                if 'classes' not in teacher_schedule[teacher]:
                    teacher_schedule[teacher]['classes'] = set()
                teacher_schedule[teacher]['classes'].add((day, class_id))

    return timetable


def find_best_hour(day, subject, timetable):
    """Eng yaxshi soatni topish, ketma-ketlikni oldini olish uchun"""
    available_hours = set(range(1, 6)) - {i + 1 for i, les in enumerate(timetable[day])}

    # Avvalo, boshqa fanlar orasiga joylashtirishga harakat qilamiz
    for hour in sorted(available_hours):
        prev_lesson = timetable[day][hour - 2] if hour > 1 and len(timetable[day]) >= hour - 1 else None
        next_lesson = timetable[day][hour] if hour <= len(timetable[day]) else None

        if (prev_lesson and subject in prev_lesson) or (next_lesson and subject in next_lesson):
            continue
        return hour

    # Agar bunday soat topilmasa, boshqa soatlarni ko'rib chiqamiz
    for hour in sorted(available_hours):
        prev_lesson = timetable[day][hour - 2] if hour > 1 and len(timetable[day]) >= hour - 1 else None
        if prev_lesson and subject in prev_lesson:
            continue
        return hour

    return None


def generate_timetable_for_all_classes(class_counts):
    """Barcha sinflar uchun jadval yaratish"""
    all_timetables = {}
    teacher_workload = defaultdict(lambda: defaultdict(int))
    teacher_schedule = defaultdict(lambda: defaultdict(set))

    # Ustozlarni ish yuki lug'atini yaratish
    for subject in TEACHERS:
        if subject != "base":
            for teacher in TEACHERS[subject]:
                teacher_workload[teacher] = {"total": 0, "Dushanba": 0, "Seshanba": 0,
                                             "Chorshanba": 0, "Payshanba": 0, "Juma": 0}

    # Har bir sinf uchun jadval yaratish
    for class_level, class_count in sorted(class_counts.items()):
        class_timetables = []
        for class_num in range(1, class_count + 1):
            timetable = generate_class_timetable(
                class_level, class_num, teacher_workload, teacher_schedule
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
                    msg.append(f"\n<b>{day}:</b>")
                    for j, lesson in enumerate(timetable[day]):
                        msg.append(f"{j + 1}. {lesson}")
            await send_long_message(update, "\n".join(msg))

    # Ustozlarning ish yuki
    workload_msg = ["<b>Ustozlarning ish yuki:</b>"]
    for subject in TEACHERS:
        if subject != "base":
            workload_msg.append(f"\n<b>{subject}:</b>")
            for teacher in TEACHERS[subject]:
                days_worked = [d for d in days if teacher_workload[teacher][d] > 0]
                workload_msg.append(
                    f"{teacher}: {teacher_workload[teacher]['total']} soat "
                    f"({', '.join(f'{d}:{teacher_workload[teacher][d]}' for d in days_worked)})"
                )
    await send_long_message(update, "\n".join(workload_msg))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni ishga tushirish"""
    await update.message.reply_text(
        "📅 Dars jadvali generatori\n\n"
        "Har bir sinf uchun sinflar sonini kiriting (1-9 oralig'ida):\n"
        "Masalan: <code>1-sinf:3,2-sinf:1,3-sinf:2,4-sinf:1</code>\n\n"
        "Bu 1-sinfdan 3 ta, 2-sinfdan 1 ta sinf borligini bildiradi",
        parse_mode="HTML"
    )
    return 1


async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi kiritgan ma'lumotlarni qayta ishlash"""
    try:
        text = update.message.text.strip()
        class_counts = {}

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
                    "⚠️ Noto'g'ri son! Har bir sinf uchun 1-9 oralig'ida son kiriting.",
                    parse_mode="HTML"
                )
                return 1

        if not class_counts:
            raise ValueError("Hech qanday ma'lumot kiritilmadi")

        # Jadval generatsiya qilish
        timetables, teacher_workload = generate_timetable_for_all_classes(class_counts)
        await send_timetables(update, timetables, teacher_workload)

    except ValueError as e:
        logger.error(f"Xatolik: {str(e)}")
        await update.message.reply_text(
            "⚠️ Xato format! Iltimos, quyidagi formatda kiriting:\n"
            "<code>1-sinf:3,2-sinf:1,3-sinf:2,4-sinf:1</code>\n\n"
            "Har bir sinf uchun 1-9 oralig'ida son kiriting. "
            "Faqat vergul bilan ajrating.",
            parse_mode="HTML"
        )
        return 1
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {str(e)}")
        await update.message.reply_text(
            "⚠️ Kutilmagan xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            parse_mode="HTML"
        )
        return 1

    return ConversationHandler.END


def main():
    """Dasturni ishga tushirish"""
    try:
        application = Application.builder().token(TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_input)],
            },
            fallbacks=[],
        )

        application.add_handler(conv_handler)

        logger.info("Bot ishga tushdi...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Bot ishga tushmadi: {str(e)}")


if __name__ == "__main__":
    main()