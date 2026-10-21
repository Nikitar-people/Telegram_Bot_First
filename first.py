import asyncio
import logging
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import create_engine, Text, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime
from sqlalchemy import select
import os
from dotenv import load_dotenv
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery






load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN") 



# Логирование
logging.basicConfig(level=logging.INFO)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()




class Base(DeclarativeBase):
    pass

class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    


engine = create_engine("sqlite:///users.db", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)




@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я простой бот. Вот что я умею:\n"
        "/start — это сообщение\n"
        "/help — помощь\n"
        "/echo <текст> — повторить текст\n\n"
        "/add <код> - добавить код\n\n"
        "/pay - имитация оплаты которая просто выводит код из бд\n\n"
        "Или просто напиши мне что-нибудь 🙂"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Команды:\n"
        "/start — приветствие\n"
        "/help — помощь\n"
        "/echo <текст> — повторить текст\n\n"
        "Также я умею считать символы в твоём сообщении."
    )


@dp.message(Command("echo"))
async def cmd_echo(message: Message):
    # Берём текст после команды
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Напиши так: /echo Привет, мир!")
        return
    await message.answer(args[1])





@dp.message(Command("add"))
async def cmd_add(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("Напиши так: /add МОЙ_КОД")
        return

    code = args[1].strip()
    with SessionLocal() as session:
        p = Person(code=code)
        session.add(p)
        session.commit()
        new_id = p.id

    await message.answer(f"Добавлено: id={new_id}, code={code}")






# @dp.message(Command("pay"))
# async def cmd_pay(message: Message):
#     with SessionLocal() as session:
#         # Берём первую запись (по возрастанию id)
#         person = session.scalars(
#             select(Person).order_by(Person.id.asc()).limit(1).with_for_update()
#         ).first()

#         if person is None:
#             await message.answer("База пуста. Добавь через /add <код>.")
#             return
#         code = person.code
#         person_id = person.id
#         session.delete(person)
#         session.commit()
#     await message.answer(f"Выдан код: {code} (id={person_id})")



















def get_and_remove_code():
    with SessionLocal() as session:
        person = session.scalars(
            select(Person).order_by(Person.id.asc()).limit(1).with_for_update()
        ).first()
        if person is None:
            return None, None
        code = person.code
        person_id = person.id
        session.delete(person)
        session.commit()
        return code, person_id

# Новая команда /pay для инициации оплаты
@dp.message(Command("pay"))
async def cmd_pay(message: Message):
    with SessionLocal() as session:
        exists = session.scalars(select(Person).limit(1)).first()
        if not exists:
            await message.answer("База пуста. Добавь код через /add <код> перед оплатой.")
            return

    
    await message.answer_invoice(
        title="Покупка кода",
        description="Оплата за получение уникального кода",
        payload="code_purchase_payload", 
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Код", amount=10000)], 
        start_parameter="buy-code"
    )


@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    
    await pre_checkout_query.answer(ok=True)


@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
   
    code, person_id = get_and_remove_code()
    
    if code:
        await message.answer(
            f"✅ Оплата прошла успешно!\n\n"
            f"Ваш код: `{code}`\n"
            f"(ID записи: {person_id})",
            parse_mode="Markdown"
        )
        
        payment_id = message.successful_payment.telegram_payment_charge_id
        logging.info(f"Успешный платёж {payment_id}. Выдан код {code}")
    else:
        
        await message.answer(
            "❌ Оплата прошла, но коды закончились. Пожалуйста, свяжитесь с администратором для возврата средств."
        )

























@dp.message(F.text)
async def echo_all(message: Message):
    # На любое текстовое сообщение отвечаем тем же
    await message.answer(
        f"Ты написал: «{message.text}»\n"
        f"Символов: {len(message.text)}"
    )





async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
        