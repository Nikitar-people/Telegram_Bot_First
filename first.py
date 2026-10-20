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







load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")




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
        "/add <код> - добавить код"
        "/pay - имитация оплаты которая просто выводит код из бд"
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






@dp.message(Command("pay"))
async def cmd_pay(message: Message):
    with SessionLocal() as session:
        # Берём первую запись (по возрастанию id)
        person = session.scalars(
            select(Person).order_by(Person.id.asc()).limit(1).with_for_update()
        ).first()

        if person is None:
            await message.answer("База пуста. Добавь через /add <код>.")
            return
        code = person.code
        person_id = person.id
        session.delete(person)
        session.commit()
    await message.answer(f"Выдан код: {code} (id={person_id})")







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
        