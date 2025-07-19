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

TOKEN = "7830429206:AAHFLVu-UZN1HA9-oLu2vdF6X7m2XCIoPqQ"  # BotFatherdan olingan token

# Sinf darajalari
CLASS_LEVELS = [1, 2, 3, 4]

# Asosiy fanlar
BASE_SUBJECTS = {
    1: {"Ona tili": 4, "o'qish": 4, "Matematika": 5, "Science": 1, "Texnologiya": 1, "Tarbiya": 1, "Tasviriy san'at": 1},
    2: {"Ona tili": 3, "o'qish": 4, "Matematika": 5, "Science": 2, "Texnologiya": 1, "Tarbiya": 1, "Tasviriy san'at": 1},
    3: {"Ona tili": 3, "o'qish": 4, "Matematika": 5, "Science": 2, "Texnologiya": 1, "Tarbiya": 1, "Tasviriy san'at": 1},
    4: {"Ona tili": 3, "o'qish": 4, "Matematika": 5, "Science": 2, "Texnologiya": 1, "Tarbiya": 1, "Tasviriy san'at": 1}
}

# Qo'shimcha fanlar
EXTRA_SUBJECTS = {
    1: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1},
    2: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1, "Rus tili": 2},
    3: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1, "Rus tili": 2},
    4: {"Jismoniy tarbiya": 2, "Chet tili": 2, "Musiqa": 1, "Rus tili": 2}
}

# Ustozlar (asosiy va qo'shimcha)
TEACHERS = {
    "base": "Sinf rahbari",
    "Jismoniy tarbiya": ["Tarbiya ustoz 1"],
    "Chet tili": ["Ingliz tili ustoz 1", ],
    "Rus tili": ["Rus tili ustoz 1", ],
    "Musiqa": ["Musiqa ustoz 1"],

}


async def send_long_message(update: Update, text: str, max_length=4000):
    """Uzun xabarlarni qismlarga bo'lib yuborish"""
    for i in range(0, len(text), max_length):
        part = text[i:i + max_length]
        await update.message.reply_text(part, parse_mode="HTML")


def generate_class_timetable(class_level, class_num, teacher_workload):
    """Bir sinf uchun jadval yaratish va ustozlarning ish yukini hisoblash"""
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma"]
    timetable = {day: [] for day in days}

    # Asosiy fanlarni joylashtirish (o'zgarmaydi)
    for subject, weekly_hours in BASE_SUBJECTS[class_level].items():
        scheduled = 0
        attempts = 0
        while scheduled < weekly_hours and attempts < 200:
            attempts += 1
            day = random.choice(days)

            # Cheklovlarni tekshirish
            math_limit = (subject == "Matematika" and
                          sum(1 for les in timetable[day] if les.startswith(f"Matematika")) >= 1)
            base_limit = (subject != "Matematika" and
                          sum(1 for les in timetable[day] if les.startswith(subject)) >= 2)
            daily_limit = len(timetable[day]) >= 5
            consecutive = timetable[day] and subject in timetable[day][-1]

            if math_limit or base_limit or daily_limit or consecutive:
                continue

            timetable[day].append(f"{subject} ({TEACHERS['base']})")
            scheduled += 1

    # Qo'shimcha fanlarni joylashtirish (optimallashtirilgan versiya)
    for subject, weekly_hours in EXTRA_SUBJECTS.get(class_level, {}).items():
        scheduled = 0
        attempts = 0
        available_teachers = TEACHERS.get(subject, [])

        if not available_teachers:
            continue

        # Ustozlarni ish yuki bo'yicha saralash (kam ishlaganlar oldin)
        sorted_teachers = sorted(available_teachers, key=lambda t: (
            teacher_workload[t]["total"],
            len([d for d in days if teacher_workload[t][d] > 0])
        ))

        for teacher in sorted_teachers:
            # Ustoz uchun optimal kunlarni tanlash (haftada 2-3 kun)
            teacher_days = [d for d in days if teacher_workload[teacher][d] < 5]

            # Agar ustoz allaqachon 3 kunga tayinlangan bo'lsa, yangi kun qo'shmaslik
            active_days = len([d for d in days if teacher_workload[teacher][d] > 0])
            if active_days >= 3:
                teacher_days = [d for d in teacher_days if teacher_workload[teacher][d] > 0]

            # Har bir tanlangan kunga kamida 3 soat dars qo'yish
            for day in teacher_days:
                if scheduled >= weekly_hours:
                    break

                if len(timetable[day]) >= 5:  # Kuniga max 5 dars
                    continue

                if sum(1 for les in timetable[day] if les.startswith(subject)) >= 1:  # Kuniga 1 marta
                    continue

                # Kuniga 3 soat dars qo'yish
                for _ in range(3):
                    if scheduled >= weekly_hours:
                        break
                    if len(timetable[day]) >= 5:
                        break

                    timetable[day].append(f"{subject} ({teacher})")
                    teacher_workload[teacher]["total"] += 1
                    teacher_workload[teacher][day] += 1
                    scheduled += 1

        # Qolgan darslarni taqsimlash
        while scheduled < weekly_hours and attempts < 200:
            attempts += 1
            day = random.choice(days)

            # Cheklovlarni tekshirish
            subject_limit = sum(1 for les in timetable[day] if les.startswith(subject)) >= 1
            daily_limit = len(timetable[day]) >= 5
            consecutive = timetable[day] and subject in timetable[day][-1]

            if subject_limit or daily_limit or consecutive:
                continue

            # Eng kam ishlayotgan ustozni tanlash
            teacher = min(available_teachers, key=lambda t: (
                teacher_workload[t]["total"],
                len([d for d in days if teacher_workload[t][d] > 0])
            ))

            # Ustozning kunlik ish yuki 5 soatdan oshmasligi kerak
            if teacher_workload[teacher][day] >= 5:
                continue

            # Ustoz haftada 3 kundan ortiq ishlamasligi kerak
            active_days = len([d for d in days if teacher_workload[teacher][d] > 0])
            if active_days >= 3 and teacher_workload[teacher][day] == 0:
                continue

            timetable[day].append(f"{subject} ({teacher})")
            teacher_workload[teacher]["total"] += 1
            teacher_workload[teacher][day] += 1
            scheduled += 1

    return timetable, teacher_workload


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

        # Ma'lumotlarni ajratib olish
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

        # Ustozlarning ish yukini hisoblash uchun lug'at
        teacher_workload = defaultdict(lambda: defaultdict(int))
        for subject in TEACHERS:
            if subject != "base":
                for teacher in TEACHERS[subject]:
                    teacher_workload[teacher] = {"total": 0, "Dushanba": 0, "Seshanba": 0,
                                                 "Chorshanba": 0, "Payshanba": 0, "Juma": 0}

        # Haftalik dars soatlari
        weekly_msg = ["<b>Haftalik dars soatlari:</b>"]
        for level in sorted(class_counts.keys()):
            weekly_msg.append(f"\n<b>{level}-sinf:</b>")
            for subject, hours in BASE_SUBJECTS[level].items():
                weekly_msg.append(f"{subject}: {hours} soat")
            for subject, hours in EXTRA_SUBJECTS.get(level, {}).items():
                weekly_msg.append(f"{subject}: {hours} soat")
        await send_long_message(update, "\n".join(weekly_msg))

        # Har bir sinf uchun jadvallar
        for class_level, class_count in sorted(class_counts.items()):
            class_msg = [f"<b>➡️ {class_level}-sinf ({class_count} ta sinf)</b>"]

            for class_num in range(1, class_count + 1):
                timetable, teacher_workload = generate_class_timetable(class_level, class_num, teacher_workload)
                class_msg.append(f"\n<b>Sinf {class_num}:</b>")

                for day in ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma"]:
                    if not timetable[day]:
                        continue

                    class_msg.append(f"\n<b>{day}:</b>")
                    for i, lesson in enumerate(timetable[day], 1):
                        class_msg.append(f"{i}. {lesson}")

                class_msg.append("\n" + "▬" * 20)

            await send_long_message(update, "\n".join(class_msg))

        # Ustozlarning ish yuki haqida hisobot
        workload_msg = ["<b>Ustozlarning ish yuki:</b>"]
        for subject in TEACHERS:
            if subject != "base":
                workload_msg.append(f"\n<b>{subject}:</b>")
                for teacher in TEACHERS[subject]:
                    workload_msg.append(
                        f"{teacher}: {teacher_workload[teacher]['total']} soat "
                        f"(D:{teacher_workload[teacher]['Dushanba']} "
                        f"S:{teacher_workload[teacher]['Seshanba']} "
                        f"Ch:{teacher_workload[teacher]['Chorshanba']} "
                        f"P:{teacher_workload[teacher]['Payshanba']} "
                        f"J:{teacher_workload[teacher]['Juma']})"
                    )
        await send_long_message(update, "\n".join(workload_msg))

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